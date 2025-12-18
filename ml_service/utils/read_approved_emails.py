import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ВРЕМЕННЫЙ СКРИПТ, ОН НЕ БУДЕТ ПОТОМ ИСПОЛЬЗОВАТЬСЯ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Email, Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"


def view_approved():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    approved_emails = session.query(Email).filter(Email.is_approved == True).all()

    print(f"\n=== ЗОЛОТОЙ ДАТАСЕТ (Утверждено: {len(approved_emails)}) ===\n")

    if not approved_emails:
        print("Пока нет утвержденных писем. Запустите human_review.py!")
        return

    for i, email in enumerate(approved_emails, 1):
        company = session.query(Company).filter_by(hh_id=email.company_id).first()
        comp_name = company.name if company else "Unknown"

        print(f"[{i}] КОМПАНИЯ: {comp_name}")
        print(f"    ID: {email.company_id}")
        text_to_show = email.final_content if email.final_content else email.content

        print(f"    ТЕКСТ ПИСЬМА:")
        print("-" * 40)
        print(text_to_show.strip())
        print("-" * 40)

        if email.human_feedback:
            print(f"    СТАТУС: Отредактировано человеком ({email.human_feedback})")
        else:
            print(f"    СТАТУС: Принято без правок")
        print("\n" + "=" * 40 + "\n")


if __name__ == "__main__":
    view_approved()