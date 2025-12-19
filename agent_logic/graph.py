import sys
import os
from langgraph.graph import StateGraph, END
from ml_service.api_client import BackendClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agent_logic.state import AgentState
from agent_logic.nodes import enrichment_node, score_node, draft_node, approval_node, finalize_skipped_node

DATABASE_URL = "postgresql://admin:password@localhost:5432/partner_finder"

workflow = StateGraph(AgentState)

workflow.add_node("enrichment", enrichment_node)
workflow.add_node("scoring", score_node)
workflow.add_node("drafting", draft_node)
workflow.add_node("approval", approval_node)
workflow.add_node("finalize_skipped", finalize_skipped_node)

workflow.set_entry_point("enrichment")
workflow.add_edge("enrichment", "scoring")

def check_score(state):
    if state.get('is_relevant'):
        return "drafting"
    return "finalize_skipped"

workflow.add_conditional_edges(
    "scoring",
    check_score,
    {
        "drafting": "drafting",
        "finalize_skipped": "finalize_skipped"
    }
)

workflow.add_edge("drafting", "approval")
workflow.add_edge("approval", END)
workflow.add_edge("finalize_skipped", END)

app = workflow.compile()

def run_agent():
    api = BackendClient()
    print(f"🔍 Запрашиваю задачу у API...")

    target_data = api.get_next_company()

    if not target_data:
        print("🎉 Все компании обработаны (или API недоступен)!")
        return

    inputs = {
        "company_id": target_data['hh_id'],
        "company_name": target_data['name'],
        "company_data": {
            "tech_stack": target_data.get('tech_stack', []),
            "is_it_company": target_data.get('is_it_company', False),
            "description": target_data.get('description', ""),
            "vacancies_text": target_data.get('vacancies_text', [])
        },
        "logs": []
    }

    print(f"🚀 ЗАПУСК АГЕНТА: {inputs['company_name']}")
    app.invoke(inputs)