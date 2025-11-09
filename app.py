# app.py - COMPLETE VERSION
import pandas as pd
import streamlit as st
import base64

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Tenancy Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import after page config
from src.chat import ask

# ========== BERTSCORE HELPER ==========
try:
    from bert_score import score as bertscore_score
except Exception:
    bertscore_score = None

def compute_bertscore(preds, refs, lang="en", rescale_with_baseline=False):
    if bertscore_score is None:
        raise ImportError("bert-score is not installed. Run: pip install bert-score")
    P, R, F1 = bertscore_score(preds, refs, lang=lang, rescale_with_baseline=rescale_with_baseline)
    return {
        "precision": float(P.mean().item()),
        "recall": float(R.mean().item()),
        "f1": float(F1.mean().item()),
    }

# ========== PDF VIEWER ==========
def create_pdf_viewer(pdf_path, page_number):
    """
    Create embedded PDF viewer

    Args:
        pdf_path: Path to PDF file
        page_number: 0-based page number from metadata (0 = first page)

    Note:
        - We show users "Page X+1" (human-readable)
        - But jump to "page=X+1" in PDF viewer (which also uses 1-based)
    """
    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            base64_pdf = base64.b64encode(pdf_data).decode('utf-8')

        # PDF viewer page is 1-based; metadata is 0-based
        viewer_page = int(page_number) + 1

        pdf_viewer_html = f'''
        <div style="margin-top:1rem; position:relative;">
            <embed
                src="data:application/pdf;base64,{base64_pdf}#page={viewer_page}"
                type="application/pdf"
                width="100%"
                height="700px"
                style="border: 3px solid #667eea; border-radius: 8px; box-shadow: 0 4px 12px rgba(102,126,234,0.2);"
            />
            <div style="position:absolute; top:10px; right:10px; background:rgba(102,126,234,0.9); color:white; padding:8px 16px; border-radius:6px; font-weight:600;">
                📄 Page {viewer_page}
            </div>
        </div>
        '''
        return pdf_viewer_html

    except FileNotFoundError:
        return f'<div style="color:#dc3545; padding:1rem; background:#fff5f5; border-radius:6px;">❌ PDF file not found at {pdf_path}</div>'
    except Exception as e:
        return f'<div style="color:#dc3545; padding:1rem; background:#fff5f5; border-radius:6px;">❌ Failed to load PDF: {str(e)}</div>'

# ========== CONSTANTS ==========
WHATSAPP_NUMBER = "6593537789"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"

# Import FAQ
try:
    from FAQ_DATA import FAQ_ITEMS
except ImportError:
    FAQ_ITEMS = {}
    st.error("FAQ_DATA.py not found.")

# ========== CUSTOM CSS ==========
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .header-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
    }

    .header-box h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 600;
    }

    .header-box p {
        color: rgba(255,255,255,0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }

    .user-msg {
        background: #e3f2fd;
        padding: 0.75rem 1rem;
        border-radius: 16px 16px 2px 16px;
        margin: 0.5rem 0;
        max-width: 70%;
        margin-left: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.08);
        color: #1a1a1a;
    }

    .assistant-msg {
        background: white;
        padding: 1rem 1.25rem;
        border-radius: 16px 16px 16px 2px;
        margin: 0.5rem 0;
        max-width: 75%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 3px solid #667eea;
        color: #2c3e50;
        line-height: 1.6;
    }

    .conf-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .conf-high {
        background: #d4edda;
        color: #155724;
    }

    .conf-medium {
        background: #fff3cd;
        color: #856404;
    }

    .conf-low {
        background: #f8d7da;
        color: #721c24;
    }

    .conf-accuracy {
        background: #e0f0ff;
        color: #0d6efd;
        border: 1px solid #b6daff;
        border-radius: 12px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton button {
        width: 100%;
        text-align: left;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        background: white;
        transition: all 0.2s ease;
        padding: 0.5rem 1rem;
        color: #2c3e50;
    }

    .stButton button:hover {
        border-color: #667eea;
        background-color: #f8f9fa;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }

    .streamlit-expanderHeader {
        font-weight: 600;
        color: #2c3e50;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if "messages" not in st.session_state:
    st.session_state.messages = []

if "show_modal" not in st.session_state:
    st.session_state.show_modal = False

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### Tenancy Assistant")
    st.caption("AI-powered contract assistance")
    st.markdown("---")

    st.markdown("### Frequently Asked Questions")
    st.caption("Click any question to ask instantly")

    if FAQ_ITEMS:
        for category, questions in FAQ_ITEMS.items():
            with st.expander(f"**{category}**", expanded=False):
                for q in questions:
                    if st.button(q, key=f"faq_{category}_{q}"):
                        st.session_state.show_modal = False
                        res = ask(q)
                        st.session_state.messages.append({
                            "role": "user",
                            "content": q
                        })
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": res
                        })
                        st.rerun()

    st.markdown("---")

    st.markdown("### Need Human Assistance?")
    st.caption("Our team handles complex tenancy matters")

    if st.button("Contact Support Team", use_container_width=True, type="primary"):
        st.session_state.show_modal = True
        st.rerun()

    st.markdown("---")

    with st.expander("How It Works"):
        st.markdown("""
        **1. Ask Questions**  
        Type any query about your tenancy

        **2. AI Search**  
        System searches your agreement

        **3. Get Answers**  
        Receive accurate answers with references

        **4. Escalate if Needed**  
        Contact support for complex matters
        """)

# ========== MAIN HEADER ==========
st.markdown("""
<div class="header-box">
    <h1>Tenancy Agreement Assistant</h1>
    <p>Ask questions about your tenancy agreement and get instant, accurate answers based on your contract.</p>
</div>
""", unsafe_allow_html=True)

# ========== CHAT DISPLAY ==========
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown(
            f'<div style="display:flex;justify-content:flex-end;margin:0.75rem 0;">'
            f'<div class="user-msg">{msg["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        content = msg["content"]

        # Parse response
        if isinstance(content, dict):
            answer = content.get("answer", "")
            reference = content.get("reference")
            show_cta = content.get("show_cta", False)
            confidence = content.get("confidence", "Unknown")
            confidence_score = content.get("score", None)   # optional numeric score 0..1
        else:
            answer = str(content)
            reference = None
            show_cta = False
            confidence = "Unknown"
            confidence_score = None

        # Map confidence to CSS class
        conf_class = f"conf-{confidence.lower()}" if confidence.lower() in ["high", "medium", "low"] else "conf-medium"

        # Prepare accuracy text (not strictly needed in UI, kept for completeness)
        if confidence_score is not None:
            percent = int(round(confidence_score * 100))
            acc_text = f"Accuracy: {percent}%"
        else:
            acc_text = "Accuracy: N/A"

        # Render assistant message
        st.markdown(
            f"""
            <div style="display:flex;justify-content:flex-start;margin:0.75rem 0;">
                <div class="assistant-msg">
                    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px;">
                        <span class="conf-badge {conf_class}">Confidence: {confidence}</span>
                        <span class="conf-badge conf-accuracy">Confidence Accuracy: {int(round(confidence_score * 100)) if confidence_score is not None else 'N/A'}%</span>
                    </div>
                    {answer}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # --- Reference viewer (added in the correct scope) ---
        if reference and isinstance(reference, dict):
            ref_text = reference.get("text", "")
            ref_page = reference.get("page", "?")

            # Convert 0-based -> 1-based for display
            display_page = int(ref_page) + 1 if str(ref_page).isdigit() else ref_page

            with st.expander("📄 View Contract Reference", expanded=False):
                # Header
                st.markdown(
                    f'''
                    <div style="background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color:white; padding:1rem 1.25rem; border-radius:8px; margin-bottom:1rem;
                                box-shadow:0 2px 8px rgba(102,126,234,0.3);">
                        <div style="font-size:1.05rem; font-weight:600;">📍 Contract Source</div>
                        <div style="margin-top:0.5rem; opacity:0.95; font-size:0.95rem;">
                            Page {display_page} | Tenancy Agreement
                        </div>
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

                # Clause text
                st.markdown(
                    f'''
                    <div style="background:#f8f9fa; padding:1.5rem; border-left:4px solid #667eea;
                                border-radius:6px; line-height:1.8; color:#2c3e50; font-size:0.95rem;
                                box-shadow:0 1px 3px rgba(0,0,0,0.08); margin-bottom:1rem;">
                        <div style="color:#667eea; font-weight:600; margin-bottom:0.75rem; font-size:0.9rem;">
                            📋 RELEVANT CLAUSE:
                        </div>
                        {ref_text}
                    </div>
                    ''',
                    unsafe_allow_html=True
                )

                st.caption("💡 Want to verify? View this clause in the original contract document.")

                view_pdf_btn = st.button(
                    f"📖 View Original PDF (Page {display_page})",
                    key=f"view_pdf_btn_{i}",
                    use_container_width=True,
                    type="primary"
                )

                if view_pdf_btn:
                    st.markdown("---")
                    st.markdown(
                        f'''
                        <div style="background:#e7f3ff; padding:0.75rem 1rem; border-radius:6px;
                                    border-left:4px solid #0066cc; margin:1rem 0;">
                            <strong style="color:#0066cc;">📖 Viewing Original Contract</strong><br>
                            <span style="font-size:0.9rem;">Loading Page {display_page} of tenancy_agreement.pdf</span>
                        </div>
                        ''',
                        unsafe_allow_html=True
                    )
                    with st.spinner("Loading PDF document..."):
                        # Only call viewer if we have a numeric page
                        page_for_viewer = int(ref_page) if str(ref_page).isdigit() else 0
                        pdf_html = create_pdf_viewer("./data/tenancy_agreement.pdf", page_for_viewer)
                        st.markdown(pdf_html, unsafe_allow_html=True)
                    st.success("PDF loaded successfully")

# ========== CHAT INPUT ==========
st.markdown("---")
user_input = st.chat_input("Ask a question about your tenancy agreement...")

if user_input:
    st.session_state.show_modal = False
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Searching your agreement..."):
        res = ask(user_input)

    st.session_state.messages.append({"role": "assistant", "content": res})
    st.rerun()

# ========== SUPPORT MODAL ==========
if st.session_state.get("show_modal", False):
    st.markdown("---")
    st.markdown("""
    ### 🤝 Connect with Support Team

    Our AI assistant is trained on your tenancy agreement and can answer most questions instantly.

    **Human support is recommended for:**
    - Complex legal interpretation
    - Dispute resolution
    - Special requests to landlord
    - Urgent maintenance issues
    """)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Continue with AI", use_container_width=True, key="continue_ai"):
            st.session_state.show_modal = False
            st.rerun()

    with col2:
        st.link_button(
            "WhatsApp Support",
            WHATSAPP_URL,
            use_container_width=True,
            type="primary"
        )

# ========== BATCH VALIDATION (BERTScore only, always fast mode) ==========
st.markdown("---")

if "batch_eval" not in st.session_state:
    st.session_state.batch_eval = None

with st.expander("📊 Batch Validation (Upload Excel/CSV with questions + references)", expanded=False):
    st.write(
        "Upload a file with columns: **question** and **reference** (gold answer). "
        "Supported formats: `.xlsx`, `.xls`, `.csv`."
    )

    file = st.file_uploader(
        "Upload validation file",
        type=["xlsx", "xls", "csv"],
        key="eval_file"
    )
    limit = st.number_input(
        "Max examples to validate",
        min_value=1,
        max_value=5000,
        value=20,
        step=1
    )

    # Always fast mode (skip baseline rescale)
    fast_mode = True

    @st.cache_data(show_spinner=False, ttl=3600)
    def _cached_ask(q: str):
        out = ask(q)
        return out.get("answer", "") if isinstance(out, dict) else str(out)

    st.markdown(
        """
        <style>
            div[data-testid="stButton"] > button {
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left_col, spacer, right_col = st.columns([2, 4, 2])

    with left_col:
        run_clicked = st.button(
            "Run BERTScore Validation",
            type="primary",
            use_container_width=True,
            key="run_validation_btn",
        )

    with right_col:
        clear_clicked = st.button(
            "Clear Results",
            use_container_width=True,
            key="clear_results_btn",
        )

    # Clear stored validation
    if clear_clicked:
        st.session_state.batch_eval = None
        st.success("Cleared previous validation results.")

    # Run validation
    if run_clicked:
        if file is None:
            st.warning("Please upload a valid Excel or CSV file first.")
        else:
            try:
                name = file.name.lower()
                df = pd.read_excel(file) if name.endswith((".xlsx", ".xls")) else pd.read_csv(file)
                df.columns = [c.strip().lower() for c in df.columns]
            except Exception as e:
                st.error(f"Could not read file: {e}")
                df = None

            if df is not None and {"question", "reference"}.issubset(set(df.columns)):
                total = min(int(limit), len(df))
                rows = df.head(total).copy()
                st.success(f"Loaded {len(df)} rows. Validating top {total} ...")

                preds, refs = [], []
                progress = st.progress(0)
                status = st.empty()

                for i, row in rows.iterrows():
                    q = str(row["question"]).strip()
                    ref = str(row["reference"]).strip()
                    pred_text = _cached_ask(q)
                    preds.append(pred_text)
                    refs.append(ref)
                    progress.progress(min(len(preds) / total, 1.0))
                    status.write(f"Validated {len(preds)}/{total}")

                try:
                    bs = compute_bertscore(preds, refs, lang="en", rescale_with_baseline=False)
                    st.session_state.batch_eval = {
                        "rows_records": rows.to_dict("records"),
                        "preds": preds,
                        "refs": refs,
                        "bs": bs,
                    }
                    st.success("✅ Validation completed successfully.")
                except Exception as e:
                    st.error(f"BERTScore error: {e}")

            else:
                st.error("Your file must contain columns named exactly: 'question' and 'reference'")

# ===== Results Section (stays outside expander, appears after run) =====
if st.session_state.batch_eval is not None:
    data = st.session_state.batch_eval
    preds = data["preds"]
    bs = data["bs"]
    st.subheader("Overall Validation")
    st.json({"BERTScore (avg)": bs})

    f1 = float(bs.get("f1", 0.0))
    if f1 >= 0.90:
        st.success("Semantic match: Excellent (BERTScore F1 ≥ 0.90)")
    elif f1 >= 0.80:
        st.info("Semantic match: Very Good (0.80–0.90)")
    elif f1 >= 0.70:
        st.warning("Semantic match: Good (0.70–0.80)")
    else:
        st.error("Semantic match: Low (F1 < 0.70)")

    if st.checkbox("Show per-question results"):
        rows_df = pd.DataFrame.from_records(data["rows_records"])
        rows_df["prediction"] = preds
        st.dataframe(rows_df[["question", "reference", "prediction"]], use_container_width=True)

# ========== FOOTER ==========
st.markdown("---")
st.caption("💡 All answers are based on your actual tenancy agreement. Use the sidebar FAQ for common questions.")
