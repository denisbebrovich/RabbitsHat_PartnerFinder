import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Добавляем путь к корню проекта для импорта моделей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Email, Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"
OUTPUT_FILE = "ml_service/dataset_partners.jsonl"

# Шаблоны инструкций для разных языков
# Для английского мы явно указываем, что описание может быть на русском, но ответ нужен на английском.
INSTRUCTION_TEMPLATES = {
    "ru": 'Напиши деловое письмо с предложением стажировки в компанию "{name}". Стек: {stack}. Описание компании: {desc}',
    "en": 'Write a formal partnership proposal email in English to "{name}". Base your proposal on their tech stack ({stack}) and company description: {desc}'
}


def export_for_finetuning():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Берем только утвержденные письма
    approved_emails = session.query(Email).filter(Email.is_approved == True).all()

    if not approved_emails:
        print("Нет утвержденных писем для экспорта!")
        return

    print(f"Экспорт {len(approved_emails)} примеров для обучения...")

    count_ru = 0
    count_en = 0

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for email in approved_emails:
            company = session.query(Company).filter_by(hh_id=email.company_id).first()
            if not company: continue

            # --- 1. ОПРЕДЕЛЕНИЕ ЯЗЫКА ---
            # Проверяем параметры генерации.
            # Если params нет (старые 53 письма) или там нет ключа "lang" -> считаем, что это русский.
            params = email.generation_params
            if params and params.get("lang") == "en":
                lang = "en"
                count_en += 1
            else:
                lang = "ru"
                count_ru += 1

            # --- 2. ПОДГОТОВКА ДАННЫХ КОМПАНИИ ---
            stack_list = company.tech_stack if company.tech_stack else []
            stack_str = ", ".join(stack_list[:8]) if stack_list else "IT"  # Берем топ-8 технологий

            desc_raw = company.description if company.description else ""
            # Очищаем описание от переносов строк, чтобы не ломать JSON
            desc_short = desc_raw[:300].replace("\n", " ").replace('"', "'") + "..."

            # --- 3. ВЫБОР ИНСТРУКЦИИ ---
            # Выбираем шаблон по ключу языка
            template = INSTRUCTION_TEMPLATES.get(lang, INSTRUCTION_TEMPLATES["ru"])

            instruction = template.format(
                name=company.name,
                stack=stack_str,
                desc=desc_short
            )

            # --- 4. ФОРМИРОВАНИЕ ОБЪЕКТА ---
            # Берем финальный (отредактированный) текст
            ideal_response = email.final_content if email.final_content else email.content

            data_point = {
                "instruction": instruction,
                "input": "",
                "output": ideal_response
            }

            f.write(json.dumps(data_point, ensure_ascii=False) + "\n")

    print(f"Готово! Датасет сохранен в {OUTPUT_FILE}")
    print(f"Статистика: RU={count_ru}, EN={count_en}")


if __name__ == "__main__":
    export_for_finetuning()