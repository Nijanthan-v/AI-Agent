import os
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from agent import run_agent
from tools import (
    init_db_pool,
    close_db_pool,
    get_db_cursor,
    execute_resolution_action,
    save_ticket_tool,
    get_tickets_tool,
    get_ticket_by_id_tool,
    update_ticket_status_tool
)

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("agent.server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages startup and shutdown events for production deployment.
    """
    logger.info("🚀 Starting AI Agent Microservice API...")
    init_db_pool(minconn=2, maxconn=20)
    yield
    logger.info("🛑 Shutting down AI Agent Microservice API...")
    close_db_pool()

app = FastAPI(
    title="AI Agent Microservice API",
    description="Dynamic LangGraph AI Agent with Deterministic Anti-Hallucination Circuit Breaker and PostgreSQL Persistence.",
    version="1.1.0",
    lifespan=lifespan
)

# CORS Middleware (Configurable via environment variable)
cors_origins_raw = os.getenv("CORS_ORIGINS", "*")
allowed_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiagnoseRequest(BaseModel):
    user_id: Optional[str] = Field(default="usr_alex_01", description="Unique user identifier")
    user_email: Optional[str] = Field(default="alex@techcorp.io", description="Customer email address")
    stripe_customer_id: Optional[str] = Field(default="cus_stripe_alex123", description="Associated Stripe customer ID")
    issue_description: str = Field(..., description="Customer escalation complaint including any trace IDs")

class ApproveRequest(BaseModel):
    user_id: str
    action: str
    ticket_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    operator_notes: Optional[str] = None

class RejectRequest(BaseModel):
    user_id: str
    ticket_id: Optional[str] = None
    reason: Optional[str] = "Operator rejected automated resolution"


@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Active health check reporting database connectivity, engine type, and service state.
    """
    db_status = "offline"
    engine_name = "unknown"
    
    try:
        with get_db_cursor() as (cursor, engine):
            cursor.execute("SELECT 1;")
            db_status = "connected"
            engine_name = engine
    except Exception as e:
        logger.error("Health check DB query failed: %s", e)
        db_status = f"error: {str(e)[:60]}"

    return {
        "status": "online" if db_status == "connected" else "degraded",
        "service": "AI Agent Microservice",
        "version": "1.1.0",
        "orchestrator": "LangGraph StateGraph",
        "auditor": "Deterministic Anti-Hallucination Circuit Breaker",
        "database": {
            "status": db_status,
            "engine": engine_name
        }
    }


@app.get("/tickets", tags=["Tickets"])
async def list_tickets(status: Optional[str] = None):
    """
    Fetches all tickets, optionally filtered by status (awaiting_approval, resolved, rejected).
    Non-blocking offload to thread pool.
    """
    tickets = await asyncio.to_thread(get_tickets_tool, status)
    return {"count": len(tickets), "tickets": tickets}


@app.get("/tickets/{ticket_id}", tags=["Tickets"])
async def get_single_ticket(ticket_id: str):
    """
    Fetches full diagnostic details and audit trail for a specific ticket.
    """
    ticket = await asyncio.to_thread(get_ticket_by_id_tool, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket '{ticket_id}' not found."
        )
    return ticket


@app.post("/diagnose", tags=["Agent Workflow"])
async def diagnose_ticket(req: DiagnoseRequest):
    """
    Dispatches customer payload to the LangGraph state machine.
    Offloaded to a worker thread so the async event loop is never blocked.
    """
    if not req.issue_description.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="issue_description is required."
        )

    # Run LangGraph state machine asynchronously in thread pool
    result = await asyncio.to_thread(run_agent, req.model_dump())
    
    # Persist ticket and audit trail to database
    ticket_id = await asyncio.to_thread(save_ticket_tool, result)
    result["ticket_id"] = ticket_id
    
    return result


@app.post("/approve", tags=["Operator Gate"])
async def approve_resolution(req: ApproveRequest):
    """
    Executes an approved resolution action in the database and updates ticket status to 'resolved'.
    """
    if not req.user_id or not req.action:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id and action are required."
        )
        
    result = await asyncio.to_thread(
        execute_resolution_action,
        action=req.action,
        user_id=req.user_id,
        customer_id=req.stripe_customer_id
    )
    
    # Update ticket status in database
    await asyncio.to_thread(
        update_ticket_status_tool,
        status="resolved" if result["success"] else "action_failed",
        ticket_id=req.ticket_id,
        user_id=req.user_id,
        operator_notes=req.operator_notes or result["details"]
    )
    
    return {
        "status": "resolved" if result["success"] else "failed",
        "ticket_id": req.ticket_id,
        "action_executed": req.action,
        "details": result["details"],
        "operator_notes": req.operator_notes
    }


@app.post("/reject", tags=["Operator Gate"])
async def reject_resolution(req: RejectRequest):
    """
    Rejects the proposed resolution and routes the ticket to manual Tier-3 escalation.
    """
    await asyncio.to_thread(
        update_ticket_status_tool,
        status="rejected",
        ticket_id=req.ticket_id,
        user_id=req.user_id,
        operator_notes=req.reason
    )
    
    return {
        "status": "rejected",
        "ticket_id": req.ticket_id,
        "user_id": req.user_id,
        "reason": req.reason,
        "details": f"Automated action for user '{req.user_id}' rejected by operator. Escalated to tier-3 manual queue."
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
