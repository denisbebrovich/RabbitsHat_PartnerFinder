from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator


class AgentState(TypedDict):
    company_id: str
    company_name: str
    company_data: Dict[str, Any]

    score: float
    is_relevant: bool
    draft_email: Optional[str]
    final_email: Optional[str]

    status: str
    error: Optional[str]

    logs: Annotated[List[str], operator.add]
