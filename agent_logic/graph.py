import sys
import os
from langgraph.graph import StateGraph, END
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from back.DB.models import Company, Email
from state import AgentState
from nodes import score_node, draft_node, approval_node

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"

workflow = StateGraph(AgentState)

workflow.add_node("scoring", score_node)
workflow.add_node("drafting", draft_node)
workflow.add_node("approval", approval_node)

workflow.set_entry_point("scoring")


def check_score(state):
    return "drafting" if state['is_relevant'] else END


workflow.add_conditional_edges("scoring", check_score, {"drafting": "drafting", END: END})
workflow.add_edge("drafting", "approval")
workflow.add_edge("approval", END)

app = workflow.compile()


def run_agent():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    companies = session.query(Company).all()
    target = None

    for comp in companies:
        if not session.query(Email).filter_by(company_id=comp.hh_id).first():
            target = comp
            break

    if not target:
        print("Все компании уже обработаны! (Запустите clear_emails.py если хотите начать заново)")
        return

    inputs = {
        "company_id": target.hh_id,
        "company_name": target.name,
        "company_data": {
            "tech_stack": target.tech_stack,
            "is_it_company": target.is_it_company,
            "description": target.description
        },
        "logs": []
    }

    print(f"🚀 ЗАПУСК АГЕНТА ПО КОМПАНИИ: {target.name}")
    app.invoke(inputs)


if __name__ == "__main__":
    run_agent()
