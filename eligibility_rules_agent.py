"""
Agent 4: Eligibility and Rules Agent.
Evaluates product-specific lending rules and lender policies without cross-leakage.
Uses dedicated PersonalLoanPolicy and EducationLoanPolicy rule engines,
supported by externalized YAML configurations.
"""

from typing import Dict, Any, List, Optional
import yaml
from pathlib import Path

from config.settings import CONFIG_DIR
from models.schemas import EligibilityRulesResult, RuleEvaluationItem
from services.personal_loan_policy import PersonalLoanPolicy
from services.education_loan_policy import EducationLoanPolicy


class EligibilityRulesAgent:
    """Agent 4: Configurable rule engine for lending product policies."""

    def __init__(self):
        self.yaml_rules = self._load_rules_config()

    def _load_rules_config(self) -> List[Dict[str, Any]]:
        rules_path = CONFIG_DIR / "loan_rules.yaml"
        if rules_path.exists():
            with open(rules_path, "r") as f:
                data = yaml.safe_load(f)
                return data.get("rules", [])
        return []

    def evaluate_rules(
        self,
        applicant_data: Dict[str, Any],
        validation_result: Optional[Dict[str, Any]] = None,
        financial_result: Optional[Dict[str, Any]] = None
    ) -> EligibilityRulesResult:
        rule_items: List[RuleEvaluationItem] = []
        passed_count = 0
        failed_count = 0
        requires_human_review = False

        loan_product = applicant_data.get("loan_product", "PERSONAL_LOAN")
        fin_data = financial_result or {}

        # 1. Evaluate Product-Specific Policy Rules (No cross-contamination)
        if loan_product == "EDUCATION_LOAN":
            policy_evals = EducationLoanPolicy.evaluate_rules(applicant_data, fin_data)
        else:
            policy_evals = PersonalLoanPolicy.evaluate_rules(applicant_data, fin_data)

        for p_rule in policy_evals:
            res = p_rule.get("result", "PASS")
            sev = p_rule.get("severity", "WARNING")
            review_needed = p_rule.get("human_review_required", False)

            if res == "PASS":
                passed_count += 1
            else:
                failed_count += 1
                if sev == "BLOCKING" or review_needed:
                    requires_human_review = True

            rule_items.append(RuleEvaluationItem(
                rule_id=p_rule.get("rule_id", "POL-RULE"),
                name=p_rule.get("name", "Policy Rule"),
                condition=p_rule.get("condition", "Verified Policy"),
                severity=sev,
                result=res,
                explanation=p_rule.get("explanation", ""),
                human_review_required=review_needed and (res == "FAIL")
            ))

        # 2. General Configurable Baseline Rules from YAML (Age limits, minimum credit score where available)
        context = dict(applicant_data)
        age = int(context.get("age", 25))
        tenure_months = int(context.get("loan_tenure_months", 12))
        context["age_at_maturity"] = age + (tenure_months / 12.0)
        context["dti_ratio"] = fin_data.get("dti_ratio", 0.0)

        for rule in self.yaml_rules:
            # Avoid duplicating DTI rule if already evaluated in product policy
            r_id = rule.get("id", "")
            if "DTI" in r_id and any(item.rule_id == "PL-RULE-DTI" for item in rule_items):
                continue
            if "MIN_INCOME" in r_id and loan_product == "EDUCATION_LOAN":
                continue  # Student income not required

            field = rule.get("field", "")
            operator = rule.get("operator", "==")
            expected_val = rule.get("value")
            actual_val = context.get(field)

            if actual_val is None:
                continue

            passed = False
            try:
                if operator == ">=":
                    passed = float(actual_val) >= float(expected_val)
                elif operator == "<=":
                    passed = float(actual_val) <= float(expected_val)
                elif operator == ">":
                    passed = float(actual_val) > float(expected_val)
                elif operator == "<":
                    passed = float(actual_val) < float(expected_val)
                elif operator == "==":
                    passed = actual_val == expected_val
                elif operator == "!=":
                    passed = actual_val != expected_val
            except Exception:
                passed = False

            sev = rule.get("severity", "WARNING")
            review_req = rule.get("human_review_required", False)

            if passed:
                passed_count += 1
                res = "PASS"
                expl = f"Criteria satisfied: {field} ({actual_val}) {operator} {expected_val}."
            else:
                failed_count += 1
                res = "FAIL"
                expl = f"{rule.get('failure_explanation', 'Rule condition unmet')}: {actual_val} vs required {operator} {expected_val}."
                if sev == "BLOCKING" or review_req:
                    requires_human_review = True

            rule_items.append(RuleEvaluationItem(
                rule_id=r_id,
                name=rule.get("name", "Baseline Rule"),
                condition=f"{field} {operator} {expected_val}",
                severity=sev,
                result=res,
                explanation=expl,
                human_review_required=review_req and (res == "FAIL")
            ))

        # Check validation agent status
        if validation_result and not validation_result.get("is_valid", True):
            requires_human_review = True

        # Synthesis
        if any(r.result == "FAIL" and r.severity == "BLOCKING" for r in rule_items):
            preliminary_eligibility = "INELIGIBLE_RULES_FAIL"
            summary = "One or more mandatory BLOCKING policy rules failed. Pre-screening cannot proceed automatically."
        elif requires_human_review or failed_count > 0:
            preliminary_eligibility = "CONDITIONAL_REVIEW"
            summary = f"{failed_count} rule condition(s) triggered policy exceptions. Requires underwriter review."
        else:
            preliminary_eligibility = "ELIGIBLE_PRE_SCREEN"
            summary = "All evaluated product eligibility rules passed standard baseline thresholds."

        return EligibilityRulesResult(
            loan_product=loan_product,
            policy_version="v2.4-education" if loan_product == "EDUCATION_LOAN" else "v2.4-personal",
            rules_evaluated=len(rule_items),
            rules_passed=passed_count,
            rules_failed=failed_count,
            rule_items=rule_items,
            requires_human_review=requires_human_review,
            summary=summary,
            preliminary_eligibility=preliminary_eligibility
        )
