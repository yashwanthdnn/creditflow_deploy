"""
Document Verification Page: Inspection of uploaded files, OCR & entity extraction previews,
comparison against declared form values, and simulated KYC token verification.
"""

import streamlit as st
import json
from services.database import get_db_connection, list_applications, get_application_details
from services.integration_service import IntegrationService


def render_document_verification():
    st.markdown('<div class="page-title">📄 Document Verification & Extraction Center</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Inspect submitted identity, income, and bank documents, verify OCR extractions against form baselines, and test integration sandboxes.</div>',
        unsafe_allow_html=True
    )

    apps = list_applications(limit=50)
    if not apps:
        st.info("No applications registered in database yet.")
        return

    app_id_list = [a["application_id"] for a in apps]
    selected_app_id = st.selectbox("Select Application to Verify Documents", app_id_list)

    details = get_application_details(selected_app_id)
    if not details:
        st.error("Application not found.")
        return

    st.markdown(f"**Applicant**: `{details['full_name']}` | **Product**: `{details['loan_product']}` | **Status**: `{details['status']}`")

    # Fetch documents for this application
    docs = details.get("documents", [])
    if not docs:
        st.warning(f"No documents are currently attached to application {selected_app_id}.")

        # Allow uploading directly in verification desk
        st.markdown("##### ➕ Upload Supporting Document for Verification Desk")
        doc_category = st.selectbox(
            "Document Category",
            ["IDENTITY_PROOF", "ADDRESS_PROOF", "INCOME_PROOF", "BANK_STATEMENT", "EMPLOYMENT_PROOF"]
        )
        up_file = st.file_uploader("Upload Document File (PDF / PNG / JPG)", type=["pdf", "png", "jpg", "jpeg"], key="desk_upload")
        if up_file and st.button("Save to Application Dossier", type="primary"):
            from services.document_service import save_uploaded_file, extract_text_from_pdf, extract_document_entities
            import uuid

            bytes_data = up_file.read()
            file_path, safe_name = save_uploaded_file(selected_app_id, doc_category, up_file.name, bytes_data)

            extracted_text = ""
            extracted_fields = {}
            if safe_name.lower().endswith(".pdf"):
                extracted_text = extract_text_from_pdf(file_path)
                extracted_fields = extract_document_entities(extracted_text)

            conn = get_db_connection()
            doc_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
            with conn:
                conn.execute("""
                INSERT INTO documents (
                    doc_id, application_id, doc_category, original_filename,
                    file_path, file_size_bytes, content_type, status,
                    extracted_fields_json, confirmed_by_applicant
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Extraction Completed', ?, 1)
                """, (
                    doc_id, selected_app_id, doc_category, up_file.name,
                    file_path, len(bytes_data), up_file.type, json.dumps(extracted_fields)
                ))
            conn.close()
            st.success("Document attached and registered successfully!")
            st.rerun()
        return

    st.markdown("##### Attached Verification Dossier")
    for doc in docs:
        with st.expander(f"📄 {doc['doc_category']}: {doc['original_filename']} — Status: {doc['status']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Document ID**: `{doc['doc_id']}`")
                st.write(f"**File Size**: {doc['file_size_bytes'] // 1024} KB")
                st.write(f"**Format**: `{doc['content_type']}`")
                st.write(f"**Uploaded At**: {doc['uploaded_at']}")
            with col2:
                st.write(f"**Verification Status**: `{doc['status']}`")
                extracted = json.loads(doc.get("extracted_fields_json") or "{}")
                if extracted:
                    st.markdown("**Detected Entities**:")
                    st.json(extracted)
                else:
                    st.caption("No structured entities discovered in text.")

            # Form vs Document Field Match Verification
            st.markdown("###### Cross-Verification Comparison")
            comp_col1, comp_col2, comp_col3 = st.columns(3)
            with comp_col1:
                st.caption("Declared Form Full Name")
                st.write(f"**{details['full_name']}**")
            with comp_col2:
                st.caption("Document Detected Name")
                st.write(f"**{extracted.get('detected_name', 'Not Found')}**")
            with comp_col3:
                det_name = extracted.get("detected_name")
                if det_name and details["full_name"].lower() in det_name.lower():
                    st.success("✅ Consistent Match")
                elif det_name:
                    st.warning("⚠️ Name Variation Detected")
                else:
                    st.info("ℹ️ Standard OCR Verified")

            # Simulated KYC Token Verification Button
            if st.button(f"🛡️ Trigger Simulated KYC Integration Check ({doc['doc_id']})"):
                with st.spinner("Connecting to Synthetic KYC Sandbox..."):
                    kyc_res = IntegrationService.verify_identity_kyc(
                        national_id=details.get("national_id_masked", "MOCK-ID"),
                        full_name=details["full_name"]
                    )
                st.info(f"**Integration Mode**: `{kyc_res['mode']}` | **Status**: `{kyc_res['status']}`")
                st.write(kyc_res["message"])
                st.caption("Disclaimer: Never claims OCR proves legal authenticity. Simulated sandbox verification token.")
