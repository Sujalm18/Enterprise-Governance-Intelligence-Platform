import logging
from datetime import datetime
import requests
from sqlalchemy.orm import Session
from backend.app.models import Organization

logger = logging.getLogger("governance_copilot.services.integrations")

def get_integration_settings(db: Session, tenant_id: int):
    org = db.query(Organization).filter(Organization.id == tenant_id).first()
    if not org:
        return None, None
    return org.slack_webhook_url, org.teams_webhook_url

def send_slack_alert(webhook_url: str, title: str, message: str, severity: str, details: str = None) -> bool:
    if not webhook_url:
        return False
    
    color = "#FF0000" if severity.lower() in ("critical", "high", "p1") else "#FFC000"
    
    payload = {
        "attachments": [
            {
                "fallback": f"[{severity.upper()}] {title}: {message}",
                "color": color,
                "pretext": "🚨 *Governance Copilot Alert*",
                "title": title,
                "text": message,
                "fields": [
                    {
                        "title": "Severity / Priority",
                        "value": severity.upper(),
                        "short": True
                    }
                ],
                "footer": "Governance Operations Center",
                "ts": int(datetime.utcnow().timestamp())
            }
        ]
    }
    
    if details:
        payload["attachments"][0]["fields"].append({
            "title": "Details",
            "value": details,
            "short": False
        })
        
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code == 200:
            logger.info("Successfully sent Slack alert")
            return True
        else:
            logger.error(f"Failed to send Slack alert: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Slack alert: {e}")
        return False

def send_teams_alert(webhook_url: str, title: str, message: str, severity: str, details: str = None) -> bool:
    if not webhook_url:
        return False
        
    theme_color = "FF0000" if severity.lower() in ("critical", "high", "p1") else "FFC000"
    
    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": theme_color,
        "summary": f"Governance Alert - {severity.upper()}",
        "sections": [
            {
                "activityTitle": "🚨 Governance Copilot Alert",
                "activitySubtitle": title,
                "facts": [
                    {"name": "Severity", "value": severity.upper()}
                ],
                "text": message,
                "markdown": True
            }
        ]
    }
    
    if details:
        payload["sections"][0]["facts"].append({"name": "Details", "value": details})
        
    try:
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code in (200, 201, 202):
            logger.info("Successfully sent Teams alert")
            return True
        else:
            logger.error(f"Failed to send Teams alert: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending Teams alert: {e}")
        return False

def trigger_governance_alerts(db: Session, tenant_id: int, title: str, message: str, severity: str, details: str = None):
    slack_url, teams_url = get_integration_settings(db, tenant_id)
    if not slack_url and not teams_url:
        logger.info(f"No webhooks configured for tenant {tenant_id}. Skipping alerts.")
        return
        
    if slack_url:
        send_slack_alert(slack_url, title, message, severity, details)
    if teams_url:
        send_teams_alert(teams_url, title, message, severity, details)
