from backend.state import ProtocolState
from backend.config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import re

def review_safety(state: ProtocolState) -> dict:
    """
    Safety Agent that reviews the current draft for risky content using an LLM.
    Returns partial update merging into feedback.
    """
    current_draft = state.get("current_draft", "")
    llm = get_llm()
    
    if not llm:
        return {
            "safety_score": 1.0,
            "feedback_from_agents": {"safety": "LLM not available. Assuming safe."}
        }
    
    prompt = (
        "You are a Clinical Safety Supervisor. "
        "Review the following CBT protocol for any risk of self-harm, medical advice, or dangerous instructions.\n"
        "Output ONLY a JSON-like string in this format:\n"
        "Score: <1.0 for Safe, 0.5 for Warning, 0.0 for Critical>\n"
        "Feedback: <one sentence safety assessment>\n\n"
        f"Draft:\n{current_draft}"
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content
        
        # Parse Score
        score_match = re.search(r"Score:\s*([\d\.]+)", response)
        score = float(score_match.group(1)) if score_match else 1.0
        
        # Parse Feedback
        feedback_match = re.search(r"Feedback:\s*(.+)", response, re.DOTALL)
        notes = feedback_match.group(1).strip() if feedback_match else response
        
    except Exception as e:
        import sys
        print(f"Safety Agent Error: {e}", file=sys.stderr)
        score = 0.5
        notes = "Error during safety evaluation."

    return {
        "safety_score": score,
        "feedback_from_agents": {"safety": notes}
    }
