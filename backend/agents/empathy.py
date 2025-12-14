from backend.state import ProtocolState
from backend.config import get_llm
from langchain_core.messages import SystemMessage, HumanMessage
import re

def critique_empathy(state: ProtocolState) -> dict:
    """
    Empathy Agent that reviews the current draft for empathetic tone using an LLM.
    Returns partial update merging into feedback.
    """
    current_draft = state.get("current_draft", "")
    llm = get_llm()
    
    if not llm:
        # Fallback if no LLM configured
        return {
            "empathy_score": 3.0,
            "feedback_from_agents": {"empathy": "LLM not available for critique. Defaulting to neutral."}
        }

    prompt = (
        "You are an empathetic clinical supervisor. "
        "Evaluate the following CBT protocol draft for warmth, validation, and supportive tone.\n"
        "Output ONLY a JSON-like string in this format:\n"
        "Score: <number between 1.0 and 5.0>\n"
        "Feedback: <one sentence critique>\n\n"
        f"Draft:\n{current_draft}"
    )
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)]).content
        
        # Parse Score
        score_match = re.search(r"Score:\s*([\d\.]+)", response)
        score = float(score_match.group(1)) if score_match else 3.0
        
        # Parse Feedback
        feedback_match = re.search(r"Feedback:\s*(.+)", response, re.DOTALL)
        notes = feedback_match.group(1).strip() if feedback_match else response
        
        # Cap score just in case
        score = max(1.0, min(5.0, score))
        
    except Exception as e:
        import sys
        print(f"Empathy Agent Error: {e}", file=sys.stderr)
        score = 3.0
        notes = "Error during empathy evaluation."

    return {
        "empathy_score": score,
        "feedback_from_agents": {"empathy": notes}
    }
