import sys
import os
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Company, Email

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"
LM_STUDIO_URL = "http://localhost:1234/v1"

# Настройка генерации письма
TARGET_LANG = 'en'  # Язык письма: 'ru' или 'en'
TARGET_STYLE = 'formal'  # Стиль письма: 'formal' или 'informal'
MIN_SCORE = 40  # Минимальный рейтинг компании

client = OpenAI(base_url=LM_STUDIO_URL, api_key="lm-studio")

STOP_WORDS = {
    "английский", "язык", "решение", "проблем", "коммуникабельность",
    "ответственность", "пунктуальность", "работа", "команде", "управление",
    "администрирование", "ос", "знание", "опыт", "разработка", "внедрение",
    "анализ", "автоматизация", "систем", "программы", "желание", "учиться",
    "сетевые", "технологии"
}


def clean_stack_for_prompt(stack_list):
    if not stack_list: return []
    clean = []
    seen = set()
    for tech in stack_list:
        t_lower = tech.lower().strip()
        if len(tech) > 25 or len(tech) < 2: continue
        if any(stop in t_lower for stop in STOP_WORDS): continue

        # Нормализация
        if t_lower in ["sql", "php", "html", "css", "mvp", "api", "seo"]:
            tech_clean = t_lower.upper()
        else:
            tech_clean = tech.strip().capitalize()

        if tech_clean.lower() not in seen:
            clean.append(tech_clean)
            seen.add(tech_clean.lower())
    return clean[:8]

# 4 отдельных сценария, каждый содержит System Prompt и User Prompt Template (ВРЕМЕННО, ПОСЛЕ БУДЕТ ОБУЧЕННАЯ МОДЕЛЬ, УЖЕ ПОЧТИ ГОТОВАЯ)
PROMPT_TEMPLATES = {
    ("ru", "formal"): {
        "system": (
            "Ты — официальный представитель Центра проектного обучения УрФУ. "
            "Твоя задача — писать деловые письма потенциальным партнерам. "
            "Стиль: Строгий, уважительный, без сленга. Используй обращение на 'Вы'. "
            "Язык: Строго Русский."
        ),
        "user_template": """
        Напиши деловое письмо в компанию "{company_name}".

        ВВОДНЫЕ ДАННЫЕ:
        - Стек компании: {stack_str}
        - О чем они (контекст): {desc_short}

        СТРУКТУРА ПИСЬМА:
        1. Тема: "Предложение о сотрудничестве: студенческий проект ({top_tech})"
        2. Приветствие: "Здравствуйте, коллеги из {company_name}!"
        3. Вступление: Начни строго с фразы: "Мы внимательно изучили профиль вашей компании и были впечатлены вашим технологическим стеком ({stack_str})."
        4. Кто мы: "Пишет вам команда Центра проектного обучения «ПроКомпетенции» (УрФУ). Мы занимаемся организацией практики для студентов IT-специальностей."
        5. Суть предложения: "Мы хотим предложить вам сотрудничество. Наша команда студентов готова бесплатно разработать для вас MVP или закрыть задачи из бэклога в рамках производственной практики (3 месяца)."
        6. Выгода: Это бесплатно для бизнеса и позволяет присмотреться к будущим сотрудникам.
        7. Призыв к действию: "Готовы обсудить формат взаимодействия в Zoom на этой неделе?"
        8. Подпись: "С уважением, Команда центра ПроКомпетенции."

        ВАЖНО: Не выдумывай опыт работы центра. Мы образовательная организация.
        """
    },

    ("ru", "informal"): {
        "system": (
            "Ты — менеджер студенческого IT-акселератора. Ты пишешь стартапам и IT-компаниям. "
            "Стиль: Живой, энергичный, дружелюбный, но профессиональный. Без канцеляризмов. "
            "Язык: Строго Русский."
        ),
        "user_template": """
        Напиши письмо ребятам из компании "{company_name}".

        ВВОДНЫЕ ДАННЫЕ:
        - Их стек: {stack_str}
        - О чем они: {desc_short}

        СТРУКТУРА ПИСЬМА:
        1. Тема: "Студенты-разработчики ({top_tech}) для {company_name}"
        2. Приветствие: "Привет, команда {company_name}!"
        3. Хук: "Заценили ваш стек ({stack_str}) — крутой выбор!"
        4. Кто мы: "Мы — студенческий центр «ПроКомпетенции» при УрФУ. Драйвим практику для начинающих разработчиков."
        5. Оффер: "У нас есть толковые студенты, которым нужна боевая практика. Готовы бесплатно запилить для вас MVP или разгрести задачи в бэклоге за 3 месяца."
        6. Выгода: "Вы получаете рабочие руки и свежий взгляд, студенты — опыт. Win-win."
        7. CTA: "Давайте созвонимся в Zoom на 10 минут, расскажем детали?"
        8. Подпись: "Команда ПроКомпетенции."
        """
    },

    ("en", "formal"): {
        "system": (
            "You are a Partnership Manager at the Ural Federal University (UrFU) Project Center. "
            "Your goal is to propose academic partnerships to IT companies. "
            "Style: Professional, polite, concise. Business English. "
            "Language: Strictly English."
        ),
        "user_template": """
        Write a formal email to "{company_name}".

        DETAILS:
        - Tech Stack: {stack_str}
        - Company Context: {desc_short}

        EMAIL STRUCTURE:
        1. Subject: "Collaboration Proposal: Student Internship Project ({top_tech})"
        2. Salutation: "Dear {company_name} Team,"
        3. Opening: Mention that we analyzed their profile and are impressed by their tech stack ({stack_str}).
        4. Who we are: "I represent the 'ProCompetencies' Project Learning Center at UrFU. We bridge the gap between academia and industry."
        5. The Offer: "We propose a partnership where our students develop an MVP or complete backlog tasks for your company over a 3-month internship period. This is free of charge."
        6. Benefit: Access to motivated talent and R&D support.
        7. Call to Action: "Are you available for a brief Zoom call this week to discuss potential synergy?"
        8. Sign-off: "Sincerely, ProCompetencies Center Team."

        IMPORTANT: Do not hallucinate previous commercial experience. We are an educational entity.
        """
    },

    ("en", "informal"): {
        "system": (
            "You are an Outreach Manager for a Student Tech Accelerator. "
            "You are writing to tech startups. "
            "Style: Casual, friendly, direct. Silicon Valley vibe. "
            "Language: Strictly English."
        ),
        "user_template": """
        Write a cold email to "{company_name}".

        DETAILS:
        - Stack: {stack_str}
        - Context: {desc_short}

        STRUCTURE:
        1. Subject: "Dev students ({top_tech}) for {company_name}?"
        2. Hi: "Hi {company_name} team!"
        3. Hook: "Love your tech stack ({stack_str}) — great choices."
        4. Intro: "We are 'ProCompetencies', a student accelerator at UrFU."
        5. Pitch: "We have ambitious students looking for real-world challenges. They can build an MVP or clear your backlog for free during a 3-month internship."
        6. Why: "You get extra coding power; they get experience."
        7. CTA: "Open to a quick chat this week?"
        8. Sign: "Best, ProCompetencies Team."
        """
    }
}


def generate_emails():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        current_template = PROMPT_TEMPLATES[(TARGET_LANG, TARGET_STYLE)]
        print(f"--- ЗАПУСК ГЕНЕРАЦИИ ---")
        print(f"Язык: {TARGET_LANG.upper()}")
        print(f"Стиль: {TARGET_STYLE.upper()}")
        print(f"------------------------")
    except KeyError:
        print("Ошибка: Неверная комбинация языка и стиля в настройках")
        return

    # Фильтруем компании
    targets = session.query(Company).filter(Company.score >= MIN_SCORE).all()
    print(f"Найдено компаний с рейтингом > {MIN_SCORE}: {len(targets)}")

    count = 0

    for company in targets:
        # --- НОВАЯ ЛОГИКА ПРОВЕРКИ ---
        # Мы ищем, есть ли уже письмо с ТЕКУЩИМ языком (TARGET_LANG)
        # 1. Получаем все письма компании
        existing_emails = session.query(Email).filter_by(company_id=company.hh_id).all()

        # 2. Проверяем, есть ли среди них письмо на нужном языке
        already_has_target_lang = False
        for email in existing_emails:
            # Проверяем параметры генерации (если они есть)
            if email.generation_params and email.generation_params.get("lang") == TARGET_LANG:
                already_has_target_lang = True
                break
            # Если параметров нет (старые письма), считаем их русскими ('ru')
            elif not email.generation_params and TARGET_LANG == 'ru':
                already_has_target_lang = True
                break

        if already_has_target_lang:
            # Если английское письмо уже есть, и мы генерируем английское — пропускаем
            continue
        # -----------------------------

        print(f"Генерация ({TARGET_LANG.upper()}) для: {company.name}...")

        stack_clean = clean_stack_for_prompt(company.tech_stack)
        stack_str = ", ".join(stack_clean) if stack_clean else "IT technologies"
        top_tech = stack_clean[0] if stack_clean else "Tech"

        # Если описание русское, а генерируем EN — модель сама переведет суть,
        # но можно добавить подсказку "IT company" если описания нет.
        desc_short = company.description[:200].replace("\n", " ") + "..." if company.description else "IT company"

        user_prompt_filled = current_template["user_template"].format(
            company_name=company.name,
            stack_str=stack_str,
            desc_short=desc_short,
            top_tech=top_tech
        )

        try:
            response = client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": current_template["system"]},
                    {"role": "user", "content": user_prompt_filled}
                ],
                temperature=0.2,
            )

            email_text = response.choices[0].message.content

            # СОХРАНЯЕМ НОВОЕ ПИСЬМО (ВТОРЫМ РЯДОМ)
            new_email = Email(
                company_id=company.hh_id,
                content=email_text,
                status=f'generated_{TARGET_LANG}_{TARGET_STYLE}',
                is_approved=False,  # Важно: оно требует проверки
                # Обязательно пишем параметры, чтобы потом различить языки
                generation_params={"lang": TARGET_LANG, "style": TARGET_STYLE}
            )
            session.add(new_email)
            session.commit()
            count += 1
            print(f"OK ({count})")

        except Exception as e:
            print(f"Ошибка API: {e}")


if __name__ == "__main__":
    generate_emails()