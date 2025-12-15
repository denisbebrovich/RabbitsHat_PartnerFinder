import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ВРЕМЕННЫЙ СКРИПТ, ПОТОМ ОН НЕ БУДЕТ ИСПОЛЬЗОВАТЬСЯ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Email, Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"
OUTPUT_FILE = "ml_service/dataset_partners.jsonl"


def export_for_finetuning():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    approved_emails = session.query(Email).filter(Email.is_approved == True).all()
    print(f"Экспорт {len(approved_emails)} примеров для обучения...")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for email in approved_emails:
            company = session.query(Company).filter_by(hh_id=email.company_id).first()
            if not company: continue

            stack_list = company.tech_stack if company.tech_stack else []
            stack_str = ", ".join(stack_list[:6]) if stack_list else "IT"

            desc_raw = company.description if company.description else ""
            desc_short = desc_raw[:200].replace("\n", " ") + "..."

            instruction = f"""Напиши холодное письмо в компанию "{company.name}".
            Стек: {stack_str}. Описание: {desc_short}
            Цель: Предложить стажировку студентов."""

            ideal_response = email.final_content if email.final_content else email.content

            data_point = {
                "instruction": instruction,
                "input": "",
                "output": ideal_response
            }

            f.write(json.dumps(data_point, ensure_ascii=False) + "\n")

    print(f"Готово! Датасет сохранен в {OUTPUT_FILE}")
    print(f"Всего сохранено писем: {len(approved_emails)}")


if __name__ == "__main__":
    export_for_finetuning()