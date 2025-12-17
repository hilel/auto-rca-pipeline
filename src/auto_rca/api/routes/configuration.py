"""Configuration management endpoints"""

from fastapi import APIRouter, HTTPException

from auto_rca.api.schemas import ConfigResponse, ConfigRequest
from auto_rca.repositories import get_session_field, set_session_field

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get(
    "/session-field",
    response_model=ConfigResponse,
    summary="Get session identifier field",
    description="""Get the current field name used for session identification.
    
    **Dynamic Configuration:**
    The session identifier field determines which field in the log entries will be used
    as the primary key for grouping logs into sessions. By default, this is 'session_id',
    but it can be changed to other fields like 'token', 'order_id', 'transaction_id', etc.
    
    **Learn More:**
    - [Session Management in Log Analysis](https://en.wikipedia.org/wiki/Session_(computer_science))
    """,
    response_description="Current session identifier field configuration"
)
async def get_session_field_config():
    """Get the current session identifier field"""
    try:
        field = get_session_field()
        return {
            "success": True,
            "message": "Configuration retrieved successfully",
            "data": {
                "session_field": field
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve configuration: {str(e)}"
        )


@router.post(
    "/session-field",
    response_model=ConfigResponse,
    summary="Update session identifier field",
    description="""Update the field name used for session identification.
    
    **Impact:**
    Changing this field affects how future log processing operations group logs into sessions.
    The new field will be checked first, with fallback to the default priority chain:
    session_id > request_id > user_id > ip_address
    
    **Common Use Cases:**
    - Use 'token' for token-based session tracking
    - Use 'order_id' for e-commerce transaction logs
    - Use 'transaction_id' for banking/payment logs
    - Use 'correlation_id' for distributed tracing
    
    **Note:**
    This change persists in the database and will apply to all subsequent API calls
    until changed again or the database is reset.
    """,
    response_description="Updated session identifier field configuration"
)
async def update_session_field_config(request: ConfigRequest):
    """Update the session identifier field"""
    try:
        set_session_field(request.session_field)
        return {
            "success": True,
            "message": f"Session field updated to '{request.session_field}'",
            "data": {
                "session_field": request.session_field
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update configuration: {str(e)}"
        )
