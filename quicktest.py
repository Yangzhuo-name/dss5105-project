#!/usr/bin/env python3
"""
快速单次测试 - 不保存，测完就恢复
"""

import os
import sys
import shutil

# 添加路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

# 测试参数
TEST_CHUNK_SIZE = 450
TEST_CHUNK_OVERLAP = 100
TEST_THRESHOLD = 0.65

print("="*80)
print(f"🧪 快速测试: chunk={TEST_CHUNK_SIZE}/{TEST_CHUNK_OVERLAP}, threshold={TEST_THRESHOLD}")
print("="*80)

# 1. 备份配置
print("\n1️⃣  备份配置...")
shutil.copy('src/config.py', 'src/config.py.test_backup')

# 2. 写入测试配置
print("2️⃣  写入测试配置...")
config_content = f"""# src/config.py - TEMPORARY TEST CONFIG
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

CHUNK_SIZE = {TEST_CHUNK_SIZE}
CHUNK_OVERLAP = {TEST_CHUNK_OVERLAP}

TOP_K_RETRIEVAL = 10
TOP_K_CONTEXT = 3
USE_MMR = False
MMR_LAMBDA = 0.7

THRESHOLD_CAN_ANSWER = {TEST_THRESHOLD}
"""

with open('src/config.py', 'w') as f:
    f.write(config_content)

# 3. 重建向量存储
print("3️⃣  重建向量存储...")
if os.path.exists('vector_store'):
    shutil.rmtree('vector_store')
os.system('python -m src.embedder')

# 4. 运行测试
print("\n4️⃣  运行测试...")
print("="*80)

# 清除模块缓存
for module in list(sys.modules.keys()):
    if module.startswith('src.'):
        del sys.modules[module]

from src.chat import ask

TEST_CASES = {
    "CanAnswer": [
        "When is my rent due each month?",
        "What is the security deposit amount?",
        "Who pays for electricity and water?",
        "What's the diplomatic clause?",
        "Who is responsible for air conditioning maintenance?",
        "Can I keep pets?",
        "Who pays for repairs under $200?",
        "Can I install a dishwasher?",
        "What if the aircon breaks during the first week?",
    ],
    
    "CannotAnswer": [
        "What's the best internet service provider in Singapore?",
        "How do I apply for a work permit?",
        "Where can I buy furniture nearby?",
        "What's the weather like in Singapore?",
        "How do I open a bank account in DBS?",
        "Which primary school is good for my children?",
        "Where is the nearest MRT station?",
    ]
}

correct = 0
total = 0
confusion = {"CanAnswer": {"CanAnswer": 0, "CannotAnswer": 0}, 
             "CannotAnswer": {"CanAnswer": 0, "CannotAnswer": 0}}

for expected, questions in TEST_CASES.items():
    print(f"\n{'='*80}")
    print(f"Testing {expected}")
    print("="*80)
    
    for q in questions:
        total += 1
        try:
            response = ask(q)
            can_answer = response.get('can_answer', True)
            predicted = 'CanAnswer' if can_answer else 'CannotAnswer'
            score = response.get('score', 1.0)
            
            is_correct = (predicted == expected)
            if is_correct:
                correct += 1
                symbol = "✅"
            else:
                symbol = "❌"
            
            confusion[expected][predicted] += 1
            
            print(f"{symbol} {q[:60]}")
            print(f"   Expected: {expected} | Got: {predicted} | Score: {score:.3f}")
            
        except Exception as e:
            print(f"❌ {q[:60]}")
            print(f"   Error: {str(e)}")

accuracy = (correct / total) * 100

# 结果
print("\n" + "="*80)
print("📊 RESULTS")
print("="*80)

print(f"\nConfusion Matrix:")
print(f"                    Predicted")
print(f"Actual        CanAnswer  CannotAnswer")
print(f"CanAnswer         {confusion['CanAnswer']['CanAnswer']:2}          {confusion['CanAnswer']['CannotAnswer']:2}")
print(f"CannotAnswer      {confusion['CannotAnswer']['CanAnswer']:2}          {confusion['CannotAnswer']['CannotAnswer']:2}")

can_acc = confusion['CanAnswer']['CanAnswer'] / len(TEST_CASES['CanAnswer']) * 100
cannot_acc = confusion['CannotAnswer']['CannotAnswer'] / len(TEST_CASES['CannotAnswer']) * 100

print(f"\n📈 Overall Accuracy: {accuracy:.1f}%")
print(f"   CanAnswer: {can_acc:.1f}%")
print(f"   CannotAnswer: {cannot_acc:.1f}%")

# 5. 恢复配置
print("\n" + "="*80)
print("5️⃣  恢复原始配置...")
shutil.copy('src/config.py.test_backup', 'src/config.py')
os.remove('src/config.py.test_backup')
print("✅ 已恢复，测试配置已删除")
print("="*80)

print(f"\n💡 与0.70对比:")
print(f"   Threshold 0.70: 75.0% (CanAnswer 89%, CannotAnswer 57%)")
print(f"   Threshold {TEST_THRESHOLD}: {accuracy:.1f}% (CanAnswer {can_acc:.0f}%, CannotAnswer {cannot_acc:.0f}%)")