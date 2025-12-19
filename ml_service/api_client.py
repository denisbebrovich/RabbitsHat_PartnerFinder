import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

class BackendClient:
    def __init__(self, base_url=BACKEND_URL):
        self.base_url = base_url

    def get_next_company(self):
        try:
            resp = requests.get(f"{self.base_url}/api/agent/next_task")
            if resp.status_code == 200:
                return resp.json() # Ожидаем JSON с данными компании
            return None
        except Exception as e:
            print(f"🔌 Ошибка подключения к API: {e}")
            return None

    def update_tech_stack(self, company_id, stack):
        try:
            payload = {"tech_stack": stack}
            requests.patch(f"{self.base_url}/api/companies/{company_id}", json=payload)
        except Exception as e:
            print(f"❌ Не удалось сохранить стек: {e}")

    def save_email_draft(self, company_id, email_text, status="drafted"):
        try:
            payload = {
                "company_id": company_id,
                "content": email_text,
                "status": status,
                "is_approved": status == "ready_to_send"
            }
            requests.post(f"{self.base_url}/api/emails", json=payload)
        except Exception as e:
            print(f"❌ Не удалось сохранить письмо: {e}")

    def log_skip(self, company_id, reason="low_score"):
        self.save_email_draft(company_id, f"Skipped: {reason}", status="skipped")

    def get_memories(self, company_id):
        try:
            resp = requests.get(f"{self.base_url}/api/memories/{company_id}")
            if resp.status_code == 200:
                return resp.json()
            return []
        except Exception as e:
            print(f"🧠 Ошибка чтения памяти: {e}")
            return []

    def save_memory(self, company_id, subject, predicate, obj, confidence=1.0):
        try:
            payload = {
                "subject": subject,
                "predicate": predicate,
                "obj": obj,
                "confidence": confidence
            }
            resp = requests.post(f"{self.base_url}/api/memories/{company_id}", json=payload)
            if resp.status_code == 200:
                print(f"🧠 Запомнил: {subject} --{predicate}--> {obj}")
        except Exception as e:
            print(f"❌ Не удалось сохранить воспоминание: {e}")