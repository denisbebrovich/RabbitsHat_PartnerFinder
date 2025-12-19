import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Email, Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"
OUTPUT_FILE = "ml_service/dataset_partners.jsonl"

INSTRUCTION_TEMPLATES = {
    "ru": 'Напиши деловое письмо с предложением стажировки в компанию "{name}". Стек: {stack}. Описание компании: {desc}',
    "en": 'Write a formal partnership proposal email in English to "{name}". Base your proposal on their tech stack ({stack}) and company description: {desc}'
}


def export_for_finetuning():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

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

            params = email.generation_params
            if params and params.get("lang") == "en":
                lang = "en"
                count_en += 1
            else:
                lang = "ru"
                count_ru += 1

            stack_list = company.tech_stack if company.tech_stack else []
            stack_str = ", ".join(stack_list[:8]) if stack_list else "IT"

            desc_raw = company.description if company.description else ""
            desc_short = desc_raw[:300].replace("\n", " ").replace('"', "'") + "..."

            template = INSTRUCTION_TEMPLATES.get(lang, INSTRUCTION_TEMPLATES["ru"])

            instruction = template.format(
                name=company.name,
                stack=stack_str,
                desc=desc_short
            )

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