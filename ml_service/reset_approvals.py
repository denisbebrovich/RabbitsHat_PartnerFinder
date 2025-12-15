import sys
import os
from sqlalchemy import create_engine, text

# ВРЕМЕННЫЙ СКРИПТ, ОН НЕ БУДЕТ ПОТОМ ИСПОЛЬЗОВАТЬСЯ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"


def reset_approvals():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Сброс статусов утверждения...")

        sql = text("""
                   UPDATE emails
                   SET is_approved    = false,
                       final_content  = NULL,
                       status         = 'generated_reset',
                       human_feedback = NULL
                   WHERE is_approved = true;
                   """)

        result = conn.execute(sql)
        conn.commit()
        print(f"Сброшено писем: {result.rowcount}")

if __name__ == "__main__":
    confirm = input("Это удалит ваши РУЧНЫЕ правки писем. Сбросить валидацию? (y/n): ")
    if confirm.lower() == 'y':
        reset_approvals()
    else:
        print("Отмена.")