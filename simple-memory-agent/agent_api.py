import uuid
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from agent import Agent

load_dotenv()

app = FastAPI(
    title="Memory Agent API",
    description="Multi-tenant conversational agent with semantic memory",
    version="1.0.0"
)
_session_cache: Dict[str, Agent] = {}


def _get_or_create_agent(user_id: str, run_id: str) -> Agent:
    if run_id in _session_cache:
        return _session_cache[run_id]

    agent = Agent(user_id=user_id, run_id=run_id)
    _session_cache[run_id] = agent
    return agent


class InvocationRequest(BaseModel):
    user_id: str = Field(..., description="User identifier for memory isolation")
    run_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    query: str = Field(..., description="User's message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context/tags")


class InvocationResponse(BaseModel):
    response: str
    user_id: str
    run_id: str


@app.get("/ping")
def ping():
    return {"status": "ok", "message": "Memory Agent API is running"}


@app.post("/invocation", response_model=InvocationResponse)
def invocation(request: InvocationRequest):
    run_id = request.run_id or str(uuid.uuid4())[:8]

    try:
        agent = _get_or_create_agent(request.user_id, run_id)
        response_text = agent.chat(request.query)
        return InvocationResponse(
            response=response_text,
            user_id=request.user_id,
            run_id=run_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
