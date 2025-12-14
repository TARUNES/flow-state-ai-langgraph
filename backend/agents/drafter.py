from backend.state import ProtocolState

def draft_protocol(state: ProtocolState) -> dict:
    """
    Drafting agent that generates or refines a CBT protocol.
    
    It moves the current draft to previous_drafts, increments the iteration count,
    and generates a new draft based on the user intent and any feedback.
    """
    
    # 1. Archive current draft if it exists
    # note: with the reducer, logic here changes slightly to avoid double appending if not careful,
    # but since this node runs sequentially before parallel nodes, we can just return the new value for the list reducer.
    current_draft = state.get("current_draft")
    
    # 2. Extract context for generation
    user_intent = state.get("user_intent", "")
    feedback = state.get("feedback_from_agents", {})
    iteration = state.get("iteration_count", 0)
    
    # 3. Generate Content
    from backend.config import get_llm
    from langchain_core.messages import SystemMessage, HumanMessage
    
    llm = get_llm()
    
    if llm:
        import sys
        print(f"--- [Drafter] Generating draft #{iteration + 1} using {llm.__class__.__name__} ---", file=sys.stderr)
        system_instructions = (
            "You are an expert CBT (Cognitive Behavioral Therapy) Protocol Designer.\n"
            "Your task is to create specific, actionable therapeutic exercises.\n"
            "Output clear, structured steps for the user to follow."
        )
        
        user_prompt = (
            f"User Intent: {user_intent}\n"
            f"Current Iteration: {iteration + 1}\n"
        )
        
        if feedback:
            user_prompt += f"\nCRITICAL FEEDBACK TO ADDRESS:\n{list(feedback.values())}"
            
        try:
            response = llm.invoke([
                SystemMessage(content=system_instructions),
                HumanMessage(content=user_prompt)
            ])
            draft_content = response.content
        except Exception as e:
            draft_content = f"Error generating content with LLM: {str(e)}"
            
    else:
        # Fallback Mock logic
        draft_content = (
            f"Draft #{iteration + 1} for intent: '{user_intent}'.\n"
            f"Addressing feedback: {list(feedback.values()) if feedback else 'None'}."
            "\n\n[CBT Exercise Content Placeholder]\n"
            "- Step 1: Identification\n"
            "- Step 2: Challenge\n"
            "- Step 3: Reframing"
        )
    
    updates = {
        "user_intent": user_intent,
        "current_draft": draft_content,
        "iteration_count": iteration + 1,
        "status": "reviewing",
        # Clear feedback for new round
        "feedback_from_agents": {"__RESET__": True} 
    }

    if current_draft:
        updates["previous_drafts"] = [current_draft]
    
    return updates
