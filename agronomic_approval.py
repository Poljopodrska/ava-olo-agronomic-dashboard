"""
AVA OLO Agronomic Approval Dashboard - Port 8007
Expert dashboard for conversation approval and management
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import httpx
import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AVA OLO Agronomic Approval Dashboard",
    description="Expert dashboard for conversation approval and management",
    version="1.0.0"
)

# Setup templates
templates = Jinja2Templates(directory="services/templates")

async def get_api_gateway_data(endpoint: str) -> Dict[str, Any]:
    """Get data from API Gateway"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"http://localhost:8000{endpoint}")
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API Gateway returned status {response.status_code}")
                return {"error": f"API returned status {response.status_code}"}
    except Exception as e:
        logger.error(f"Failed to connect to API Gateway: {str(e)}")
        return {"error": str(e)}

async def send_approval_request(endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Send approval request to API Gateway"""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"http://localhost:8000{endpoint}", json=data)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API Gateway returned status {response.status_code}")
                return {"error": f"API returned status {response.status_code}"}
    except Exception as e:
        logger.error(f"Failed to send approval request: {str(e)}")
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Agronomic approval dashboard home"""
    # Get all conversations grouped by approval status
    conversations_data = await get_api_gateway_data("/api/v1/conversations/approval")
    
    if "error" in conversations_data:
        conversations = {"unapproved": [], "approved": []}
    else:
        conversations = conversations_data.get("conversations", {"unapproved": [], "approved": []})
    
    return templates.TemplateResponse("agronomic_approval.html", {
        "request": request,
        "conversations": conversations,
        "selected_conversation": None,
        "message": None
    })

@app.get("/conversation/{conversation_id}", response_class=HTMLResponse)
async def get_conversation_details(request: Request, conversation_id: int):
    """Get details for specific conversation"""
    # Get all conversations
    conversations_data = await get_api_gateway_data("/api/v1/conversations/approval")
    
    if "error" in conversations_data:
        conversations = {"unapproved": [], "approved": []}
    else:
        conversations = conversations_data.get("conversations", {"unapproved": [], "approved": []})
    
    # Get specific conversation details
    conversation_data = await get_api_gateway_data(f"/api/v1/conversations/{conversation_id}")
    selected_conversation = conversation_data.get("conversation", None) if "error" not in conversation_data else None
    
    return templates.TemplateResponse("agronomic_approval.html", {
        "request": request,
        "conversations": conversations,
        "selected_conversation": selected_conversation,
        "message": None
    })

@app.post("/approve_message", response_class=HTMLResponse)
async def approve_message(request: Request, conversation_id: int = Form(...), action: str = Form(...)):
    """Approve individual message"""
    result = await send_approval_request("/api/v1/conversations/approve", {
        "conversation_id": conversation_id,
        "action": action
    })
    
    # Get updated data
    conversations_data = await get_api_gateway_data("/api/v1/conversations/approval")
    conversations = conversations_data.get("conversations", {"unapproved": [], "approved": []}) if "error" not in conversations_data else {"unapproved": [], "approved": []}
    
    conversation_data = await get_api_gateway_data(f"/api/v1/conversations/{conversation_id}")
    selected_conversation = conversation_data.get("conversation", None) if "error" not in conversation_data else None
    
    message = result.get("message", "Action completed") if "error" not in result else f"Error: {result['error']}"
    
    return templates.TemplateResponse("agronomic_approval.html", {
        "request": request,
        "conversations": conversations,
        "selected_conversation": selected_conversation,
        "message": message
    })

@app.post("/bulk_approve", response_class=HTMLResponse)
async def bulk_approve(request: Request, farmer_id: int = Form(None), action: str = Form(...)):
    """Bulk approve conversations"""
    data = {"action": action}
    if farmer_id:
        data["farmer_id"] = farmer_id
    
    result = await send_approval_request("/api/v1/conversations/bulk_approve", data)
    
    # Get updated data
    conversations_data = await get_api_gateway_data("/api/v1/conversations/approval")
    conversations = conversations_data.get("conversations", {"unapproved": [], "approved": []}) if "error" not in conversations_data else {"unapproved": [], "approved": []}
    
    message = result.get("message", "Bulk action completed") if "error" not in result else f"Error: {result['error']}"
    
    return templates.TemplateResponse("agronomic_approval.html", {
        "request": request,
        "conversations": conversations,
        "selected_conversation": None,
        "message": message
    })

@app.post("/send_manual_message", response_class=HTMLResponse)
async def send_manual_message(request: Request, farmer_id: int = Form(...), message: str = Form(...)):
    """Send manual message to farmer"""
    result = await send_approval_request("/api/v1/conversations/manual_message", {
        "farmer_id": farmer_id,
        "message": message
    })
    
    # Get updated data
    conversations_data = await get_api_gateway_data("/api/v1/conversations/approval")
    conversations = conversations_data.get("conversations", {"unapproved": [], "approved": []}) if "error" not in conversations_data else {"unapproved": [], "approved": []}
    
    message_result = result.get("message", "Manual message sent") if "error" not in result else f"Error: {result['error']}"
    
    return templates.TemplateResponse("agronomic_approval.html", {
        "request": request,
        "conversations": conversations,
        "selected_conversation": None,
        "message": message_result
    })

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "service": "Agronomic Approval Dashboard",
        "status": "healthy",
        "port": 8007,
        "purpose": "Expert dashboard for conversation approval and management"
    }

if __name__ == "__main__":
    import uvicorn
    print("🌾 Starting AVA OLO Agronomic Approval Dashboard on port 8007")
    uvicorn.run(app, host="0.0.0.0", port=8007)