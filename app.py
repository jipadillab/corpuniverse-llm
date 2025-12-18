import os
import json
import uuid
from typing import List, Dict, Any, Tuple
import streamlit as st

from config import APP_TITLE, OUTPUT_DIR, DOCS_DIR
from ocr.ocr_engine import ocr_image_bytes
from rag.ingest import build_vector_store
from rag.retriever import retrieve_context
from llm.groq_client import groq_chat
from analysis.learning_path import build_learning_path_payload
from analysis.mentor_recommender import recommend_mentors_payload
from analysis.roi_model import estimate_roi_and_growth
from viz.radar_skills import radar_chart
from viz.growth_plot import growth_line_plot
from viz.roi_plot import roi_indicator_plot
from viz.network_graph import skill_network_plot
from validation.schema_validation import validate_company_profile
from rag.ingest import extract_text_from_uploads

st.set_page_config(page_title=APP_TITLE, layout="wide")

# ---------- Utilities ----------
def ensure_dirs():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

def save_bytes_to_disk(file_bytes: bytes, filename: str) -> str:
    ensure_dirs()
    out_path = os.path.join(DOCS_DIR, filename)
    with open(out_path, "wb") as f:
        f.write(file_bytes)
    return out_path

def safe_get_secret(key: str) -> str:
    # Streamlit Cloud: st.secrets; Local: .streamlit/secrets.toml
    try:
        return st.secrets.get(key, "")
    except Exception:
        return ""

# ---------- UI ----------
st.title(APP_TITLE)
st.caption("Corporate University Diagnosis • RAG • OCR • Learning Paths • Mentors • ROI & Skills Analytics")

with st.sidebar:
    st.header("Configuration")
    secret_key = safe_get_secret("GROQ_API_KEY")
    groq_api_key = st.text_input(
        "Groq API Key",
        value=secret_key,
        type="password",
        help="Stored safely in .streamlit/secrets.toml on local or Streamlit Cloud Secrets."
    )
    model_name = st.text_input("Groq model", value="llama3-8b-8192")
    top_k = st.slider("RAG top-k chunks", 2, 10, 5)
    st.divider()
    st.subheader("Export")
    export_company_id = st.text_input("Company ID for export", value="C001")

st.divider()

colA, colB = st.columns([1.1, 0.9], gap="large")

with colA:
    st.subheader("1) Upload Company Documents (RAG sources)")
    docs = st.file_uploader(
        "Upload PDFs, DOCX, TXT, or images (PNG/JPG) for OCR",
        accept_multiple_files=True,
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]
    )

    st.subheader("2) Upload Diagnosis Document (Training needs / corporate university diagnosis)")
    diagnosis_doc = st.file_uploader(
        "Upload a diagnosis (PDF/DOCX/TXT/Image)",
        accept_multiple_files=False,
        type=["pdf", "docx", "txt", "png", "jpg", "jpeg"]
    )

    st.subheader("3) Optional: Company Profile (JSON)")
    st.caption("If you do not upload JSON, the app will infer information from documents.")
    company_profile_file = st.file_uploader(
        "Upload company_profile.json",
        accept_multiple_files=False,
        type=["json"]
    )

with colB:
    st.subheader("Mockup OCR (Requirement: read mockup image)")
    st.caption("Upload an image mockup and the app will OCR it (free).")
    mockup_image = st.file_uploader(
        "Upload mockup image (PNG/JPG)",
        accept_multiple_files=False,
        type=["png", "jpg", "jpeg"]
    )
    mockup_text = ""
    if mockup_image is not None:
        mockup_bytes = mockup_image.read()
        st.image(mockup_bytes, caption="Mockup Preview", use_container_width=True)
        mockup_text = ocr_image_bytes(mockup_bytes)
        with st.expander("OCR text extracted from mockup"):
            st.write(mockup_text if mockup_text.strip() else "(No text detected)")

st.divider()

run_btn = st.button("Run Diagnosis → Learning Path → Mentors → Analytics", type="primary", use_container_width=True)

if run_btn:
    if not groq_api_key:
        st.error("Groq API Key is required to run the LLM steps. Add it in the sidebar.")
        st.stop()

    ensure_dirs()

    # ---- Load company profile (if provided) ----
    company_profile: Dict[str, Any] = {}
    if company_profile_file is not None:
        try:
            company_profile = json.loads(company_profile_file.read().decode("utf-8"))
            validate_company_profile(company_profile)
        except Exception as e:
            st.error(f"Invalid company profile JSON: {e}")
            st.stop()

    # ---- Extract texts from uploaded documents ----
    all_files = []
    if docs:
        all_files.extend(docs)
    if diagnosis_doc is not None:
        all_files.append(diagnosis_doc)

    if not all_files:
        st.error("Please upload at least one document (company docs and/or diagnosis).")
        st.stop()

    st.info("Extracting text from documents (PDF/DOCX/TXT) + OCR for images...")
    extracted_texts, doc_meta = extract_text_from_uploads(all_files)

    if not extracted_texts or all(len(t.strip()) == 0 for t in extracted_texts):
        st.error("No text could be extracted. Please upload readable PDFs/DOCX/TXT or clear images for OCR.")
        st.stop()

    st.success(f"Extracted text from {len(extracted_texts)} document(s). Building RAG index...")

    # ---- Build vector store ----
    index, chunks, embedder = build_vector_store(extracted_texts)

    # ---- Create a combined query ----
    inferred_context_query = (
        "Extract company mission, vision, strategy, and identify training needs. "
        "Return skill gaps and required competencies aligned with corporate university outcomes."
    )

    # Add company profile fields to the query if available
    if company_profile:
        inferred_context_query += "\nCompany profile JSON:\n" + json.dumps(company_profile, ensure_ascii=False)

    # ---- Retrieve context from RAG ----
    context_chunks = retrieve_context(
        query=inferred_context_query,
        index=index,
        chunks=chunks,
        embedder=embedder,
        top_k=top_k
    )

    rag_context = "\n\n".join([f"- {c}" for c in context_chunks])

    # ---- LLM: Diagnosis + Skill gaps (structured JSON) ----
    st.info("Calling Groq LLM for diagnosis and skill gaps...")
    diagnosis_prompt = f"""
You are a Corporate University expert and talent strategist.

Using ONLY the provided context, produce a JSON object with:
- company_summary: short text
- mission: string (if unknown, infer carefully)
- vision: string (if unknown, infer carefully)
- strategy: list of strategy pillars
- skill_gaps: list of objects: {{skill, current_level_0_100, target_level_0_100, priority('Critical'|'High'|'Medium'|'Low'), role_impact}}
- training_needs: list of key needs
- assumptions: list of assumptions you made

CONTEXT:
{rag_context}

Return ONLY valid JSON. No extra text.
"""
    diagnosis_json_text = groq_chat(
        api_key=groq_api_key,
        model=model_name,
        user_prompt=diagnosis_prompt,
        temperature=0.2,
        max_tokens=1500,
    )

    # Parse JSON safely
    try:
        diagnosis_payload = json.loads(diagnosis_json_text)
    except Exception:
        st.error("LLM did not return valid JSON. Below is the raw output for debugging:")
        st.code(diagnosis_json_text)
        st.stop()

    # ---- Learning path + mentors ----
    st.info("Generating learning path and mentor recommendations...")
    learning_path = build_learning_path_payload(diagnosis_payload)
    mentor_plan = recommend_mentors_payload(diagnosis_payload)

    # ---- ROI + Growth simulation ----
    roi_payload, growth_payload = estimate_roi_and_growth(diagnosis_payload)

    # ---- Export skills CSV (Req. 11) ----
    from analysis.learning_path import export_skills_csv
    csv_path = export_skills_csv(
        company_id=export_company_id,
        diagnosis_payload=diagnosis_payload,
        output_dir=OUTPUT_DIR
    )

    # ---- Save report JSON ----
    report = {
        "run_id": str(uuid.uuid4()),
        "company_id": export_company_id,
        "diagnosis": diagnosis_payload,
        "learning_path": learning_path,
        "mentors": mentor_plan,
        "roi": roi_payload,
        "growth": growth_payload,
        "rag_top_k": top_k
    }

    report_path = os.path.join(OUTPUT_DIR, "last_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # ---------- Results UI ----------
    st.success("Completed. Results are shown below.")

    tab1, tab2, tab3, tab4 = st.tabs(["Diagnosis", "Learning Path", "Mentors", "Analytics"])

    with tab1:
        st.subheader("Company Diagnosis (LLM + RAG)")
        st.json(diagnosis_payload)

    with tab2:
        st.subheader("Recommended Corporate Learning Path")
        st.json(learning_path)

    with tab3:
        st.subheader("Mentors / Teachers / Coaches")
        st.json(mentor_plan)

    with tab4:
        st.subheader("ROI Impact • Skill Growth • Skill Radar • Network Graph")

        # ROI
        st.plotly_chart(roi_indicator_plot(roi_payload), use_container_width=True)

        # Growth
        st.plotly_chart(growth_line_plot(growth_payload), use_container_width=True)

        # Radar
        radar_data = {
            s["skill"]: s["target_level_0_100"]
            for s in diagnosis_payload.get("skill_gaps", [])[:8]  # top 8 for readability
        }
        if radar_data:
            st.plotly_chart(radar_chart(radar_data), use_container_width=True)
        else:
            st.warning("No skill gaps detected to build the radar chart.")

        # Network
        st.plotly_chart(skill_network_plot(diagnosis_payload, mentor_plan), use_container_width=True)

    # Downloads
    st.divider()
    st.subheader("Downloads")
    with open(csv_path, "rb") as f:
        st.download_button("Download skills_database.csv", f, file_name="skills_database.csv", mime="text/csv")

    with open(report_path, "rb") as f:
        st.download_button("Download last_report.json", f, file_name="last_report.json", mime="application/json")

