import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Email, Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


def view_emails():
    emails = session.query(Email).all()
    print(f"Всего писем в базе: {len(emails)}\n")

    for email in emails:
        company = session.query(Company).filter_by(hh_id=email.company_id).first()
        company_name = company.name if company else "Неизвестная компания"

        print(f"=== ПИСЬМО ДЛЯ: {company_name} (ID: {email.company_id}) ===")
        print(f"Статус: {email.status}")
        print("-" * 30)
        print(email.content)
        print("=" * 50 + "\n")

if __name__ == "__main__":
    view_emails()