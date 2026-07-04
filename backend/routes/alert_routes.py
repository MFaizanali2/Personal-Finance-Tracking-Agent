import logging
from fastapi import APIRouter
from backend.alerts.alert_system import AlertSystem

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/current")
async def get_current_alerts():
    alert_system = AlertSystem()
    alerts = await alert_system.get_current_alerts()
    return {"alerts": alerts}


@router.get("/history")
async def get_alert_history():
    alert_system = AlertSystem()
    history = await alert_system.get_alert_history()
    return {"alerts": history}


@router.delete("/{alert_id}")
async def dismiss_alert(alert_id: str):
    alert_system = AlertSystem()
    success = await alert_system.dismiss_alert(alert_id)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"status": "dismissed", "alert_id": alert_id}


@router.get("/summary")
async def alert_summary():
    alert_system = AlertSystem()
    summary = await alert_system.get_alert_summary()
    return summary
