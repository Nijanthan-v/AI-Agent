import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional


from agent import run_agent
from tools import (
    execute_resolution_action,
    save_ticket_tool,
    get_tickets_tool,
    get_ticket_by_id_tool,
    update_ticket_status_tool
)

app = FastAPI(
    title="AI Agent Microservice API",
    description="Dynamic LangGraph AI Agent with Deterministic Anti-Hallucination Circuit Breaker and PostgreSQL Persistence.",
    version="1.0.0"
)

# Enable CORS for external Frontend UI apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiagnoseRequest(BaseModel):
    user_id: Optional[str] = "usr_alex_01"
    user_email: Optional[str] = "alex@techcorp.io"
    stripe_customer_id: Optional[str] = "cus_stripe_alex123"
    issue_description: str

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

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "AI Agent Microservice",
        "orchestrator": "LangGraph StateGraph",
        "auditor": "Deterministic Anti-Hallucination Circuit Breaker",
        "persistence": "PostgreSQL tickets"
    }

@app.get("/tickets")
def list_tickets(status: Optional[str] = None):
    """
    Fetches all tickets, optionally filtered by status (awaiting_approval, resolved, rejected).
    """
    tickets = get_tickets_tool(status)
    return {"count": len(tickets), "tickets": tickets}

@app.get("/tickets/{ticket_id}")
def get_single_ticket(ticket_id: str):
    """
    Fetches details for a specific ticket.
    """
    ticket = get_ticket_by_id_tool(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{ticket_id}' not found.")
    return ticket

@app.post("/diagnose")
def diagnose_ticket(req: DiagnoseRequest):
    """
    Triggers the LangGraph agent for a dynamic request payload and persists the ticket to PostgreSQL.
    """
    if not req.issue_description:
        raise HTTPException(status_code=400, detail="issue_description is required.")
        
    result = run_agent(req.model_dump())
    
    # Persist the ticket and its full audit trail to database
    ticket_id = save_ticket_tool(result)
    result["ticket_id"] = ticket_id
    
    return result

@app.post("/approve")
def approve_resolution(req: ApproveRequest):
    """
    Executes an approved resolution action in the database and updates ticket status to 'resolved'.
    """
    if not req.user_id or not req.action:
        raise HTTPException(status_code=400, detail="user_id and action are required.")
        
    result = execute_resolution_action(
        action=req.action,
        user_id=req.user_id,
        customer_id=req.stripe_customer_id
    )
    
    # Update ticket status in database
    update_ticket_status_tool(
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

@app.post("/reject")
def reject_resolution(req: RejectRequest):
    """
    Rejects the proposed resolution and routes the ticket to manual human escalation.
    """
    update_ticket_status_tool(
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
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
