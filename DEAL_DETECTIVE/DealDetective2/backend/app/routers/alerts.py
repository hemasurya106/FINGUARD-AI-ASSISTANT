from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.database import get_db
from app.models import PriceAlert

router = APIRouter()

# Request/Response Models
class SetAlertRequest(BaseModel):
    product_url: str
    target_price: float
    email: EmailStr

class SetAlertResponse(BaseModel):
    alert_id: int
    message: str
    product_url: str
    target_price: float
    email: str

class AlertItem(BaseModel):
    id: int
    product_url: str
    target_price: float
    last_checked: Optional[str]
    created_at: Optional[str]

class UserAlertsResponse(BaseModel):
    email: str
    alerts: List[AlertItem]

# Endpoints
@router.post("/set-alert", response_model=SetAlertResponse)
async def set_alert(
    request: SetAlertRequest,
    db: Session = Depends(get_db)
):
    # Validate URL
    if not request.product_url or not request.product_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid product URL")
    
    # Validate target price
    if request.target_price <= 0:
        raise HTTPException(status_code=400, detail="Target price must be greater than 0")
    
    # Check if alert already exists for this URL and email
    existing_alert = db.query(PriceAlert).filter(
        PriceAlert.product_url == request.product_url,
        PriceAlert.email == request.email,
        PriceAlert.is_active == True
    ).first()
    
    if existing_alert:
        # Update existing alert
        existing_alert.target_price = request.target_price
        # Update last_checked so it gets picked up again if needed (or just leave it)
        # existing_alert.last_checked = datetime.utcnow() # Removed to avoid tz confusion for now
        db.commit()
        db.refresh(existing_alert)
        
        return SetAlertResponse(
            alert_id=existing_alert.id,
            message="Alert updated successfully",
            product_url=existing_alert.product_url,
            target_price=existing_alert.target_price,
            email=existing_alert.email
        )
    
    # Create new alert
    new_alert = PriceAlert(
        product_url=request.product_url,
        target_price=request.target_price,
        email=request.email,
        is_active=True
    )
    
    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)
    
    return SetAlertResponse(
        alert_id=new_alert.id,
        message="Alert created successfully. You will be notified when the price drops below your threshold.",
        product_url=new_alert.product_url,
        target_price=new_alert.target_price,
        email=new_alert.email
    )

@router.get("/alerts/{email}", response_model=UserAlertsResponse)
async def get_user_alerts(
    email: EmailStr,
    db: Session = Depends(get_db)
):
    """Get all active alerts for a user by email"""
    alerts = db.query(PriceAlert).filter(
        PriceAlert.email == email,
        PriceAlert.is_active == True
    ).all()
    
    return {
        "email": email,
        "alerts": [
            {
                "id": alert.id,
                "product_url": alert.product_url,
                "target_price": alert.target_price,
                "last_checked": alert.last_checked.isoformat() if alert.last_checked else None,
                "created_at": alert.created_at.isoformat() if alert.created_at else None
            }
            for alert in alerts
        ]
    }

@router.delete("/alerts/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Deactivate an alert"""
    alert = db.query(PriceAlert).filter(PriceAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_active = False
    db.commit()
    
    return {"message": "Alert deactivated successfully"}
