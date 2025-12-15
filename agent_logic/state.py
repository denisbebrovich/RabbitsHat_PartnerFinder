from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator


class AgentState(TypedDict):
    # Данные о компании (вход)
    company_id: str
    company_name: str
    company_data: Dict[str, Any]  # tech_stack, description, etc.

    # Результаты работы узлов
    score: float
    is_relevant: bool
    draft_email: Optional[str]
    final_email: Optional[str]

    # Статусы
    status: str  # 'processing', 'skipped', 'drafted', 'approved', 'sent'
    error: Optional[str]

    # Лог действий (чтобы мы видели, что делал агент)
    logs: Annotated[List[str], operator.add]