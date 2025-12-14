import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END
from backend.state import ProtocolState
from backend.agents.drafter import draft_protocol
from backend.agents.safety import review_safety
from backend.agents.empathy import critique_empathy
from backend.agents.supervisor import supervisor_node

# Pass-through nodes. Returns partial update.
def supervisor_step(state: ProtocolState) -> dict:
    return {} # No state update, just routing

def human_review_step(state: ProtocolState) -> dict:
    if state.get("human_action") == "revise":
        return {"status": "reviewing"}
    return {"status": "approved"}

# 1. Initialize Graph
workflow = StateGraph(ProtocolState)

# 2. Add Nodes
workflow.add_node("drafter", draft_protocol)
workflow.add_node("safety", review_safety)
workflow.add_node("empathy", critique_empathy)
workflow.add_node("supervisor", supervisor_step)
workflow.add_node("human_review", human_review_step)

# 3. Define Entry
workflow.set_entry_point("drafter")

# 4. Define Edges
workflow.add_edge("drafter", "safety")
workflow.add_edge("drafter", "empathy")
workflow.add_edge("safety", "supervisor")
workflow.add_edge("empathy", "supervisor")

# 5. Conditional Logic
workflow.add_conditional_edges(
    "supervisor",
    supervisor_node,
    {
        "revise": "drafter",
        "halt": "human_review",   # Pause for human
        "approve": "human_review" # Auto-approve but still require human sign-off
    }
)

def route_human_decision(state: ProtocolState):
    if state.get("human_action") == "revise":
        return "revise"
    return "approve"

# Route based on human decision
workflow.add_conditional_edges(
    "human_review",
    route_human_decision,
    {
        "revise": "drafter",
        "approve": END
    }
)

# 6. Checkpointing Setup
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# 7. Compile with Interrupt
graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=["human_review"]
)
