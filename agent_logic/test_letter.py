import smtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"  # Для Gmail: smtp.gmail.com | Mail.ru: smtp.mail.ru
SMTP_PORT = 465
SENDER_EMAIL = "procompetencepartnerhelper@gmail.com"
RECIPIENT_EMAIL = "Mamaev.Sergey@urfu.me"
# ВАЖНО: используйте пароль приложения, а не основной пароль
PASSWORD = "rkbv zmhv dumo pnpd"

msg = EmailMessage()
msg.set_content("Привет, как дела?")
msg['Subject'] = "Тестовое письмо"
msg['From'] = SENDER_EMAIL
msg['To'] = RECIPIENT_EMAIL

try:
    # Подключение и отправка
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
        server.login(SENDER_EMAIL, PASSWORD)
        server.send_message(msg)
    print("Письмо успешно отправлено!")
except Exception as e:
    print(f"Ошибка: {e}")