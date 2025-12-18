import sys
import os
from langgraph.graph import StateGraph, END
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Company, Email, Vacancy
from state import AgentState
from nodes import enrichment_node, score_node, draft_node, approval_node, finalize_skipped_node

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"

# --- ПОСТРОЕНИЕ ГРАФА ---
workflow = StateGraph(AgentState)

# Добавляем узлы
workflow.add_node("enrichment", enrichment_node)
workflow.add_node("scoring", score_node)
workflow.add_node("drafting", draft_node)
workflow.add_node("approval", approval_node)
# !!! НОВЫЙ УЗЕЛ !!!
workflow.add_node("finalize_skipped", finalize_skipped_node)

# Связи
workflow.set_entry_point("enrichment")
workflow.add_edge("enrichment", "scoring")

# Логика ветвления
def check_score(state):
    # Если релевантно -> пишем письмо
    if state.get('is_relevant'):
        return "drafting"
    # Если НЕТ -> идем фиксировать пропуск (вместо END)
    return "finalize_skipped"

workflow.add_conditional_edges(
    "scoring",
    check_score,
    {
        "drafting": "drafting",
        "finalize_skipped": "finalize_skipped" # <-- Маршрут для низкого рейтинга
    }
)

workflow.add_edge("drafting", "approval")
workflow.add_edge("approval", END)
workflow.add_edge("finalize_skipped", END) # После фиксации пропуска - конец

app = workflow.compile()

# --- ЗАПУСК ---
def run_agent():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print(f"🔍 Ищу необработанную компанию...")

    # SQL запрос берет компании, у которых Email.id IS NULL
    # Теперь, когда мы сохраняем статус 'skipped', у них БУДЕТ Email.id,
    # и они больше не попадут в выборку.
    target = session.query(Company).outerjoin(Email).filter(
        Email.id == None
    ).first()

    if not target:
        print("🎉 Все компании обработаны!")
        return

    # Собираем тексты вакансий
    vacancies_text = [v.description for v in target.vacancies if v.description]

    inputs = {
        "company_id": target.hh_id,
        "company_name": target.name,
        "company_data": {
            "tech_stack": target.tech_stack,
            "is_it_company": target.is_it_company,
            "description": target.description,
            "vacancies_text": vacancies_text
        },
        "logs": []
    }

    print(f"🚀 ЗАПУСК АГЕНТА: {target.name}")
    app.invoke(inputs)
    session.close()

if __name__ == "__main__":
    while True:
        run_agent()
        # Добавил небольшую паузу или проверку, чтобы не спамить, если все обработано
        # Но логика input осталась как у тебя
        cont = input("\nОбработать следующую? [Enter - Да, n - Нет]: ")
        if cont.lower() == 'n':
            break