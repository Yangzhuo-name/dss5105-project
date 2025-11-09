# src/config.py
import os
from dotenv import load_dotenv

# 自动加载 .env 文件中的变量（如果存在）
load_dotenv()

# ========== API KEYS ==========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY. Please set it in your .env file or environment.")

# ========== EMBEDDING MODEL ==========
EMBEDDING_MODEL = "text-embedding-3-small"

# ========== CHUNKING PARAMETERS ==========
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# ========== CHAT MODEL ==========
CHAT_MODEL = "gpt-4o-mini"

# ========== RETRIEVAL PARAMETERS ==========
TOP_K_RETRIEVAL = 5
TOP_K_CONTEXT = 3
