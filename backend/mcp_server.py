import asyncio
import uuid
import sys
import os

# Add project root to sys.path so 'backend' module is found
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import MCP, handle if missing
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    import mcp.types as types
except ImportError:
    # If MCP isn't installed in the environment running this script
    # We provide a dummy implementation or exit
    print("MCP library not found. Please install 'mcp'.", file=sys.stderr)
    sys.exit(1)

# FORCE UTF-8 for Windows to support emojis and avoid 'charmap' errors
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

from backend.graph import graph

app = Server("flowstate")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_protocol",
            description="Generate a clinical CBT protocol based on user intent. Returns the draft and status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "intent": {"type": "string", "description": "The clinical intent (e.g., 'Exposure hierarchy for agoraphobia')"},
                },
                "required": ["intent"],
            },
        ),
        types.Tool(
            name="review_protocol",
            description="Submit a human review decision (approve/revise) for a paused protocol thread.",
            inputSchema={
                "type": "object",
                "properties": {
                    "thread_id": {"type": "string", "description": "The Thread ID provided by generate_protocol"},
                    "action": {"type": "string", "enum": ["approve", "revise"], "description": "The decision: 'approve' to finalize, 'revise' to retry"},
                    "feedback": {"type": "string", "description": "Feedback instructions if revising (optional for approval)"}
                },
                "required": ["thread_id", "action"],
            },
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "generate_protocol":
        intent = arguments.get("intent")
        thread_id = str(uuid.uuid4())
        initial_input = {"user_intent": intent}
        config = {"configurable": {"thread_id": thread_id}}
        
        # Invoke graph
        # We run the graph until it either finishes or hits the human review interrupt
        result = graph.invoke(initial_input, config=config)
        
        snapshot = graph.get_state(config)
        # Check if we are at the Human Review node (interrupted)
        is_interrupted = bool(snapshot.next)
        status = "Waiting for Human Review" if is_interrupted else "Completed"
        
        output_text = f"--- FlowState ---\n"
        output_text += f"Status: {status}\n"
        output_text += f"Thread ID: {thread_id}\n"
        output_text += f"Iteration: {result.get('iteration_count')}\n"
        output_text += f"Safety Score: {result.get('safety_score')}\n"
        output_text += f"Empathy Score: {result.get('empathy_score')}\n\n"
        output_text += f"--- Current Draft ---\n{result.get('current_draft')}\n"
        
        if is_interrupted:
            output_text += "\n[ACTION REQUIRED] System paused for Human Review.\n"
            output_text += f"To proceed, call the 'review_protocol' tool with thread_id='{thread_id}' and action='approve' or 'revise'."
            
        return [types.TextContent(type="text", text=output_text)]

    elif name == "review_protocol":
        thread_id = arguments.get("thread_id")
        action = arguments.get("action")
        feedback = arguments.get("feedback")
        
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = graph.get_state(config)
        
        if not snapshot.next:
            return [types.TextContent(type="text", text=f"Thread {thread_id} is already completed or not found.")]
            
        # Update state with human decision
        updates = {"human_action": action}
        if feedback:
            updates["feedback_from_agents"] = {"human": feedback}
            
        graph.update_state(config, updates)
        
        # Resume graph execution (None input resumes from interruption)
        result = graph.invoke(None, config=config)

        final_snapshot = graph.get_state(config)
        is_finished = not final_snapshot.next
        
        status_msg = "Protocol Approved & Finalized!" if is_finished else "Feedback Submitted. New Draft Generated."
        
        output_text = f"--- Review Submitted ---\n"
        output_text += f"Action: {action}\n"
        output_text += f"Status: {status_msg}\n"
        
        if not is_finished:
            output_text += f"\n--- New Draft (Iter {result.get('iteration_count')}) ---\n{result.get('current_draft')}\n"
            output_text += f"\n[NOTE] System is paused again for typical review cycle. Use 'review_protocol' again to finalize."
        
        return [types.TextContent(type="text", text=output_text)]

    raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
