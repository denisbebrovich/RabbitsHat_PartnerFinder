import sys
import os
import subprocess
import tempfile
import platform
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Email, Company

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"


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
        print(f"Ошибка открытия редактора: {e}")
        return initial_text

    with open(tf_path, 'r', encoding='utf-8') as f:
        edited_text = f.read()

    os.remove(tf_path)
    return edited_text


def review_loop():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    pending_emails = session.query(Email).filter(
        Email.status.like('generated%'),
        Email.is_approved == False
    ).order_by(Email.id).all()

    if not pending_emails:
        print("Нет новых писем для проверки (все утверждены).")
        return

    print(f"Найдено {len(pending_emails)} писем на проверку.\n")

    for i, email in enumerate(pending_emails, 1):
        company = session.query(Company).filter_by(hh_id=email.company_id).first()

        while True:
            print("=" * 60)
            print(f"ПИСЬМО {i}/{len(pending_emails)} | КОМПАНИЯ: {company.name}")
            print(f"СТЕК: {company.tech_stack[:10]}...")
            print("-" * 20)

            current_content = email.final_content if email.final_content else email.content
            print(current_content)
            print("-" * 20)

            print("\nДЕЙСТВИЯ:")
            print("[y] Approve (Одобрить текущий текст)")
            print("[e] Edit (Редактировать в Блокноте)")
            print("[s] Skip (Пропустить пока)")
            print("[q] Quit (Выход)")

            choice = input("Выбор > ").lower().strip()

            if choice == 'y':
                email.is_approved = True
                email.final_content = current_content
                email.status = 'ready_to_send'
                session.commit()
                print("✅ Все письма утверждены.")
                break

            elif choice == 'e':
                print("Открываю редактор...")
                edited = open_editor(current_content)

                email.final_content = edited.strip()
                email.human_feedback = "Edited by human"
                print("--- Текст обновлен в памяти. Проверьте его выше ---")

            elif choice == 's':
                print("Пропуск.")
                break

            elif choice == 'q':
                print("Выход.")
                return
            else:
                print("Неизвестная команда.")


if __name__ == "__main__":
    review_loop()