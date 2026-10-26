"""
Agent 1: Coordinator Agent.
Workflow orchestrator: manages execution lifecycle, state transitions,
coordinates Agents 2-7 sequentially, logs agent run traces, and safely escalates exceptions.
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from models.schemas import (
    ApplicationStatus,
    PreliminaryOutcome,
    AgentRunLog
)
from agents.data_validation_agent import DataValidationAgent
from agents.financial_analysis_agent import FinancialAnalysisAgent
from agents.eligibility_rules_agent import EligibilityRulesAgent
from agents.credit_risk_agent import CreditRiskAgent
from agents.risk_explanation_agent import RiskExplanationAgent
from agents.record_management_agent import RecordManagementAgent
from services.audit_service import AuditService
from services.database import create_fraud_case

logger = logging.getLogger(__name__)


class CoordinatorAgent:
    """Agent 1: Primary Orchestrator for the multi-agent loan pre-screening lifecycle."""

    def __init__(self):
        # Instantiate constituent specialized agents
        self.validation_agent = DataValidationAgent()
        self.financial_agent = FinancialAnalysisAgent()
        self.rules_agent = EligibilityRulesAgent()
        self.credit_risk_agent = CreditRiskAgent()
        self.explanation_agent = RiskExplanationAgent()
        self.record_agent = RecordManagementAgent()

    @staticmethod
    def generate_application_id() -> str:
        date_str = datetime.utcnow().strftime("%Y%m%d")
        rand_str = uuid.uuid4().hex[:6].upper()
        return f"APP-{date_str}-{rand_str}"

    @staticmethod
    def generate_trace_id() -> str:
        return f"TRC-{uuid.uuid4().hex[:8].upper()}"

    def process_application(
        self,
        applicant_form_data: Dict[str, Any],
        uploaded_documents: Optional[List[Dict[str, Any]]] = None,
        has_open_dispute: bool = False
    ) -> Dict[str, Any]:
        """
        Orchestrate complete pipeline across all seven agents:
        Coordinator -> Validation -> Financial Analysis -> Rules -> Credit Risk -> Explanation -> Record Management
        """
        workflow_trace_id = self.generate_trace_id()
        app_id = applicant_form_data.get("application_id") or self.generate_application_id()
        applicant_form_data["application_id"] = app_id

        if not applicant_form_data.get("applicant_id"):
            applicant_form_data["applicant_id"] = f"APPLICANT-{uuid.uuid4().hex[:8].upper()}"

        agent_logs: List[Dict[str, Any]] = []
        workflow_status = ApplicationStatus.RECEIVED

        from services.database import create_initial_application
        create_initial_application(applicant_form_data, app_id, workflow_trace_id)

        AuditService.log_event(
            actor_id="SYSTEM_COORDINATOR",
            actor_role="ORCHESTRATOR",
            action="APPLICATION_RECEIVED",
            application_id=app_id,
            event_details={"trace_id": workflow_trace_id}
        )

        validation_res = None
        financial_res = None
        rules_res = None
        risk_res = None
        rec_res = None
        fraud_case_id = None

        try:
            # ---------------------------------------------------------
            # Step 1: Agent 2 - Data Validation Agent
            # ---------------------------------------------------------
            workflow_status = ApplicationStatus.VALIDATING
            t0 = time.time()
            v_result = self.validation_agent.validate(applicant_form_data, uploaded_documents)
            v_duration = round((time.time() - t0) * 1000, 2)
            validation_res = v_result.model_dump()

            has_fraud_flags = len(v_result.inconsistency_flags) > 0
            has_dup_flags = len(v_result.duplicate_flags) > 0

            escalation_note = None
            if has_fraud_flags or has_dup_flags:
                escalation_note = "Potential fraud or duplicate application detected."
            elif not v_result.is_valid:
                escalation_note = "Mandatory applicant fields missing or invalid."

            v_status = "WARNING" if escalation_note else "SUCCESS"

            agent_logs.append({
                "agent_name": "DataValidationAgent",
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": v_duration,
                "status": v_status,
                "input_summary": f"Evaluated applicant fields and {len(uploaded_documents or [])} documents",
                "output_summary": f"Valid: {v_result.is_valid}, Action: {v_result.recommended_action}",
                "escalation_reason": escalation_note
            })

            # Check for critical fraud trigger
            if has_fraud_flags or has_dup_flags:
                fraud_flags = v_result.inconsistency_flags + v_result.duplicate_flags
                fraud_case_id = create_fraud_case(
                    application_id=app_id,
                    triggering_flags=fraud_flags,
                    evidence_notes=f"Flagged during DataValidationAgent pass. Duplicate flags: {has_dup_flags}."
                )

            # If mandatory information is missing, pause assessment
            if not v_result.is_valid and not (has_fraud_flags or has_dup_flags):
                workflow_status = ApplicationStatus.MORE_INFORMATION_REQUIRED

            # ---------------------------------------------------------
            # Step 2: Agent 3 - Financial Analysis Agent
            # ---------------------------------------------------------
            t0 = time.time()
            fin_result = self.financial_agent.analyze(applicant_form_data)
            fin_duration = round((time.time() - t0) * 1000, 2)
            financial_res = fin_result.model_dump()

            fin_status = "SUCCESS" if fin_result.is_reliable else "WARNING"
            fin_escalation = None if fin_result.is_reliable else "Financial metrics could not be computed reliably."

            agent_logs.append({
                "agent_name": "FinancialAnalysisAgent",
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": fin_duration,
                "status": fin_status,
                "input_summary": f"Amount: {applicant_form_data.get('requested_loan_amount')}, Rate: {applicant_form_data.get('proposed_interest_rate')}%, Tenure: {applicant_form_data.get('loan_tenure_months')}m",
                "output_summary": f"EMI: {fin_result.monthly_emi}, DTI: {round(fin_result.dti_ratio*100, 1)}%",
                "escalation_reason": fin_escalation
            })

            if workflow_status == ApplicationStatus.VALIDATING:
                workflow_status = ApplicationStatus.FINANCIAL_ANALYSIS_COMPLETED

            # ---------------------------------------------------------
            # Step 3: Agent 4 - Eligibility and Rules Agent
            # ---------------------------------------------------------
            t0 = time.time()
            r_result = self.rules_agent.evaluate_rules(
                applicant_data=applicant_form_data,
                validation_result=validation_res,
                financial_result=financial_res
            )
            r_duration = round((time.time() - t0) * 1000, 2)
            rules_res = r_result.model_dump()

            r_status = "WARNING" if r_result.requires_human_review else "SUCCESS"
            r_escalation = r_result.summary if r_result.requires_human_review else None

            agent_logs.append({
                "agent_name": "EligibilityRulesAgent",
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": r_duration,
                "status": r_status,
                "input_summary": f"Evaluated {r_result.rules_evaluated} product policies",
                "output_summary": f"Passed: {r_result.rules_passed}, Failed: {r_result.rules_failed}, Outcome: {r_result.preliminary_eligibility}",
                "escalation_reason": r_escalation
            })

            if workflow_status == ApplicationStatus.FINANCIAL_ANALYSIS_COMPLETED:
                workflow_status = ApplicationStatus.RULE_CHECK_COMPLETED

            # ---------------------------------------------------------
            # Step 4: Agent 5 - Credit Risk Agent (ML Model)
            # ---------------------------------------------------------
            t0 = time.time()
            risk_result = self.credit_risk_agent.assess_risk(
                applicant_data=applicant_form_data,
                financial_data=financial_res
            )
            risk_duration = round((time.time() - t0) * 1000, 2)
            risk_res = risk_result.model_dump()

            risk_status = "SUCCESS" if risk_result.is_prediction_reliable else "WARNING"
            risk_escalation = None if risk_result.is_prediction_reliable else "; ".join(risk_result.warnings)

            agent_logs.append({
                "agent_name": "CreditRiskAgent",
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": risk_duration,
                "status": risk_status,
                "input_summary": f"Features: {len(risk_result.features_used)}, Bureau Score: {applicant_form_data.get('credit_score')}",
                "output_summary": f"Risk Band: {risk_result.risk_category}, Default Prob: {round((risk_result.risk_score or 0.0)*100, 1)}%",
                "escalation_reason": risk_escalation
            })

            if workflow_status == ApplicationStatus.RULE_CHECK_COMPLETED:
                workflow_status = ApplicationStatus.RISK_ASSESSED

            # ---------------------------------------------------------
            # Step 5: Agent 6 - Risk Explanation and Recommendation Agent
            # ---------------------------------------------------------
            t0 = time.time()
            rec_result = self.explanation_agent.generate_recommendation(
                applicant_data=applicant_form_data,
                validation_data=validation_res,
                financial_data=financial_res,
                rules_data=rules_res,
                risk_data=risk_res,
                has_open_dispute=has_open_dispute,
                has_fraud_flag=has_fraud_flags,
                has_duplicate_flag=has_dup_flags
            )
            rec_duration = round((time.time() - t0) * 1000, 2)
            rec_res = rec_result.model_dump()

            rec_status = "SUCCESS"
            if rec_result.preliminary_outcome != PreliminaryOutcome.PROCEED_TO_NEXT_STAGE:
                rec_status = "PAUSED" if rec_result.preliminary_outcome == PreliminaryOutcome.MORE_INFORMATION_REQUIRED else "WARNING"

            agent_logs.append({
                "agent_name": "RiskExplanationAgent",
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": rec_duration,
                "status": rec_status,
                "input_summary": "Unified synthesis of Validation, Financial, Rules, and ML agents",
                "output_summary": f"Route: {rec_result.preliminary_outcome.value}",
                "escalation_reason": rec_result.pause_reason or ("; ".join(rec_result.escalation_flags) if rec_result.escalation_flags else None)
            })

            # Derive finalized workflow status from Safe Decision Policy output
            if rec_result.preliminary_outcome == PreliminaryOutcome.PROCEED_TO_NEXT_STAGE:
                workflow_status = ApplicationStatus.PRE_SCREENING_COMPLETED
            elif rec_result.preliminary_outcome == PreliminaryOutcome.MORE_INFORMATION_REQUIRED:
                workflow_status = ApplicationStatus.MORE_INFORMATION_REQUIRED
            elif rec_result.preliminary_outcome == PreliminaryOutcome.ON_HOLD_FOR_VERIFICATION:
                workflow_status = ApplicationStatus.DISPUTED if has_open_dispute else ApplicationStatus.ON_HOLD
            else:
                workflow_status = ApplicationStatus.HUMAN_REVIEW_REQUIRED

            # ---------------------------------------------------------
            # Step 6: Agent 7 - Final Record Management Agent
            # ---------------------------------------------------------
            t0 = time.time()
            app_record = {
                "application_id": app_id,
                "loan_product": applicant_form_data.get("loan_product", "PERSONAL_LOAN"),
                "requested_loan_amount": applicant_form_data.get("requested_loan_amount", 0.0),
                "loan_tenure_months": applicant_form_data.get("loan_tenure_months", 12),
                "proposed_interest_rate": applicant_form_data.get("proposed_interest_rate", 12.0),
                "credit_score": applicant_form_data.get("credit_score"),
                "previous_defaults_count": applicant_form_data.get("previous_defaults_count", 0),
                "consent_given": applicant_form_data.get("consent_given", True),
                "status": workflow_status.value,
                "preliminary_outcome": rec_result.preliminary_outcome.value
            }

            rec_management_res = self.record_agent.persist_assessment_bundle(
                applicant_data=applicant_form_data,
                application_data=app_record,
                validation_result=validation_res,
                financial_result=financial_res,
                rules_result=rules_res,
                risk_result=risk_res,
                recommendation_result=rec_res,
                agent_logs=agent_logs,
                trace_id=workflow_trace_id
            )
            rec_mgr_duration = round((time.time() - t0) * 1000, 2)

            agent_logs.append({
                "agent_name": "RecordManagementAgent",
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": rec_mgr_duration,
                "status": "SUCCESS" if rec_management_res.record_saved else "ERROR",
                "input_summary": f"Saved assessment records for {app_id}",
                "output_summary": f"Status: {rec_management_res.database_status}, Logs: {rec_management_res.audit_log_count}",
                "escalation_reason": None
            })

        except Exception as e:
            logger.error(f"Coordinator error processing application {app_id}: {e}", exc_info=True)
            workflow_status = ApplicationStatus.ERROR
            agent_logs.append({
                "agent_name": "CoordinatorAgent",
                "start_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "end_time": datetime.utcnow().strftime("%H:%M:%S.%f")[:-3],
                "duration_ms": 0.0,
                "status": "ERROR",
                "input_summary": f"Workflow failed on trace {workflow_trace_id}",
                "output_summary": "Uncaught exception halted pipeline.",
                "escalation_reason": str(e)
            })

        return {
            "application_id": app_id,
            "workflow_trace_id": workflow_trace_id,
            "status": workflow_status.value,
            "preliminary_outcome": rec_res.get("preliminary_outcome") if rec_res else None,
            "fraud_case_id": fraud_case_id,
            "validation_result": validation_res,
            "financial_result": financial_res,
            "rules_result": rules_res,
            "risk_result": risk_res,
            "recommendation_result": rec_res,
            "agent_logs": agent_logs
        }
