import pandas as pd
import streamlit as st
import base64
import os, json, hashlib, secrets, html, re, shutil, importlib  # + html, re, shutil, importlib

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Tenancy Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import after page config (import the MODULE so we can reload it later)
import src.chat as chat

# ========== BERTSCORE HELPER ==========
try:
    from bert_score import score as bertscore_score
except Exception:
    bertscore_score = None

def compute_bertscore(preds, refs, lang="en", rescale_with_baseline=False):
    if bertscore_score is None:
        raise ImportError("bert-score is not installed. Run: pip install bert-score")
    P, R, F1 = bertscore_score(preds, refs, lang=lang, rescale_with_baseline=rescale_with_baseline)
    return {"precision": float(P.mean().item()),
            "recall": float(R.mean().item()),
            "f1": float(F1.mean().item())}

# ========== PDF VIEWER ==========
def create_pdf_viewer(pdf_path, page_number):
    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        viewer_page = int(page_number) + 1
        return f'''
        <div style="margin-top:1rem; position:relative;">
            <embed src="data:application/pdf;base64,{base64_pdf}#page={viewer_page}"
                   type="application/pdf" width="100%" height="700px"
                   style="border:3px solid #667eea;border-radius:8px;box-shadow:0 4px 12px rgba(102,126,234,0.2);" />
            <div style="position:absolute; top:10px; right:10px; background:rgba(102,126,234,0.9); color:white;
                        padding:8px 16px; border-radius:6px; font-weight:600;">
                📄 Page {viewer_page}
            </div>
        </div>'''
    except FileNotFoundError:
        return f'<div style="color:#dc3545; padding:1rem; background:#fff5f5; border-radius:6px;">❌ PDF file not found at {pdf_path}</div>'
    except Exception as e:
        return f'<div style="color:#dc3545; padding:1rem; background:#fff5f5; border-radius:6px;">❌ Failed to load PDF: {str(e)}</div>'

# ========== CONSTANTS ==========
WHATSAPP_NUMBER = "6593537789"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
DEFAULT_PDF_PATH = "./data/tenancy_agreement.pdf"  # used by chat.ask internally

try:
    from FAQ_DATA import FAQ_ITEMS
except ImportError:
    FAQ_ITEMS = {}

# ========== CSS ==========
st.markdown("""
<style>
    .main { background-color:#f8f9fa; }
    .block-container { padding-top:2rem; padding-bottom:2rem; }
    .auth-card{max-width:520px;margin:6vh auto 2rem auto;background:#fff;padding:2rem;border-radius:12px;
        box-shadow:0 12px 36px rgba(0,0,0,0.08);border:1px solid #eef1f6;text-align:center;}
    .auth-card h2{margin:0 0 .5rem 0;font-size:1.6rem;font-weight:800;color:#0f1d40;}
    .auth-card p{margin:0;color:#64748b;font-size:.95rem;}
    .header-box{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:2.5rem 2rem;border-radius:12px;
        margin-bottom:2rem;box-shadow:0 4px 6px rgba(0,0,0,0.07);}
    .header-box h1{color:white;margin:0;font-size:2rem;font-weight:600;}
    .header-box p{color:rgba(255,255,255,0.9);margin:.5rem 0 0;font-size:1rem;}
    .user-msg{background:#e3f2fd;padding:.75rem 1rem;border-radius:16px 16px 2px 16px;margin:.5rem 0;max-width:70%;
        margin-left:auto;box-shadow:0 1px 2px rgba(0,0,0,0.08);color:#1a1a1a;}
    .assistant-msg{background:#fff;padding:1rem 1.25rem;border-radius:16px 16px 16px 2px;margin:.5rem 0;max-width:75%;
        box-shadow:0 2px 8px rgba(0,0,0,0.06);border-left:3px solid #667eea;color:#2c3e50;line-height:1.6;}
    .conf-badge{display:inline-block;padding:.25rem .75rem;border-radius:12px;font-size:.75rem;font-weight:600;
        margin-bottom:.5rem;text-transform:uppercase;letter-spacing:.5px;}
    .conf-high{background:#d4edda;color:#155724;} .conf-medium{background:#fff3cd;color:#856404;}
    .conf-low{background:#f8d7da;color:#721c24;}
    .conf-accuracy{background:#e0f0ff;color:#0d6efd;border:1px solid #b6daff;border-radius:12px;padding:.25rem .75rem;
        font-size:.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.5px;}

    /* Sidebar user card */
    .user-card{
        display:flex;align-items:center;gap:.75rem;
        padding:.75rem 1rem;margin:.5rem 0 1rem 0;
        background:#ffffff;border:1px solid #eef1f6;border-radius:12px;
        box-shadow:0 4px 14px rgba(15,29,64,.05);
    }
    .user-avatar{
        width:40px;height:40px;border-radius:50%;
        display:flex;align-items:center;justify-content:center;
        color:#fff;font-weight:700;letter-spacing:.25px;text-transform:uppercase;
        box-shadow:inset 0 0 0 2px rgba(255,255,255,.25);
    }
    .user-meta{line-height:1.2}
    .user-meta .label{
        font-size:.72rem;color:#6b7280;letter-spacing:.3px;text-transform:uppercase;
    }
    .user-meta .name{
        font-size:.95rem;font-weight:700;color:#0f1d40;margin-top:2px;
        max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
    }
</style>
""", unsafe_allow_html=True)

# ========== SESSION ==========
if "messages" not in st.session_state: st.session_state.messages = []
if "show_modal" not in st.session_state: st.session_state.show_modal = False
if "batch_eval" not in st.session_state: st.session_state.batch_eval = None

# Auth session
if "auth" not in st.session_state: st.session_state.auth = False
if "user" not in st.session_state: st.session_state.user = None
if "auth_active" not in st.session_state: st.session_state.auth_active = "login"
if "prefill_login_username" not in st.session_state: st.session_state.prefill_login_username = ""
if "last_logged_in_username" not in st.session_state: st.session_state.last_logged_in_username = ""
if "login_nonce" not in st.session_state: st.session_state.login_nonce = 0

# Track which PDF is currently active for viewing
if "active_pdf_path" not in st.session_state:
    st.session_state.active_pdf_path = DEFAULT_PDF_PATH

# ========== SIMPLE AUTH STORE ==========
USERS_FILE = "./data/users.json"

def _ensure_data_dir():
    os.makedirs(os.path.dirname(USERS_FILE) or ".", exist_ok=True)

def load_users():
    _ensure_data_dir()
    if not os.path.exists(USERS_FILE): return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(users: dict):
    _ensure_data_dir()
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def hash_password(password: str, salt: str = None):
    if salt is None:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 100_000)
    return salt, dk.hex()

def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    _, ph = hash_password(password, salt)
    return secrets.compare_digest(ph, stored_hash)

# ========== AUTH GATE ==========
def auth_gate():
    """Show sign-in card + tabs; stop app until authenticated."""
    if st.session_state.auth and st.session_state.user:
        return True

    st.markdown("""
    <div class="auth-card">
        <h2>🔒 Sign in to your account</h2>
        <p>Access your account to use the Tenancy Assistant.</p>
        <hr style="margin-top:1rem; border:none; border-top:1px solid #e7eef8;">
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth_active == "login":
        tab_login, tab_register = st.tabs(["Log in", "Register"])
    else:
        tab_register, tab_login = st.tabs(["Register", "Log in"])

    # LOGIN
    with tab_login:
        default_username = (
            st.session_state.prefill_login_username
            or st.session_state.last_logged_in_username
            or ""
        )
        login_user = st.text_input("Username", value=default_username,
                                   key=f"login_user_input_{st.session_state.login_nonce}")
        login_pass = st.text_input("Password", type="password",
                                   key=f"login_pass_input_{st.session_state.login_nonce}")

        if st.button("Log in", type="primary", use_container_width=True,
                     key=f"login_btn_{st.session_state.login_nonce}"):
            users = load_users()
            if login_user in users:
                salt_user = users[login_user]["salt"]
                pw_hash = users[login_user]["hash"]
                if verify_password(login_pass, salt_user, pw_hash):
                    st.session_state.auth = True
                    st.session_state.user = login_user
                    st.session_state.last_logged_in_username = login_user
                    st.session_state.prefill_login_username = login_user
                    st.success("Login successful. Redirecting...")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.error("Invalid username or password.")

    # REGISTER
    with tab_register:
        reg_user  = st.text_input("Choose a username", key="reg_user_input")
        reg_pass  = st.text_input("Choose a password", type="password", key="reg_pass_input")
        reg_pass2 = st.text_input("Confirm password", type="password", key="reg_pass2_input")

        if st.button("Create Account", use_container_width=True, key="register_btn"):
            if not reg_user or not reg_pass:
                st.warning("Please enter a username and password.")
            elif len(reg_pass) < 8:
                st.warning("Password must be at least 8 characters long.")
            elif reg_pass != reg_pass2:
                st.warning("Passwords do not match.")
            else:
                users = load_users()
                if reg_user in users:
                    st.error("This username already exists. Please choose another.")
                else:
                    salt_user, pw_hash = hash_password(reg_pass)
                    users[reg_user] = {"salt": salt_user, "hash": pw_hash}
                    save_users(users)
                    st.session_state.prefill_login_username = reg_user
                    st.session_state.login_nonce += 1
                    st.markdown("""
                    <div style="background:#d4edda;border:1px solid #c3e6cb;
                                padding:1rem 1.25rem;border-radius:8px;
                                color:#155724;font-weight:500;margin-top:1rem;">
                        ✅ Account created successfully. Please click the <b>Log in</b> tab above and sign in.
                    </div>
                    """, unsafe_allow_html=True)

    st.stop()

# ===== Gate (IMPORTANT: call before sidebar/UI) =====
auth_gate()

# ========== SIDEBAR (only after login) ==========
with st.sidebar:
    st.markdown("### Tenancy Assistant")
    st.caption("AI-powered contract assistance")

    # Username card
    _u_raw = st.session_state.user or ""
    _u = html.escape(_u_raw)
    _letters = re.findall(r"[A-Za-z]", _u_raw)
    _initials = ("".join(_letters[:2]) or _u_raw[:2] or "U").upper()
    _hue = int(hashlib.sha256(_u_raw.encode()).hexdigest(), 16) % 360
    _avatar_bg = f"hsl({_hue}, 70%, 45%)"

    st.markdown(
        f"""
        <div class="user-card">
            <div class="user-avatar" style="background:{_avatar_bg};">{_initials}</div>
            <div class="user-meta">
                <div class="label">Signed in</div>
                <div class="name">{_u}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ===== Upload & select active contract =====
    st.markdown("#### Your Contract File")
    uploaded = st.file_uploader("Upload agreement (PDF)", type=["pdf"], key="upload_contract")
    if uploaded is not None:
        os.makedirs("./data", exist_ok=True)
        temp_path = "./data/_uploaded_agreement.pdf"
        with open(temp_path, "wb") as f:
            f.write(uploaded.read())
        st.success(f"Uploaded: {uploaded.name}")

        use_now = st.button("Use this file for Q&A", use_container_width=True, key="use_uploaded_qna")
        if use_now:
            st.session_state.active_pdf_path = temp_path
            # Copy to the default path expected by chat.ask()
            try:
                shutil.copyfile(temp_path, DEFAULT_PDF_PATH)
            except Exception as e:
                st.warning(f"Could not set default contract path: {e}")

            # CRITICAL: reload retrieval module so it rebuilds on the new PDF
            importlib.reload(chat)

            # clear Streamlit caches that might hold old answers
            st.cache_data.clear()

            st.rerun()

    # Quick status + reset
    if st.session_state.active_pdf_path != DEFAULT_PDF_PATH:
        st.info("Using your uploaded agreement for Q&A.")
    else:
        st.caption("Using the default sample agreement.")

    # Renamed as requested
    if st.button("Reset", use_container_width=True, key="reset_pdf"):
        st.session_state.active_pdf_path = DEFAULT_PDF_PATH
        # reload chat to point back to the sample file
        importlib.reload(chat)
        st.cache_data.clear()
        st.rerun()

    if st.button("Logout", use_container_width=True, key="logout_btn"):
        st.session_state.auth = False
        st.session_state.user = None
        st.session_state.messages = []
        st.session_state.batch_eval = None
        st.session_state.show_modal = False
        st.rerun()

    st.markdown("---")
    st.markdown("### Frequently Asked Questions")
    st.caption("Click any question to ask instantly")
    if "show_modal" not in st.session_state:
        st.session_state.show_modal = False

    if FAQ_ITEMS:
        for category, questions in FAQ_ITEMS.items():
            with st.expander(f"**{category}**", expanded=False):
                for q in questions:
                    if st.button(q, key=f"faq_{category}_{q}"):
                        st.session_state.show_modal = False
                        res = chat.ask(q)
                        st.session_state.messages.append({"role": "user", "content": q})
                        st.session_state.messages.append({"role": "assistant", "content": res})
                        st.rerun()

    st.markdown("---")
    st.markdown("### Need Human Assistance?")
    st.caption("Our team handles complex tenancy matters")
    if st.button("Contact Support Team", use_container_width=True, type="primary", key="contact_support_btn"):
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
        if isinstance(content, dict):
            answer = content.get("answer", "")
            reference = content.get("reference")
            confidence = content.get("confidence", "Unknown")
            confidence_score = content.get("score", None)
        else:
            answer = str(content); reference=None; confidence="Unknown"; confidence_score=None

        conf_class = f"conf-{confidence.lower()}" if confidence.lower() in ["high","medium","low"] else "conf-medium"

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

        if reference and isinstance(reference, dict):
            ref_text = reference.get("text", "")
            ref_page = reference.get("page", "?")
            display_page = int(ref_page) + 1 if str(ref_page).isdigit() else ref_page
            with st.expander("📄 View Contract Reference", expanded=False):
                st.markdown(
                    f'''
                    <div style="background:linear-gradient(135deg,#667eea 0%, #764ba2 100%);
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
                            <span style="font-size:0.9rem;">Loading Page {display_page}</span>
                        </div>
                        ''', unsafe_allow_html=True
                    )
                    with st.spinner("Loading PDF document..."):
                        page_for_viewer = int(ref_page) if str(ref_page).isdigit() else 0
                        pdf_html = create_pdf_viewer(st.session_state.active_pdf_path, page_for_viewer)
                        st.markdown(pdf_html, unsafe_allow_html=True)
                    st.success("PDF loaded successfully")

# ========== CHAT INPUT ==========
st.markdown("---")
user_input = st.chat_input("Ask a question about your tenancy agreement...")
if user_input:
    st.session_state.show_modal = False
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Searching your agreement..."):
        res = chat.ask(user_input)  # call through module (supports reload)
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
        st.link_button("WhatsApp Support", WHATSAPP_URL, use_container_width=True, type="primary")

# ========== BATCH VALIDATION ==========
st.markdown("---")
if "batch_eval" not in st.session_state:
    st.session_state.batch_eval = None

def _file_sig(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return "no-file"

@st.cache_data(show_spinner=False, ttl=3600)
def _cached_ask(q: str, file_sig: str):
    out = chat.ask(q)
    return out.get("answer", "") if isinstance(out, dict) else str(out)

with st.expander("📊 Batch Validation (Upload Excel/CSV with questions + references)", expanded=False):
    st.write("Upload a file with columns: **question** and **reference** (gold answer). Supported: .xlsx, .xls, .csv.")
    file = st.file_uploader("Upload validation file", type=["xlsx", "xls", "csv"], key="eval_file")
    limit = st.number_input("Max examples to validate", min_value=1, max_value=5000, value=20, step=1)

    left_col, _, right_col = st.columns([2, 4, 2])
    with left_col:
        run_clicked = st.button("Run BERTScore Validation", type="primary", use_container_width=True, key="run_validation_btn")
    with right_col:
        clear_clicked = st.button("Clear Results", use_container_width=True, key="clear_results_btn")

    if clear_clicked:
        st.session_state.batch_eval = None
        st.success("Cleared previous validation results.")

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
                sig = _file_sig(st.session_state.active_pdf_path)

                for i, row in rows.iterrows():
                    q = str(row["question"]).strip()
                    ref = str(row["reference"]).strip()
                    pred_text = _cached_ask(q, sig)  # cache keyed to active file
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

# ===== Results Section =====
if st.session_state.batch_eval is not None:
    data = st.session_state.batch_eval
    preds = data["preds"]
    bs = data["bs"]
    st.subheader("Overall Validation")
    st.json({"BERTScore (avg)": bs})

    f1 = float(bs.get("f1", 0.0))
    if f1 >= 0.90: st.success("Semantic match: Excellent (BERTScore F1 ≥ 0.90)")
    elif f1 >= 0.80: st.info("Semantic match: Very Good (0.80–0.90)")
    elif f1 >= 0.70: st.warning("Semantic match: Good (0.70–0.80)")
    else: st.error("Semantic match: Low (F1 < 0.70)")

    if st.checkbox("Show per-question results"):
        rows_df = pd.DataFrame.from_records(data["rows_records"])
        rows_df["prediction"] = preds
        st.dataframe(rows_df[["question", "reference", "prediction"]], use_container_width=True)

# ========== FOOTER ==========
st.markdown("---")
st.caption("💡 All answers are based on your actual tenancy agreement. Use the sidebar FAQ for common questions.")
