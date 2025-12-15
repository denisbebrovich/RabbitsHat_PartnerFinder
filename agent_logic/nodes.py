import sys
import os
import tempfile
import subprocess
import platform

# Настройка путей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml_service.scoring import calculate_score
from ml_service.email_generator import clean_stack_for_prompt, PROMPT_TEMPLATES, client, clean_company_name, \
    generate_personalized_sentence
from back.DB.models import Email
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# --- УТИЛИТА: РЕДАКТОР ---
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


# --- NODE 1: SCORING ---
def score_node(state):
    print(f"\n🔹 [1] АНАЛИЗ: {state['company_name']}")

    # Создаем объект-заглушку, так как scoring ожидает объект с атрибутами
    class MockComp:
        def __init__(self, data):
            self.tech_stack = data.get('tech_stack', [])
            self.is_it_company = data.get('is_it_company', False)
            self.description = data.get('description', "")

    score = calculate_score(MockComp(state['company_data']))
    print(f"   Рейтинг: {score}/100")

    return {
        "score": score,
        "is_relevant": score >= 30,  # Порог прохождения
        "logs": [f"Scored: {score}"]
    }


# --- NODE 2: DRAFTING (ГЕНЕРАЦИЯ) ---
def draft_node(state):
    print(f"🔹 [2] ГЕНЕРАЦИЯ ПИСЬМА...")

    if not state['is_relevant']:
        print("   ⛔ Пропуск (низкий рейтинг)")
        return {"status": "skipped", "logs": ["Skipped: Low score"]}

    # Используем логику из email_generator (Hybrid Template)
    data = state['company_data']
    target_lang = 'ru'  # Можно вынести в конфиг

    # 1. Чистим данные
    clean_name = clean_company_name(state['company_name'])
    stack_clean = clean_stack_for_prompt(data.get('tech_stack', []))
    if not stack_clean: stack_clean = ["IT"]
    stack_str = ", ".join(stack_clean)
    top_tech = stack_clean[0]

    # 2. Генерируем "умную" вставку
    personal_sent = generate_personalized_sentence(state['company_name'], data.get('description', ""), target_lang)

    # 3. Собираем шаблон (копируем логику get_russian_email из email_generator)
    # Чтобы не дублировать код, в идеале надо импортировать функцию get_russian_email,
    # но она там локальная. Для надежности соберем тут простой вариант.

    intro_extra = f"\n\n{personal_sent}" if personal_sent else ""
    greeting = f"Здравствуйте, команда {clean_name}!"

    email_text = f"""Тема: Студенческий проект на {top_tech} (предложение о сотрудничестве)

{greeting}

Пишет вам команда Центра проектного обучения «ПроКомпетенции» (УрФУ). Мы занимаемся организацией производственной практики для студентов IT-специальностей.{intro_extra}

Мы заметили, что вы используете отличный стек: {stack_str}.

Хотим предложить вам сотрудничество: наша команда студентов готова бесплатно разработать для вас MVP или закрыть задачи из бэклога в рамках практики (3 месяца).

Для вас это возможность присмотреться к талантливым студентам без затрат бюджета.

Готовы обсудить формат в Zoom на этой неделе?

С уважением,
Команда Центра «ПроКомпетенции»"""

    return {
        "draft_email": email_text,
        "status": "drafted",
        "logs": ["Draft created"]
    }


# --- NODE 3: HUMAN REVIEW ---
def approval_node(state):
    print(f"🔹 [3] ПРОВЕРКА ЧЕЛОВЕКОМ")

    if state.get('status') == 'skipped':
        return {}

    print("   Открываю редактор для проверки...")
    final_text = open_editor(state['draft_email'])

    print("\n   --- ИТОГОВОЕ ПИСЬМО ---")
    print(final_text)
    print("   -----------------------")

    choice = input("   Сохранить и отправить в БД? (y/n): ").lower()

    if choice == 'y':
        # Сохраняем в базу
        session = Session()
        new_email = Email(
            company_id=state['company_id'],
            content=state['draft_email'],  # Оригинал
            final_content=final_text,  # Итог
            is_approved=True,
            status='ready_to_send'
        )
        session.add(new_email)
        session.commit()
        session.close()
        print("   ✅ Письмо сохранено!")
        return {"status": "approved", "final_email": final_text}
    else:
        print("   ❌ Отменено.")
        return {"status": "rejected"}