import sys
import os
import tempfile
import subprocess
import platform
import re
from openai import OpenAI

# Настройка путей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml_service.scoring import calculate_score
from ml_service.email_generator import clean_stack_for_prompt
from ml_service.skill_extractor import SkillExtractor
from back.DB.models import Email, Company
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# КОНФИГ
DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"
LM_STUDIO_URL = "http://localhost:1234/v1"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")
extractor = SkillExtractor()  # Инициализируем один раз


# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def is_russian(text):
    return bool(re.search('[а-яА-Я]', text))


def open_editor(initial_text):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt", encoding='utf-8') as tf:
        tf.write(initial_text)
        tf_path = tf.name
    try:
        if platform.system() == 'Windows':
            subprocess.call(['notepad.exe', tf_path])
        else:
            subprocess.call(['nano', tf_path])
    except:
        pass
    with open(tf_path, 'r', encoding='utf-8') as f:
        edited_text = f.read()
    os.remove(tf_path)
    return edited_text


# --- NODE 0: ENRICHMENT (Обогащение данными) ---
def enrichment_node(state):
    print(f"\n🔹 [0] ОБОГАЩЕНИЕ ДАННЫХ...")

    current_stack = state['company_data'].get('tech_stack', [])

    # Если стек уже есть и он не пустой — пропускаем
    if current_stack and len(current_stack) > 0:
        print(f"   Стек уже заполнен: {current_stack[:3]}...")
        return {}

    # Если стека нет — запускаем SkillExtractor
    print("   ⚠️ Стек пуст! Запускаю SkillExtractor по вакансиям...")

    vacancies_text = state['company_data'].get('vacancies_text', [])
    if not vacancies_text:
        print("   ❌ Нет текстов вакансий для анализа.")
        return {}

    # Объединяем все вакансии в один текст для анализа
    full_text = " ".join(vacancies_text)
    extracted_stack = extractor.extract_skills(full_text)

    print(f"   ✅ Извлечено навыков: {len(extracted_stack)} ({extracted_stack[:5]}...)")

    # СОХРАНЯЕМ В БД (чтобы в следующий раз не считать)
    session = Session()
    company = session.query(Company).filter_by(hh_id=state['company_id']).first()
    if company:
        company.tech_stack = extracted_stack
        session.commit()
        print("   💾 Стек сохранен в БД.")
    session.close()

    # Обновляем состояние агента
    new_data = state['company_data'].copy()
    new_data['tech_stack'] = extracted_stack

    return {
        "company_data": new_data,
        "logs": ["Skills extracted and saved"]
    }


# --- NODE 1: SCORING (Оценка) ---
def score_node(state):
    print(f"🔹 [1] АНАЛИЗ: {state['company_name']}")

    class MockComp:
        def __init__(self, data):
            self.tech_stack = data.get('tech_stack', [])
            self.is_it_company = data.get('is_it_company', False)
            self.description = data.get('description', "")

    score = calculate_score(MockComp(state['company_data']))
    print(f"   Рейтинг: {score}/100")

    return {
        "score": score,
        "is_relevant": score >= 60,  # Порог прохода
        "logs": [f"Scored: {score}"]
    }


# --- NODE 2: DRAFTING (Генерация Llama 3) ---
def draft_node(state):
    print(f"🔹 [2] ГЕНЕРАЦИЯ ПИСЬМА (Llama 3 Local)...")

    if not state['is_relevant']:
        print("   ⛔ Пропуск (низкий рейтинг)")
        return {"status": "skipped", "logs": ["Skipped: Low score"]}

    # 1. Достаем данные
    data = state['company_data']
    comp_name = state['company_name']

    # Сырые данные
    raw_desc = data.get('description')
    raw_vacancies = data.get('vacancies_text', [])  # Список текстов вакансий

    # 2. ОПРЕДЕЛЕНИЕ ЯЗЫКА (Каскадная проверка)
    # Собираем весь доступный текст в одну кучу, чтобы найти хоть одну русскую букву
    text_for_lang_check = (raw_desc or "") + " ".join(raw_vacancies) + comp_name

    # Если нашлась хоть одна русская буква — считаем, что это RU (для HH.ru это верно на 99%)
    is_ru = is_russian(text_for_lang_check)
    lang = 'ru' if is_ru else 'en'

    print(f"   Язык определен как: {lang.upper()} (на основе анализа текста)")

    # 3. ПОДГОТОВКА ОПИСАНИЯ ДЛЯ МОДЕЛИ
    # Если описания нет, модель начнет галлюцинировать.
    # Мы подсунем ей кусок текста из вакансий, чтобы она поняла, чем занимается компания.

    if raw_desc and len(raw_desc) > 10:
        # Если есть нормальное описание — берем его
        desc_clean = raw_desc[:400].replace("\n", " ").replace('"', "'").strip()
    elif raw_vacancies:
        # Если описания нет, но есть вакансии — берем начало вакансий как контекст
        print("   ⚠️ Описания нет, использую текст вакансий как контекст.")
        desc_clean = " ".join(raw_vacancies)[:400].replace("\n", " ").replace('"', "'").strip()
    else:
        # Если вообще ничего нет — ставим заглушку
        desc_clean = "IT-компания" if lang == 'en' else "IT-компания с активными вакансиями"

    # 4. Подготовка стека
    stack_clean = clean_stack_for_prompt(data.get('tech_stack', []))
    stack_str = ", ".join(stack_clean) if stack_clean else ("IT Tech" if lang == 'en' else "IT-технологии")

    # 5. Выбор шаблона (Строго как в dataset_partners.jsonl)
    if lang == 'ru':
        instruction = f'Напиши деловое письмо с предложением стажировки в компанию "{comp_name}". Стек: {stack_str}. Описание компании: {desc_clean}'
        stop_words = ["<|eot_id|>", "### Instruction:", "### Input:", "С уважением,"]
        signature = "С уважением,\nКоманда Центра «ПроКомпетенции»"
    else:
        instruction = f'Write a formal partnership proposal email in English to "{comp_name}". Base your proposal on their tech stack ({stack_str}) and company description: {desc_clean}'
        stop_words = ["<|eot_id|>", "### Instruction:", "### Input:", "Kind regards,", "Sincerely,"]
        signature = "Kind regards,\nProCompetencies Center Team"

    # 6. Сборка промпта
    alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{instruction}

### Input:


### Response:
"""

    try:
        response = client.completions.create(
            model="local-model",
            prompt=alpaca_prompt,
            temperature=0.05,
            top_p=0.9,
            max_tokens=600,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            stop=stop_words
        )

        raw_text = response.choices[0].text.strip()
        final_draft = f"{raw_text}\n\n{signature}"

        return {
            "draft_email": final_draft,
            "status": "drafted",
            "logs": [f"Draft created ({lang})"]
        }

    except Exception as e:
        print(f"   ❌ Ошибка генерации: {e}")
        return {"error": str(e)}


# --- NODE 3: HUMAN REVIEW ---
def approval_node(state):
    print(f"🔹 [3] ПРОВЕРКА ЧЕЛОВЕКОМ")

    if state.get('status') == 'skipped':
        return {}

    print("   Открываю редактор...")
    final_text = open_editor(state['draft_email'])

    print("\n   --- ИТОГОВОЕ ПИСЬМО ---")
    print(final_text)
    print("   -----------------------")

    choice = input("   Сохранить в БД? (y/n): ").lower()

    if choice == 'y':
        session = Session()
        existing = session.query(Email).filter_by(company_id=state['company_id']).first()

        if not existing:
            new_email = Email(
                company_id=state['company_id'],
                content=state['draft_email'],
                final_content=final_text,
                is_approved=True,
                status='ready_to_send'
            )
            session.add(new_email)
        else:
            existing.final_content = final_text
            existing.is_approved = True
            existing.status = 'ready_to_send'

        session.commit()
        session.close()
        print("   ✅ Сохранено!")
        return {"status": "approved", "final_email": final_text}
    else:
        print("   ❌ Отменено.")
        return {"status": "rejected"}

def finalize_skipped_node(state):
    print(f"🔹 [X] ФИКСАЦИЯ ПРОПУСКА (Низкий рейтинг)")

    # Сохраняем в БД запись, что мы посмотрели эту компанию, но пропустили
    # Это нужно, чтобы SQL-запрос больше не выдавал эту компанию

    session = Session()
    try:
        # Проверка на дубликаты
        existing = session.query(Email).filter_by(company_id=state['company_id']).first()
        if not existing:
            skipped_email = Email(
                company_id=state['company_id'],
                content="Skipped due to low score",
                final_content="Skipped due to low score",
                is_approved=False,
                status='skipped'  # Специальный статус
            )
            session.add(skipped_email)
            session.commit()
            print("   💾 Статус 'skipped' сохранен в БД.")
        else:
            print("   (Запись уже была)")
    except Exception as e:
        print(f"   Ошибка сохранения пропуска: {e}")
    finally:
        session.close()

    return {"status": "skipped_saved"}