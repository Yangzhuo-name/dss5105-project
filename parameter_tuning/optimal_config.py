# src/config.py
# 🎯 自动优化的配置（基于网格搜索结果）
# 生成时间: 2025-11-13 01:45:25

import os
from dotenv import load_dotenv

load_dotenv()

# ========== API KEYS ==========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY. Please set it in your .env file or environment.")

# ========== EMBEDDING MODEL ==========
EMBEDDING_MODEL = "text-embedding-3-small"

# ========== OPTIMIZED CHUNKING PARAMETERS ==========
CHUNK_SIZE = 400
CHUNK_OVERLAP = 100

# ========== CHAT MODEL ==========
CHAT_MODEL = "gpt-4o-mini"

# ========== OPTIMIZED RETRIEVAL PARAMETERS ==========
TOP_K_RETRIEVAL = 10
TOP_K_CONTEXT = 3

# ========== OPTIMIZED CONFIDENCE THRESHOLDS ==========
THRESHOLD_HIGH = 0.6
THRESHOLD_MEDIUM = 0.8

# ========== OPTIMIZED ADVANCED SETTINGS ==========
USE_MMR = True
MMR_LAMBDA = 0.7
SCORE_GAP_THRESHOLD = 0.05
