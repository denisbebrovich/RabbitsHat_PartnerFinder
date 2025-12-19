import os
from openai import OpenAI

LM_STUDIO_URL = "http://localhost:1234/v1"


class EmailGenerator:
    def __init__(self, model_url=LM_STUDIO_URL):
        self.client = OpenAI(base_url=model_url, api_key="lm-studio")
        print(f"📧 EmailGenerator подключен к {model_url}")

    def generate_email(self, company_name: str, stack_str: str, desc_clean: str, lang: str = 'ru') -> dict:
        if lang == 'ru':
            instruction = f'Напиши деловое письмо с предложением стажировки в компанию "{company_name}". Стек: {stack_str}. Описание компании: {desc_clean}'
            stop_words = ["<|eot_id|>", "### Instruction:", "### Input:", "С уважением,"]
            signature = "С уважением,\nКоманда Центра «ПроКомпетенции»"
        else:
            instruction = f'Write a formal partnership proposal email in English to "{company_name}". Base your proposal on their tech stack ({stack_str}) and company description: {desc_clean}'
            stop_words = ["<|eot_id|>", "### Instruction:", "### Input:", "Kind regards,", "Sincerely,"]
            signature = "Kind regards,\nProCompetencies Center Team"

        alpaca_prompt = f"""Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

        ### Instruction:
        {instruction}

        ### Input:


        ### Response:
        """

        print("Текущий промт в LM:\n" + alpaca_prompt)

        try:
            response = self.client.completions.create(
                model="local-model",
                prompt=alpaca_prompt,
                temperature=0.1,
                top_p=0.9,
                max_tokens=600,
                stop=stop_words
            )

            raw_text = response.choices[0].text.strip()
            final_draft = f"{raw_text}\n\n{signature}"

            return {"success": True, "text": final_draft}

        except Exception as e:
            print(f"❌ Ошибка генерации в сервисе: {e}")
            return {"success": False, "error": str(e)}