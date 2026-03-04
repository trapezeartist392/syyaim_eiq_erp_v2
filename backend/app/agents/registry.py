from app.agents.lead_scoring import LeadScoringAgent
from app.agents.pr_approval import PRApprovalAgent
from app.agents.three_way_match import ThreeWayMatchAgent
from app.agents.mrp_planning import MRPPlanningAgent
from app.agents.payroll_audit import PayrollAuditAgent
from app.agents.financial_reporting import FinancialReportingAgent

lead_scoring_agent = LeadScoringAgent()
pr_approval_agent = PRApprovalAgent()
three_way_match_agent = ThreeWayMatchAgent()
mrp_planning_agent = MRPPlanningAgent()
payroll_audit_agent = PayrollAuditAgent()
financial_reporting_agent = FinancialReportingAgent()
