from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.graph import graph
import uuid

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InitRequest(BaseModel):
    user_intent: str

class ResumeRequest(BaseModel):
    current_draft: str
    action: str = "approve"
    feedback: str = None

@app.post("/thread")
async def start_thread(request: InitRequest):
    """Start a new protocol generation workflow."""
    thread_id = str(uuid.uuid4())
    initial_input = {"user_intent": request.user_intent}
    config = {"configurable": {"thread_id": thread_id}}
    
    # Run until interrupt or end
    # invoke returns the state at the end of execution (or interruption)
    result = graph.invoke(initial_input, config=config)
    
    snapshot = graph.get_state(config)
    
    return {
        "thread_id": thread_id,
        "state": result,
        "next": snapshot.next,
        "status": "interrupted" if snapshot.next else "completed"
    }

@app.get("/thread/{thread_id}")
async def get_thread_state(thread_id: str):
    """Get the current state of a workflow thread."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    return {
        "state": snapshot.values,
        "next": snapshot.next,
        "status": "interrupted" if snapshot.next else "completed"
    }

@app.post("/thread/{thread_id}/resume")
async def resume_thread(thread_id: str, request: ResumeRequest):
    """Resume a workflow thread after human review."""
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = graph.get_state(config)

    if not snapshot.next:
         raise HTTPException(status_code=400, detail="Thread is already completed")

    # Update state with human edits and feedback
    updates = {
        "current_draft": request.current_draft,
        "human_action": request.action
    }
    
    if request.feedback:
        updates["feedback_from_agents"] = {"human": request.feedback}
        
    graph.update_state(config, updates)
    
    # Resume
    result = graph.invoke(None, config=config)
    
    final_snapshot = graph.get_state(config)
    
    return {
        "thread_id": thread_id,
        "state": result,
        "next": final_snapshot.next,
        "status": "interrupted" if final_snapshot.next else "completed"
    }
