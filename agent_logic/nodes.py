import sys
import os
import tempfile
import subprocess
import platform
import re

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ml_service.scoring import calculate_score
from ml_service.skill_extractor import SkillExtractor
from ml_service.email_generator import EmailGenerator
from ml_service.api_client import BackendClient

# ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ
skill_service = SkillExtractor()
email_service = EmailGenerator()

api = BackendClient()

# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
def is_russian(text):
    if not text: return False
    return bool(re.search('[а-яА-Я]', text))


def clean_stack_list(stack_list):
    if not stack_list: return []

    STOP_WORDS = {
        "английский", "язык", "решение", "проблем", "коммуникабельность",
        "ответственность", "пунктуальность", "работа", "команде", "знание",
        "опыт", "разработка", "анализ", "желание", "учиться"
    }

    clean = []
    seen = set()

    for tech in stack_list:
        t_lower = tech.lower().strip()
        if len(tech) > 25 or len(tech) < 2: continue
        if any(stop in t_lower for stop in STOP_WORDS): continue

        if t_lower in ["sql", "php", "html", "css", "mvp", "api", "seo"]:
            tech_clean = t_lower.upper()
        else:
            tech_clean = tech.strip().capitalize()

        if tech_clean.lower() not in seen:
            clean.append(tech_clean)
            seen.add(tech_clean.lower())

    return clean[:8]


def open_editor(initial_text):
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt", encoding='utf-8') as tf:
        tf.write(initial_text)
        tf_path = tf.name

    try:
        if platform.system() == 'Windows':
            subprocess.call(['notepad.exe', tf_path])
        else:
            editor = os.environ.get('EDITOR', 'nano')
            subprocess.call([editor, tf_path])
    except Exception as e:
        print(f"⚠️ Не удалось открыть редактор: {e}")

    with open(tf_path, 'r', encoding='utf-8') as f:
        edited_text = f.read()

    os.remove(tf_path)
    return edited_text

# NODE 0: ENRICHMENT (Обогащение данными)
def enrichment_node(state):
    print(f"\n🔹 [0] ОБОГАЩЕНИЕ ДАННЫХ...")

    current_stack = state['company_data'].get('tech_stack', [])

    if current_stack and len(current_stack) > 0:
        print(f"   Стек уже заполнен: {current_stack[:3]}...")
        return {}

    print("   ⚠️ Стек пуст! Запускаю SkillExtractor по вакансиям...")

    vacancies_text = state['company_data'].get('vacancies_text', [])
    if not vacancies_text:
        print("   ❌ Нет текстов вакансий для анализа.")
        return {}

    full_text = " ".join(vacancies_text)

    extracted_stack = skill_service.extract_skills(full_text)
    print(f"   ✅ Извлечено навыков: {len(extracted_stack)} ({extracted_stack[:5]}...)")

    print("   💾 Отправляю обновленный стек на бэкенд...")
    api.update_tech_stack(state['company_id'], extracted_stack)

    new_data = state['company_data'].copy()
    new_data['tech_stack'] = extracted_stack

    return {
        "company_data": new_data,
        "logs": ["Skills extracted via SpaCy and saved via API"]
    }


# NODE 1: SCORING (Оценка релевантности)
def score_node(state):
    print(f"🔹 [1] АНАЛИЗ: {state['company_name']}")

    score = calculate_score(state['company_data'])
    print(f"   Рейтинг: {score}/100")

    is_relevant = score >= 60

    return {
        "score": score,
        "is_relevant": is_relevant,
        "logs": [f"Scored: {score}"]
    }


# NODE 2: DRAFTING (Генерация письма)
def draft_node(state):
    print(f"🔹 [2] ГЕНЕРАЦИЯ ПИСЬМА (через Llama)...")

    if not state.get('is_relevant'):
        print("   ⛔ Пропуск (низкий рейтинг)")
        return {"status": "skipped", "logs": ["Skipped: Low score"]}

    comp_name = state['company_name']
    data = state['company_data']

    raw_desc = data.get('description')
    raw_vacancies = data.get('vacancies_text', [])

    text_for_lang_check = (raw_desc or "") + " ".join(raw_vacancies) + comp_name
    is_ru = is_russian(text_for_lang_check)
    lang = 'ru' if is_ru else 'en'
    print(f"   Язык определен как: {lang.upper()}")

    if raw_desc and len(raw_desc) > 10:
        desc_clean = raw_desc[:400].replace("\n", " ").replace('"', "'").strip()
    elif raw_vacancies:
        print("   ⚠️ Описания нет, использую текст вакансий.")
        desc_clean = " ".join(raw_vacancies)[:400].replace("\n", " ").replace('"', "'").strip()
    else:
        desc_clean = "IT-компания" if lang == 'en' else "IT-компания с активными вакансиями"

    stack_clean = clean_stack_list(data.get('tech_stack', []))
    stack_str = ", ".join(stack_clean) if stack_clean else ("IT Tech" if lang == 'en' else "IT-технологии")

    result = email_service.generate_email(
        company_name=comp_name,
        stack_str=stack_str,
        desc_clean=desc_clean,
        lang=lang
    )

    if result["success"]:
        return {
            "draft_email": result["text"],
            "status": "drafted",
            "logs": [f"Draft created ({lang})"]
        }
    else:
        return {
            "error": result["error"],
            "logs": [f"Generation failed: {result['error']}"]
        }


# NODE 3: HUMAN REVIEW (Ручная проверка)
def approval_node(state):
    print(f"🔹 [3] ПРОВЕРКА ЧЕЛОВЕКОМ")

    if state.get('status') == 'skipped':
        return {}
    if state.get('error'):
        print(f"   ❌ Ошибка на предыдущем этапе: {state['error']}")
        return {}

    print("   Открываю редактор для проверки письма...")
    final_text = open_editor(state['draft_email'])

    print("\n   --- ИТОГОВОЕ ПИСЬМО ---")
    print(final_text[:200] + "...\n(показано начало)")
    print("   -----------------------")

    choice = input("   Сохранить письмо и пометить 'Ready to Send'? (y/n): ").lower()

    if choice == 'y':
        api.save_email_draft(
            company_id=state['company_id'],
            email_text=final_text,
            status="ready_to_send"
        )
        print("   ✅ Письмо сохранено через API!")
        return {"status": "approved", "final_email": final_text}
    else:
        print("   ❌ Письмо отклонено.")
        return {"status": "rejected"}


# NODE X: FINALIZE SKIPPED (Фиксация пропуска)
def finalize_skipped_node(state):
    print(f"🔹 [X] ФИКСАЦИЯ ПРОПУСКА")

    api.log_skip(
        company_id=state['company_id'],
        reason="Low score or irrelevant"
    )
    print("   💾 Пропуск зафиксирован в БД.")

    return {"status": "skipped_saved"}