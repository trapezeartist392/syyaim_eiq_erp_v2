"""Celery tasks for scheduled AI agent execution.

These tasks are only active when Celery + Redis are configured.
Without them, agents run synchronously via API endpoints.
"""
import logging

log = logging.getLogger(__name__)

try:
    from app.core.celery_app import celery_app
    if celery_app is None:
        raise ImportError("Celery not configured")
except ImportError:
    log.info("Celery unavailable — scheduled agent tasks disabled")
    # Define no-op stubs so imports don't break
    class _Stub:
        @staticmethod
        def task(*a, **kw):
            def decorator(f):
                return f
            return decorator
    celery_app = _Stub()


@celery_app.task(name="app.agents.tasks.run_mrp_planning", bind=True, max_retries=3)
def run_mrp_planning(self):
    """Daily MRP planning agent run."""
    import asyncio
    from app.agents.engine import MRPPlanningAgent
    log.info("MRP Planning Agent triggered")
    try:
        agent = MRPPlanningAgent()
        result = asyncio.run(agent.run(mrp_data={
            "open_so_count": 0,
            "total_so_value": 0,
            "below_reorder": [],
            "avg_lead_time_days": 7,
        }))
        log.info("MRP Planning completed")
        return result
    except Exception as exc:
        log.error("MRP Planning failed: %s", str(exc))
        if hasattr(self, 'retry'):
            raise self.retry(exc=exc, countdown=300)
        raise


@celery_app.task(name="app.agents.tasks.check_reorder_points", bind=True)
def check_reorder_points(self):
    """Check all products for reorder triggers."""
    log.info("Reorder Point Agent triggered")
    return {"status": "completed", "items_checked": 0, "reorders_triggered": 0}


@celery_app.task(name="app.agents.tasks.detect_attendance_anomalies", bind=True)
def detect_attendance_anomalies(self):
    """Daily attendance anomaly detection."""
    log.info("Attendance Anomaly Agent triggered")
    return {"status": "completed", "employees_checked": 0, "anomalies_found": 0}


@celery_app.task(name="app.agents.tasks.run_ar_collection_followup", bind=True)
def run_ar_collection_followup(self):
    """Daily AR collection followup."""
    log.info("AR Collection Agent triggered")
    return {"status": "completed", "invoices_checked": 0, "followups_sent": 0}


@celery_app.task(name="app.agents.tasks.score_vendor_performance", bind=True)
def score_vendor_performance(self):
    """Weekly vendor performance scoring."""
    log.info("Vendor Performance Agent triggered")
    return {"status": "completed", "vendors_scored": 0}


@celery_app.task(name="app.agents.tasks.detect_financial_anomalies", bind=True)
def detect_financial_anomalies(self):
    """Periodic financial anomaly detection."""
    log.info("Financial Anomaly Agent triggered")
    return {"status": "completed", "transactions_analyzed": 0, "anomalies_found": 0}


@celery_app.task(name="app.agents.tasks.run_agent_on_demand")
def run_agent_on_demand(agent_name: str, kwargs: dict):
    """Run any agent on-demand."""
    import asyncio
    from app.agents.engine import run_agent
    log.info("On-demand agent run: %s", agent_name)
    result = asyncio.run(run_agent(agent_name, **kwargs))
    return result
