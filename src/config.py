# src/config.py
"""
配置文件 - 基于网格搜索的最优参数
准确率: 82.4%
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ========== API KEYS ==========
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OPENAI_API_KEY. Please set it in your .env file or environment.")

# ========== MODELS ==========
EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# ========== CHUNKING PARAMETERS (OPTIMIZED) ==========
# 基于网格搜索的最优值
CHUNK_SIZE = 450
CHUNK_OVERLAP = 100

# ========== RETRIEVAL PARAMETERS ==========
# 功能1（单条款回答）
TOP_K_RETRIEVAL = 10     # 初始检索数量
TOP_K_CONTEXT = 3        # 给LLM的上下文数量

# 功能2（多RAG综合回答）
TOP_K_COMPREHENSIVE = 50      # 综合回答时检索更多候选
RELEVANCE_THRESHOLD = 0.80    # 收集相关chunks的阈值（宽松）

# MMR设置（当前未启用）
USE_MMR = False
MMR_LAMBDA = 0.7

# ========== CONFIDENCE THRESHOLD (BINARY CLASSIFICATION) ==========
# 基于网格搜索的最优值：0.65
# 准确率: 82.4% (CanAnswer: 78%, CannotAnswer: 86%)
THRESHOLD_CAN_ANSWER = 0.65

# ========== 说明 ==========
# THRESHOLD_CAN_ANSWER (0.65) 用途：
#   - 判断问题是否能回答
#   - score < 0.65 → 能回答
#   - score >= 0.65 → 不能回答，转人工
#
# RELEVANCE_THRESHOLD (0.80) 用途（功能2专用）：
#   - 收集所有相关的chunks
#   - score < 0.80 → 算作相关，包含在综合答案中
#   - 比0.65宽松，避免漏掉次要相关信息