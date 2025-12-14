from backend.graph import graph
import uuid

def test_graph():
    print("Initializing Graph Test...")
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    initial_input = {
        "user_intent": "Create an exposure hierarchy for social anxiety"
    }
    
    print(f"Starting thread {thread_id} with intent: {initial_input['user_intent']}")
    
    try:
        # 1. Run until first interrupt (Human Review)
        result = graph.invoke(initial_input, config=config)
        print("Graph execution paused (or finished).")
        print("Status:", result.get("status"))
        print("Current Draft Snapshot:", result.get("current_draft")[:50] + "...")
        print("Feedback:", result.get("feedback_from_agents"))
        
        # 2. Check checkpoint
        snapshot = graph.get_state(config)
        if snapshot.next:
            print(f"Interrupted at node: {snapshot.next}")
        else:
            print("Graph finished completely.")
            
    except Exception as e:
        print(f"Graph execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_graph()
