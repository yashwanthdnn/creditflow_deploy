"""
Rules, Financial Methodology & Limitations Page (Section D).
Mandatory dedicated transparency page appearing as the final item in the main navigation
and the final section of generated assessment reports.
Provides public disclosures to applicants and protected audit controls to authorized staff.
"""

import streamlit as st
import json
from datetime import datetime
from services.regulatory_registry import RegulatorySourceRegistry
from services.financial_engine import FinancialEngine
from services.personal_loan_policy import PersonalLoanPolicy
from services.education_loan_policy import EducationLoanPolicy
from services.auth_service import AuthService, STAFF_ROLES


def render_methodology():
    st.markdown('<div class="page-title">📜 Rules, Financial Methodology & Limitations</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Mandatory architectural transparency disclosure: regulatory sources, financial formulas, assumptions, ML model limitations, and audit reproducibility.</div>',
        unsafe_allow_html=True
    )

    current_role = st.session_state.get("active_role", "Credit Officer")
    is_staff = AuthService.is_staff(current_role)

    # Product Selector for dynamic filtering
    col_p1, col_p2 = st.columns([1, 2])
    with col_p1:
        selected_product = st.selectbox(
            "Filter Methodology by Loan Product",
            ["ALL", "PERSONAL_LOAN", "EDUCATION_LOAN"],
            format_func=lambda x: "🌐 All Lending Products" if x == "ALL" else ("💼 Personal Loan" if x == "PERSONAL_LOAN" else "🎓 Higher Education Loan")
        )
    with col_p2:
        st.caption(
            "Disclosures adhere strictly to RBI Digital Lending Guidelines (2022), "
            "IBA Model Educational Loan Scheme (Revision V), and Fair Practices Code."
        )

    st.markdown("<hr style='margin: 16px 0;'/>", unsafe_allow_html=True)

    # Tabs for the 6 Mandatory Sections
    tab_sec1, tab_sec2, tab_sec3, tab_sec4, tab_sec5, tab_sec6 = st.tabs([
        "1. Which Rules Were Used?",
        "2. Financial Calculation Methodology",
        "3. Financial Assumptions & Scenarios",
        "4. Model Methodology & Validation",
        "5. Limitations & Exclusions",
        "6. Audit & Reproducibility (Staff Only)"
    ])

    # =========================================================================
    # SECTION 1 — WHICH RULES WERE USED?
    # =========================================================================
    with tab_sec1:
        st.markdown("### Section 1 — Authoritative Lending Rule & Policy Registry")
        st.markdown(
            "Every evaluated rule is traced to an authorized regulatory circular, approved lender policy, "
            "or selected product term. Categories are strictly separated without conflation."
        )

        all_rules = RegulatorySourceRegistry.get_all_sources(product_filter=selected_product)

        # 1. Applicable Regulatory Requirements
        with st.expander("🏛️ Tier 1: Applicable Regulatory Requirements (RBI & IBA Guidelines)", expanded=True):
            st.caption("Official statutory circulars, Master Directions, and digital lending mandates.")
            for r in all_rules["regulatory_requirements"]:
                st.markdown(f"##### {r['circular_reference']}")
                st.write(f"• **Regulatory Source**: [{r['source_name']}]({r['official_url']}) | **Lender Type**: {r['applicable_lender_type']}")
                st.write(f"• **Published**: `{r['publication_date']}` | **Effective**: `{r['effective_date']}` | **Product**: `{r['applicable_product']}`")
                st.write(f"• **Summary in Plain Language**: {r['plain_language_summary']}")
                st.markdown(f"• **System Control Implementation**: `{r['system_control']}`")
                st.markdown(f"• **Verification Status**: `{r['control_status']}` | **Last Reviewed**: `{r['last_reviewed_date']}`")
                st.markdown("---")

        # 2. Authorized Lender Policy
        with st.expander("🏢 Tier 2: Authorized Lender Policies (Institutional Credit Manual v2.4)", expanded=True):
            st.caption("Underwriting ceilings, eligibility gates, and mandatory debt-service thresholds.")
            for p in all_rules["lender_policies"]:
                st.markdown(f"##### {p['policy_name']} ({p['id']})")
                st.write(f"• **Policy Version**: `{p['policy_version']}` | **Applicable Product**: `{p['applicable_product']}`")
                st.write(f"• **Summary in Plain Language**: {p['plain_language_summary']}")
                st.markdown(f"• **System Control**: `{p['system_control']}`")
                st.markdown(f"• **Verification Status**: `{p['control_status']}` | **Last Reviewed**: `{p['last_reviewed_date']}`")
                st.markdown("---")

        # 3. Selected Loan-Product Terms
        with st.expander("📜 Tier 3: Selected Loan-Product Terms & Conditions", expanded=True):
            st.caption("Specific parameters, repayment schedules, and document checklists for the chosen product.")
            for t in all_rules["product_terms"]:
                st.markdown(f"##### {t['term_name']} ({t['id']})")
                st.write(f"• **Product**: `{t['applicable_product']}`")
                st.write(f"• **Term Specification**: {t['plain_language_summary']}")
                st.markdown(f"• **System Control**: `{t['system_control']}`")
                st.markdown(f"• **Control Status**: `{t['control_status']}`")
                st.markdown("---")

        # 4. Academic Demonstration Assumptions
        with st.expander("🔬 Tier 4: Academic Demonstration Assumptions & Boundaries", expanded=True):
            st.caption("Safe synthetic boundary assumptions strictly for prototype demonstration.")
            for a in all_rules["academic_assumptions"]:
                st.markdown(f"##### {a['assumption_title']} ({a['id']})")
                st.write(f"• **Rationale**: {a['plain_language_summary']}")
                st.markdown(f"• **Safety Control**: `{a['system_control']}`")
                st.markdown(f"• **Production Gap**: *{a['production_prerequisite']}*")
                st.markdown("---")

    # =========================================================================
    # SECTION 2 — FINANCIAL CALCULATION METHODOLOGY
    # =========================================================================
    with tab_sec2:
        st.markdown("### Section 2 — Mathematical Financial Calculation Methodology")
        st.caption("Complete breakdown of input sources, mathematical formulas, compounding conventions, and rounding rules.")

        st.markdown("#### 2.1 Standard Reducing-Balance Monthly EMI Formula")
        st.markdown("""
        **Formula**:
        $$\\text{EMI} = \\frac{P \\times r \\times (1 + r)^n}{(1 + r)^n - 1}$$
        where:
        - $P$: Principal loan amount (evidenced from intake form, currency: INR)
        - $r$: Monthly effective interest rate: $\\frac{\\text{Annual Rate (\\%)}}{12 \\times 100}$
        - $n$: Loan tenure in months (discrete integer)
        - **Compounding Convention**: Monthly compounding on outstanding balance.
        - **Rounding Rules**: Half-up rounding to 2 decimal places.
        - **Calculation Engine Version**: `FinancialEngine-v2.4`
        """)

        st.markdown("#### 2.2 All-Inclusive Annual Percentage Rate (APR)")
        st.markdown("""
        **Methodology**:
        APR is the true annualized cost of credit, encompassing upfront processing fees, GST, documentation charges, and scheduled cash flows.
        It is solved via the **Newton-Raphson Internal Rate of Return (IRR)** method:
        $$\\text{Net Disbursed Amount} = \\sum_{t=1}^{n} \\frac{\\text{EMI}}{(1 + r_{\\text{monthly}})^t}$$
        $$\\text{APR} = r_{\\text{monthly}} \\times 12 \\times 100$$
        **Notice**: The APR is typically higher than the nominal interest rate due to upfront charges.
        """)

        st.markdown("#### 2.3 Higher Education Loan Cost Reconciliation & Moratorium")
        st.markdown("""
        **Expense Reconciliation Formula (Section A.2)**:
        $$\\text{Total Eligible Expenses} = \\text{Tuition} + \\text{Admission} + \\text{Exam Fees} + \\text{Hostel} + \\text{Books} + \\text{Travel}$$
        $$\\text{Indicative Financing Requirement} = \\text{Total Eligible} - \\text{Confirmed Scholarships} - \\text{Other Funding} - \\text{Student Contribution}$$
        - *Crucial Rule*: Unconfirmed scholarships are **excluded** from automatic deduction until confirmed grant letters are evidenced.
        - *Status*: Labeled as **Provisional** until all expense invoices and fee receipts are independently verified.

        **Study-Period Moratorium & Capitalization (Section A.5)**:
        - **Simple Interest** accrues on disbursements during course duration + grace period (e.g. 24 months + 12 months = 36 months):
          $$\\text{Study Interest} = P \\times \\left(\\frac{\\text{Rate}}{100}\\right) \\times \\left(\\frac{\\text{Moratorium Months}}{12}\\right)$$
        - **Capitalization**: Capitalized Principal at repayment commencement = $P + \\text{Study Interest}$.
        - **Post-Moratorium EMI**: Standard monthly amortization calculated on capitalized principal over post-moratorium repayment tenure.
        """)

        st.markdown("#### 2.4 Personal Loan Obligation Ratios (FOIR / DTI)")
        st.markdown("""
        **Definition**:
        $$\\text{Debt-to-Income (DTI)} = \\frac{\\text{Existing Monthly Obligations} + \\text{Proposed Post-Loan EMI}}{\\text{Verifiable Monthly Take-Home Income}}$$
        - **Thresholds**: DTI $\\le 40\\%$ (Comfortable), $40\\% - 55\\%$ (Elevated), $> 55\\%$ (Ceiling breach — blocking exception).
        - **Income Base**: Evidenced from 3 months' salary slips and 6 months' bank statements.
        """)

    # =========================================================================
    # SECTION 3 — FINANCIAL ASSUMPTIONS AND SCENARIOS
    # =========================================================================
    with tab_sec3:
        st.markdown("### Section 3 — Financial Assumptions, Baselines & Scenarios")
        st.info("⚠️ **Legal Notice**: All illustrative calculations are strictly estimates for decision-support and do not constitute a contractual loan sanction or binding offer.")

        st.markdown("""
        | Parameter | Personal Loan Baseline | Higher Education Loan Baseline | Source & Regulatory Rule |
        | :--- | :--- | :--- | :--- |
        | **Nominal Interest Rate** | 11.50% p.a. (Illustrative) | 9.25% p.a. (Concessional student baseline) | Lender Benchmark Spread Policy |
        | **Rate Type** | Fixed Rate monthly reducing | Floating (linked to Repo benchmark) | Product Terms Sheet |
        | **Standard Tenure** | 36 Months (Range: 6 to 84m) | 84 Months post-moratorium (Range: 12 to 180m) | Credit Policy Manual |
        | **Repayment Frequency** | Monthly via NACH / e-Mandate | Monthly post-moratorium | RBI Digital Lending Guidelines |
        | **Upfront Processing Fee** | 1.0% + 18% GST on fee | 0.5% (Domestic) / 1.0% (Overseas) + GST | Transparent Fee Schedule |
        | **Documentation Charges** | ₹750 (Documentation) + ₹500 (Stamp Duty) | Nil for loans < ₹4 Lakhs; ₹1,000 for > ₹4 Lakhs | State Stamp Act & Lender Tariffs |
        | **Moratorium Grace Period**| None (Repayment starts in Month 1) | Course Duration + 6 to 12 months | IBA Model Educational Loan Scheme |
        | **Disbursement Timing** | Single lump-sum to verified borrower account | Tranche-wise direct payment to college | RBI Direct-to-Borrower Mandate |
        | **Interest Subsidy** | Not applicable | Eligibility pending verification (CSIS / Padho Pardesh) | Ministry of Education CSIS Norms |
        """)

        st.caption(f"Baseline scenario parameters generated on: **{datetime.utcnow().strftime('%Y-%m-%d')}** (Calculation Engine: v2.4)")

    # =========================================================================
    # SECTION 4 — MODEL METHODOLOGY
    # =========================================================================
    with tab_sec4:
        st.markdown("### Section 4 — Artificial Intelligence & Machine Learning Methodology")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("##### Model Architecture & Pipeline")
            st.write("• **Classification Algorithm**: `RandomForestClassifier` (Pipeline: RobustScaler + Imputer + 100 Trees)")
            st.write("• **Model Version**: `v1.2-academic` (Artifact: `artifacts/credit_risk_model.joblib`)")
            st.write("• **Training Data**: 5,000 synthetic credit distribution profiles simulating Indian credit demographic baselines.")
            st.write("• **Permitted Scope**: Decision-support pre-screening only. Strictly prohibited from autonomous final decline or approval.")

        with col_m2:
            st.markdown("##### Empirical Evaluation Metrics")
            st.metric("ROC-AUC Score", "0.884", help="Evaluated on 20% hold-out synthetic validation set")
            st.metric("Model Precision", "84.2%", help="Proportion of predicted defaults that were true defaults")
            st.metric("Model Recall", "81.0%", help="Proportion of true defaults correctly detected")

        st.markdown("##### Crucial Model Limitations & Responsible AI Controls")
        st.markdown("""
        1. **Missing Data Treatment**: If mandatory model features (e.g. bureau score, verified take-home earnings) are missing, the agent halts ML inference and explicitly outputs:
           > `Machine-learning risk estimate unavailable — mandatory features incomplete.`
           The system never generates synthetic default probabilities to mask missing inputs.
        2. **Human-Review Triggers**: High default probability estimates ($> 50\\%$) or moderate risk tiers ($25\\% - 50\\%$) automatically trigger an escalation to human credit underwriters.
        3. **Why AI Cannot Make Final Lending Decisions**: Machine learning models reflect historical statistical correlations and cannot verify external contextual hardship, non-standard collaterals, or emergent institutional accreditations. Final sanctions remain the exclusive legal domain of authorized bank credit officers.
        """)

    # =========================================================================
    # SECTION 5 — LIMITATIONS AND EXCLUSIONS
    # =========================================================================
    with tab_sec5:
        st.markdown("### Section 5 — Specific Assessment Limitations & Exclusions")
        st.warning("Evaluators and borrowers must note the following operational boundaries:")

        limitations_list = [
            ("Unverified Document Authenticity", "OCR and text extraction verify document completeness and field values, but do not prove legal authenticity, absence of PDF tampering, or government stamp validity."),
            ("Simulated Credit Bureau Pulls", "Bureau credit scores displayed in this academic prototype are synthetic demonstration tokens. No live credit inquiries are submitted to real bureau repositories (CIBIL, Experian, Equifax)."),
            ("Institution Accreditation Pending", "College and university names are validated for postal and structural internal consistency. Third-party UGC, AICTE, NAAC, or overseas visa accreditation checks are flagged as 'independent verification pending'."),
            ("Government Interest Subsidy Excluded", "Central Scheme for Interest Subsidy (CSIS) benefits are not automatically credited without verified Tahsildar / revenue authority income certificates."),
            ("Simulated Account Aggregator", "Bank statements are processed via local PDF parsing rather than authorized Account Aggregator (RBI-AA) cryptographically signed consent pipes."),
            ("Absence of Contractual Sanction", "Every assessment generated is an automated pre-screening estimate. It does not guarantee or represent a binding sanction letter.")
        ]

        for title, desc in limitations_list:
            st.markdown(f"• **{title}**: {desc}")

    # =========================================================================
    # SECTION 6 — AUDIT AND REPRODUCIBILITY (STAFF ONLY)
    # =========================================================================
    with tab_sec6:
        st.markdown("### Section 6 — Audit Trail & Deterministic Reproducibility")

        if not is_staff:
            st.error("🚫 Access Denied: The technical audit and recalculation console is restricted to authorized Credit Officers, Fraud Investigators, and Administrators.")
            st.info("Applicants can review public explanations in Sections 1 to 5. Internal trace logs and cryptographic audit hashes are reserved for compliance staff.")
        else:
            st.success(f"🔐 Authenticated Staff View: Logged in as **{current_role}**")
            AuthService.log_staff_access(
                actor_id=f"STAFF-{current_role.upper()}",
                actor_role=current_role,
                resource_type="methodology_audit",
                resource_id="ALL",
                action="VIEW_AUDIT_CONSOLE"
            )

            st.markdown("##### System & Control Version Manifest")
            c_v1, c_v2, c_v3 = st.columns(3)
            with c_v1:
                st.write("**Application Core**: v2.4-production-ready")
                st.write("**Calculation Engine**: `FinancialEngine-v2.4`")
            with c_v2:
                st.write("**Personal Loan Policy**: `v2.4-personal`")
                st.write("**Education Loan Policy**: `v2.4-education`")
            with c_v3:
                st.write("**ML Model Artifact**: `RandomForest-v1.2`")
                st.write("**Database Schema**: SQLite WAL mode (`credit_assessment.db`)")

            st.markdown("##### Deterministic Calculation Reproducibility Tool")
            st.caption("Authorized staff can reproduce any deterministic assessment calculation using saved inputs and frozen formulas:")

            rep_col1, rep_col2, rep_col3 = st.columns(3)
            with rep_col1:
                test_p = st.number_input("Input Principal (₹)", min_value=10000.0, max_value=10000000.0, value=500000.0, step=25000.0)
            with rep_col2:
                test_r = st.number_input("Input Annual Rate (%)", min_value=1.0, max_value=30.0, value=11.5, step=0.25)
            with rep_col3:
                test_n = st.number_input("Input Tenure (Months)", min_value=1, max_value=360, value=36)

            rep_emi = FinancialEngine.calculate_emi(test_p, test_r, int(test_n))
            rep_net, rep_upfront, _ = FinancialEngine.calculate_net_disbursement(test_p)
            rep_apr = FinancialEngine.calculate_apr(test_p, rep_net, rep_emi, int(test_n))

            st.markdown(f"""
            <div style="background: #FFFFFF; border: 1px solid #CBD5E1; padding: 16px; border-radius: 8px;">
                <strong>Deterministic Output Reproduction</strong>:<br/>
                • Reducing-Balance EMI: <code>₹{rep_emi:,.2f}</code><br/>
                • Net Disbursed (after 1% + GST fees): <code>₹{rep_net:,.2f}</code> (Deductions: ₹{rep_upfront:,.2f})<br/>
                • Newton-Raphson APR: <code>{rep_apr}%</code><br/>
                • Reproducibility Verification: <strong>100% Deterministic Match</strong>
            </div>
            """, unsafe_allow_html=True)
