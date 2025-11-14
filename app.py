import pandas as pd
import streamlit as st
import base64
import os, json, hashlib, secrets, html, re, shutil, importlib

# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Tenancy Assistant",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import after page config
import src.chat as chat

# ========== PDF VIEWER ==========
def create_pdf_viewer(pdf_path, page_number):
    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            base64_pdf = base64.b64encode(pdf_data).decode('utf-8')
        viewer_page = int(page_number) + 1
        return f'''
        <div style="margin-top:1.5rem; position:relative; width:100%; height:800px;">
            <iframe 
                src="data:application/pdf;base64,{base64_pdf}#page={viewer_page}&zoom=100&toolbar=1&navpanes=1&scrollbar=1"
                type="application/pdf" 
                width="100%" 
                height="100%"
                style="border:2px solid rgba(59,130,246,0.3); border-radius:16px; box-shadow:0 8px 24px rgba(0,0,0,0.08);">
            </iframe>
            <div style="position:absolute; top:16px; right:16px; 
                        background:linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                        color:white; padding:10px 20px; border-radius:10px; 
                        font-weight:600; font-size:0.9rem;
                        box-shadow:0 4px 12px rgba(59,130,246,0.3);
                        z-index:10;">
                📄 Page {viewer_page}
            </div>
        </div>'''
    except FileNotFoundError:
        return f'<div style="color:#dc2626; padding:1.5rem; background:#fef2f2; border-radius:12px; border:1px solid #fecaca;">❌ PDF file not found</div>'
    except Exception as e:
        return f'<div style="color:#dc2626; padding:1.5rem; background:#fef2f2; border-radius:12px; border:1px solid #fecaca;">❌ Failed to load PDF: {str(e)}</div>'

# ========== CONSTANTS ==========
WHATSAPP_NUMBER = "6593537789"
WHATSAPP_URL = f"https://wa.me/{WHATSAPP_NUMBER}"
DEFAULT_PDF_PATH = "./data/tenancy_agreement.pdf"

try:
    from FAQ_DATA import FAQ_ITEMS
except ImportError:
    FAQ_ITEMS = {}

# ========== MODERN CSS ==========
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    .main {
        background: linear-gradient(to bottom, #fafbfc 0%, #f5f7fa 100%);
    }
    
    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 900px;
    }
    
    .auth-card {
        max-width: 440px;
        margin: 8vh auto 2rem auto;
        background: #ffffff;
        padding: 2.5rem;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04), 0 16px 48px rgba(0, 0, 0, 0.08);
        border: 1px solid rgba(0, 0, 0, 0.06);
        text-align: center;
    }
    
    .auth-card h2 {
        margin: 0 0 0.75rem 0;
        font-size: 1.75rem;
        font-weight: 600;
        color: #1a1a1a;
        letter-spacing: -0.02em;
    }
    
    .auth-card p {
        margin: 0;
        color: #6b6b6b;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    
    .header-box {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        padding: 3rem 2.5rem;
        border-radius: 20px;
        margin-bottom: 2.5rem;
        box-shadow: 0 4px 16px rgba(59, 130, 246, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .header-box h1 {
        color: white;
        margin: 0;
        font-size: 2.25rem;
        font-weight: 600;
        letter-spacing: -0.03em;
    }
    
    .header-box p {
        color: rgba(255, 255, 255, 0.95);
        margin: 0.75rem 0 0;
        font-size: 1.05rem;
        line-height: 1.6;
        font-weight: 400;
    }
    
    .user-msg {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        padding: 1rem 1.25rem;
        border-radius: 20px 20px 4px 20px;
        margin: 0.75rem 0;
        max-width: 65%;
        margin-left: auto;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
        font-size: 0.95rem;
        line-height: 1.6;
        font-weight: 400;
    }
    
    .assistant-msg {
        background: #ffffff;
        padding: 1.25rem 1.5rem;
        border-radius: 20px 20px 20px 4px;
        margin: 0.75rem 0;
        max-width: 75%;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.06);
        border: 1px solid rgba(0, 0, 0, 0.06);
        color: #2b2b2b;
        line-height: 1.7;
        font-size: 0.95rem;
    }
    
    .conf-badge {
        display: inline-block;
        padding: 0.35rem 0.85rem;
        border-radius: 8px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .conf-high {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
    }
    
    .conf-low {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        box-shadow: 0 2px 4px rgba(245, 158, 11, 0.2);
    }
    
    .conf-accuracy {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white;
        border: none;
        box-shadow: 0 2px 4px rgba(59, 130, 246, 0.2);
    }
    
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid rgba(0, 0, 0, 0.06);
    }
    
    section[data-testid="stSidebar"] > div {
        background: #ffffff;
    }
    
    .user-card {
        display: flex;
        align-items: center;
        gap: 0.85rem;
        padding: 0.85rem 1.1rem;
        margin: 0.5rem 0 1.5rem 0;
        background: linear-gradient(135deg, #f8f9fa 0%, #f1f3f5 100%);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    .user-avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #fff;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
    }
    
    .user-meta {
        line-height: 1.3;
        flex: 1;
    }
    
    .user-meta .label {
        font-size: 0.7rem;
        color: #8b8b8b;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .user-meta .name {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1a1a1a;
        margin-top: 3px;
        max-width: 180px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    .stButton > button {
        border-radius: 10px;
        font-weight: 500;
        border: 1px solid rgba(0, 0, 0, 0.08);
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .streamlit-expanderHeader {
        background: #ffffff;
        border-radius: 12px;
        border: 1px solid rgba(0, 0, 0, 0.06);
        font-weight: 500;
    }
    
    .stChatInput > div {
        border-radius: 16px;
        border: 2px solid rgba(0, 0, 0, 0.08);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    
    .stChatInput > div:focus-within {
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.15);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 0, 0, 0.25);
    }
    
    h1, h2, h3, h4, h5, h6 {
        letter-spacing: -0.02em;
        font-weight: 600;
    }
    
    .stMarkdown {
        color: #2b2b2b;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
if "messages" not in st.session_state: st.session_state.messages = []
if "show_modal" not in st.session_state: st.session_state.show_modal = False
if "batch_eval" not in st.session_state: st.session_state.batch_eval = None
if "auth" not in st.session_state: st.session_state.auth = False
if "user" not in st.session_state: st.session_state.user = None
if "auth_active" not in st.session_state: st.session_state.auth_active = "login"
if "prefill_login_username" not in st.session_state: st.session_state.prefill_login_username = ""
if "last_logged_in_username" not in st.session_state: st.session_state.last_logged_in_username = ""
if "login_nonce" not in st.session_state: st.session_state.login_nonce = 0
if "active_pdf_path" not in st.session_state: st.session_state.active_pdf_path = DEFAULT_PDF_PATH

# ========== AUTH ==========
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

def auth_gate():
    if st.session_state.auth and st.session_state.user:
        return True

    st.markdown("""
    <div class="auth-card">
        <h2>🏠 Welcome Back</h2>
        <p>Sign in to access your Tenancy Assistant</p>
        <hr style="margin:1.5rem 0; border:none; border-top:1px solid rgba(0,0,0,0.08);">
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.auth_active == "login":
        tab_login, tab_register = st.tabs(["Sign In", "Create Account"])
    else:
        tab_register, tab_login = st.tabs(["Create Account", "Sign In"])

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

        if st.button("Sign In", type="primary", use_container_width=True,
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
                    st.success("✨ Welcome back!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            else:
                st.error("Invalid credentials")

    with tab_register:
        reg_user  = st.text_input("Choose username", key=f"reg_user_input_{st.session_state.login_nonce}")
        reg_pass  = st.text_input("Choose password", type="password", key=f"reg_pass_input_{st.session_state.login_nonce}")
        reg_pass2 = st.text_input("Confirm password", type="password", key=f"reg_pass2_input_{st.session_state.login_nonce}")

        if st.button("Create Account", use_container_width=True, key=f"register_btn_{st.session_state.login_nonce}"):
            if not reg_user or not reg_pass:
                st.warning("Please fill in all fields")
            elif len(reg_pass) < 8:
                st.warning("Password must be at least 8 characters")
            elif reg_pass != reg_pass2:
                st.warning("Passwords don't match")
            else:
                users = load_users()
                if reg_user in users:
                    st.error("Username already exists")
                else:
                    salt_user, pw_hash = hash_password(reg_pass)
                    users[reg_user] = {"salt": salt_user, "hash": pw_hash}
                    save_users(users)
                    st.session_state.prefill_login_username = reg_user
                    st.session_state.login_nonce += 1
                    st.success("✅ Account created! Please sign in above.")

    st.stop()

auth_gate()

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 🏠 Tenancy Assistant")
    st.caption("Powered by AI")

    _u_raw = st.session_state.user or ""
    _u = html.escape(_u_raw)
    _letters = re.findall(r"[A-Za-z]", _u_raw)
    _initials = ("".join(_letters[:2]) or _u_raw[:2] or "U").upper()
    _hue = int(hashlib.sha256(_u_raw.encode()).hexdigest(), 16) % 360
    _avatar_bg = f"hsl({_hue}, 70%, 50%)"

    st.markdown(
        f"""
        <div class="user-card">
            <div class="user-avatar" style="background:{_avatar_bg};">{_initials}</div>
            <div class="user-meta">
                <div class="label">Signed in as</div>
                <div class="name">{_u}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("#### 📄 Your Contract")
    uploaded = st.file_uploader("Upload PDF", type=["pdf"], key="upload_contract")
    if uploaded is not None:
        os.makedirs("./data", exist_ok=True)
        temp_path = "./data/_uploaded_agreement.pdf"
        with open(temp_path, "wb") as f:
            f.write(uploaded.read())
        st.success(f"✓ {uploaded.name}")

        if st.button("Use for Q&A", use_container_width=True, key="use_uploaded_qna"):
            st.session_state.active_pdf_path = temp_path
            try:
                shutil.copyfile(temp_path, DEFAULT_PDF_PATH)
            except Exception as e:
                st.warning(f"Error: {e}")
            importlib.reload(chat)
            st.cache_data.clear()
            st.rerun()

    if st.session_state.active_pdf_path != DEFAULT_PDF_PATH:
        st.info("📌 Using uploaded contract")
    else:
        st.caption("Using sample contract")

    if st.button("Reset", use_container_width=True, key="reset_pdf"):
        st.session_state.active_pdf_path = DEFAULT_PDF_PATH
        importlib.reload(chat)
        st.cache_data.clear()
        st.rerun()

    if st.button("Sign Out", use_container_width=True, key="logout_btn"):
        st.session_state.auth = False
        st.session_state.user = None
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 💬 Quick Questions")
    st.caption("Click to ask instantly")

    if FAQ_ITEMS:
        for category, questions in FAQ_ITEMS.items():
            with st.expander(f"**{category}**", expanded=False):
                for q in questions:
                    if st.button(q, key=f"faq_{category}_{q}"):
                        res = chat.ask(q)
                        st.session_state.messages.append({"role": "user", "content": q})
                        st.session_state.messages.append({"role": "assistant", "content": res})
                        st.rerun()

    st.markdown("---")
    st.markdown("### 🤝 Need Help?")
    if st.button("Contact Support", use_container_width=True, type="primary", key="contact_support_btn"):
        st.session_state.show_modal = True
        st.rerun()

# ========== HEADER ==========
st.markdown("""
<div class="header-box">
    <h1>Your Tenancy Assistant</h1>
    <p>Ask questions about your rental agreement and get instant, accurate answers powered by AI.</p>
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
            can_answer = content.get("can_answer", True)
            score = content.get("score", 1.0)
            is_comprehensive = content.get("is_comprehensive", False)
        else:
            answer = str(content)
            reference = None
            can_answer = True
            score = 1.0
            is_comprehensive = False

        match_percentage = int(round((1 - score) * 100)) if score is not None else 0
        
        if can_answer:
            status_badge = f'<span class="conf-badge conf-high">✅ Answer</span>'
            if is_comprehensive:
                status_badge += f'<span class="conf-badge" style="background:linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);color:white;">🔍 Detailed</span>'
            status_badge += f'<span class="conf-badge conf-accuracy">Match: {match_percentage}%</span>'
        else:
            status_badge = f'<span class="conf-badge conf-low">⚠️ Not Found</span>'
            status_badge += f'<span class="conf-badge conf-accuracy">Score: {match_percentage}%</span>'

        st.markdown(
            f"""
            <div style="display:flex;justify-content:flex-start;margin:0.75rem 0;">
                <div class="assistant-msg">
                    <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:0.85rem;">
                        {status_badge}
                    </div>
                    {answer}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # ========== Reference 部分 ==========
        if is_comprehensive:
            # 综合问题：显示汇总信息
            if reference and isinstance(reference, dict):
                pages = reference.get("pages", [])
                num_clauses = reference.get("num_clauses", 0)
                topics = reference.get("topics", [])
                
                if num_clauses > 0:
                    pages_str = ", ".join(map(str, sorted(set(pages)))) if pages else "N/A"
                    topics_str = ", ".join(topics) if topics else "N/A"
                    
                    with st.expander(f"📑 View All Sources ({num_clauses} clauses)", expanded=False):
                        st.markdown(
                            f"""
                            <div style="background:linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                                        color:white; padding:1.25rem 1.5rem; border-radius:12px; margin-bottom:1.25rem;
                                        box-shadow:0 4px 12px rgba(59,130,246,0.2);">
                                <div style="font-size:1rem; font-weight:600;">📍 Comprehensive Answer Sources</div>
                                <div style="margin-top:0.5rem; opacity:0.95; font-size:0.9rem;">
                                    {num_clauses} clauses from pages: {pages_str}
                                </div>
                                <div style="margin-top:0.25rem; opacity:0.9; font-size:0.85rem;">
                                    Topics: {topics_str}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                        st.info(f"💡 This answer synthesized information from {num_clauses} different clauses across {len(set(pages))} pages.")
        
        else:
            # 简单问题：显示单个条款 + PDF跳转
            if reference and isinstance(reference, dict):
                ref_text = reference.get("text", "")
                ref_page = reference.get("page", "?")
                display_page = int(ref_page) + 1 if str(ref_page).isdigit() else ref_page
                
                with st.expander("📄 View Source", expanded=False):
                    st.markdown(
                        f"""
                        <div style="background:linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
                                    color:white; padding:1.25rem 1.5rem; border-radius:12px; margin-bottom:1.25rem;
                                    box-shadow:0 4px 12px rgba(59,130,246,0.2);">
                            <div style="font-size:1rem; font-weight:600;">📍 Contract Reference</div>
                            <div style="margin-top:0.5rem; opacity:0.95; font-size:0.9rem;">
                                Page {display_page}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.markdown(
                        f"""
                        <div style="background:#f8fafc; padding:1.5rem; border-left:3px solid #3b82f6;
                                    border-radius:10px; line-height:1.8; color:#334155; font-size:0.9rem;
                                    box-shadow:0 2px 8px rgba(0,0,0,0.04); margin-bottom:1.25rem;">
                            <div style="color:#2563eb; font-weight:600; margin-bottom:0.75rem; font-size:0.85rem;">
                                RELEVANT CLAUSE:
                            </div>
                            {ref_text}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button(f"📖 View PDF (Page {display_page})", key=f"view_pdf_btn_{i}", use_container_width=True, type="primary"):
                        page_for_viewer = int(ref_page) if str(ref_page).isdigit() else 0
                        pdf_html = create_pdf_viewer(st.session_state.active_pdf_path, page_for_viewer)
                        st.markdown(pdf_html, unsafe_allow_html=True)

# ========== CHAT INPUT ==========
st.markdown("---")
user_input = st.chat_input("Ask anything about your tenancy agreement...")
if user_input:
    st.session_state.show_modal = False
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("Searching..."):
        res = chat.ask(user_input)
    st.session_state.messages.append({"role": "assistant", "content": res})
    st.rerun()

# ========== SUPPORT MODAL ==========
if st.session_state.get("show_modal", False):
    st.markdown("---")
    st.markdown("""
    ### 🤝 Human Support
    
    **When to contact support:**
    - Legal interpretation needed
    - Dispute resolution
    - Urgent maintenance issues
    - Special requests
    """)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Continue with AI", use_container_width=True, key="continue_ai"):
            st.session_state.show_modal = False
            st.rerun()
    with col2:
        st.link_button("WhatsApp", WHATSAPP_URL, use_container_width=True, type="primary")

# ========== FOOTER ==========
st.markdown("---")
st.caption("💡 Answers are based on your tenancy agreement • Use quick questions in sidebar for common queries")