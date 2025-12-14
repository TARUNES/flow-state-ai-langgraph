from typing import TypedDict, List, Dict, Literal, Annotated
import operator

def merge_dict(a: dict, b: dict) -> dict:
    if b.get("__RESET__"):
        return {k: v for k, v in b.items() if k != "__RESET__"}
    return {**a, **b}

class ProtocolState(TypedDict):
    """
    Represents the state of the multi-agent clinical CBT protocol generation system.
    """
    user_intent: str  # LastWriteWins by default
    current_draft: str # LastWriteWins by default
    previous_drafts: Annotated[List[str], operator.add] # Append
    feedback_from_agents: Annotated[Dict[str, str], merge_dict] # Merge
    safety_score: float # LastWriteWins
    empathy_score: float # LastWriteWins
    iteration_count: int # LastWriteWins
    status: Literal["drafting", "reviewing", "halted", "approved"] # LastWriteWins
    human_action: Literal["approve", "revise"] # LastWriteWins
