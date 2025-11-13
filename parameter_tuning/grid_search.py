#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速网格搜索 - 放在 parameter_tuning 目录运行
"""

import os
import sys
import shutil
import json
from datetime import datetime
from itertools import product

# 添加项目根目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)  # 切换到根目录

print(f"✅ 工作目录: {os.getcwd()}")

# 测试用例
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

# 参数网格
PARAM_GRID = {
    'threshold': [0.70, 0.72, 0.75, 0.78, 0.80, 0.82, 0.85],
    'chunk_size': [450, 500, 600],
    'chunk_overlap': [100, 150],
}

def update_config(chunk_size, chunk_overlap, threshold):
    """更新config.py"""
    config_content = f"""# src/config.py - AUTO GENERATED
import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

CHUNK_SIZE = {chunk_size}
CHUNK_OVERLAP = {chunk_overlap}

TOP_K_RETRIEVAL = 10
TOP_K_CONTEXT = 3
USE_MMR = False
MMR_LAMBDA = 0.7

THRESHOLD_CAN_ANSWER = {threshold}
"""
    
    with open('src/config.py', 'w', encoding='utf-8') as f:
        f.write(config_content)


def rebuild_vector_store():
    """重建向量存储"""
    print("      重建向量存储...", end="", flush=True)
    if os.path.exists('vector_store'):
        shutil.rmtree('vector_store')
    ret = os.system('python -m src.embedder > /dev/null 2>&1')
    if ret == 0:
        print(" ✅")
    else:
        print(" ❌")


def test_configuration():
    """测试当前配置"""
    # 清除缓存的模块
    for module in list(sys.modules.keys()):
        if module.startswith('src.'):
            del sys.modules[module]
    
    from src.chat import ask
    
    results = []
    correct = 0
    total = sum(len(q) for q in TEST_CASES.values())
    
    for expected, questions in TEST_CASES.items():
        for question in questions:
            try:
                response = ask(question)
                can_answer = response.get('can_answer', True)
                predicted = 'CanAnswer' if can_answer else 'CannotAnswer'
                is_correct = (predicted == expected)
                
                if is_correct:
                    correct += 1
                
                results.append({
                    'question': question,
                    'expected': expected,
                    'predicted': predicted,
                    'correct': is_correct,
                    'score': response.get('score', 1.0)
                })
            except Exception as e:
                print(f"\n      ❌ 错误: {str(e)[:50]}")
                results.append({
                    'question': question,
                    'expected': expected,
                    'predicted': 'Error',
                    'correct': False,
                    'error': str(e)
                })
    
    accuracy = (correct / total) * 100
    
    can_results = [r for r in results if r['expected'] == 'CanAnswer']
    cannot_results = [r for r in results if r['expected'] == 'CannotAnswer']
    
    can_acc = sum(1 for r in can_results if r['correct']) / len(can_results) * 100
    cannot_acc = sum(1 for r in cannot_results if r['correct']) / len(cannot_results) * 100
    
    return {
        'accuracy': accuracy,
        'can_answer_accuracy': can_acc,
        'cannot_answer_accuracy': cannot_acc,
        'correct': correct,
        'total': total
    }


def main():
    print("="*80)
    print("⚡ 快速网格搜索 - 二分类版本")
    print("="*80)
    
    total_combos = (
        len(PARAM_GRID['threshold']) *
        len(PARAM_GRID['chunk_size']) *
        len(PARAM_GRID['chunk_overlap'])
    )
    
    print(f"\n📊 参数空间:")
    print(f"  Threshold: {PARAM_GRID['threshold']}")
    print(f"  Chunk size: {PARAM_GRID['chunk_size']}")
    print(f"  Chunk overlap: {PARAM_GRID['chunk_overlap']}")
    print(f"\n📈 总组合数: {total_combos}")
    print(f"⏱️  预计耗时: ~{total_combos * 1.5:.0f} 分钟")
    
    input("\n按 Enter 开始...")
    
    # 备份
    if os.path.exists('src/config.py'):
        shutil.copy('src/config.py', 'src/config.py.backup')
    
    all_results = []
    current = 0
    last_chunk = (None, None)
    
    start_time = datetime.now()
    
    # 遍历
    for chunk_size, chunk_overlap in product(PARAM_GRID['chunk_size'], PARAM_GRID['chunk_overlap']):
        
        needs_rebuild = (last_chunk != (chunk_size, chunk_overlap))
        
        if needs_rebuild:
            print(f"\n{'='*80}")
            print(f"📦 Chunk: size={chunk_size}, overlap={chunk_overlap}")
            print("="*80)
            update_config(chunk_size, chunk_overlap, 0.75)
            rebuild_vector_store()
            last_chunk = (chunk_size, chunk_overlap)
        
        for threshold in PARAM_GRID['threshold']:
            current += 1
            
            print(f"   [{current}/{total_combos}] threshold={threshold:.2f} ", end="", flush=True)
            
            update_config(chunk_size, chunk_overlap, threshold)
            test_result = test_configuration()
            
            result = {
                'params': {
                    'chunk_size': chunk_size,
                    'chunk_overlap': chunk_overlap,
                    'threshold': threshold
                },
                'accuracy': test_result['accuracy'],
                'can_acc': test_result['can_answer_accuracy'],
                'cannot_acc': test_result['cannot_answer_accuracy']
            }
            
            all_results.append(result)
            
            print(f"→ {test_result['accuracy']:.1f}% (✅{test_result['can_answer_accuracy']:.0f}% ❌{test_result['cannot_answer_accuracy']:.0f}%)")
    
    elapsed = (datetime.now() - start_time).total_seconds() / 60
    
    # 结果
    print(f"\n{'='*80}")
    print("🏆 TOP 10 最佳配置")
    print("="*80)
    
    all_results_sorted = sorted(all_results, key=lambda x: x['accuracy'], reverse=True)
    
    for i, r in enumerate(all_results_sorted[:10], 1):
        p = r['params']
        print(f"\n【{i}】准确率: {r['accuracy']:.1f}%")
        print(f"    chunk={p['chunk_size']}/{p['chunk_overlap']}, threshold={p['threshold']}")
        print(f"    CanAnswer={r['can_acc']:.0f}%, CannotAnswer={r['cannot_acc']:.0f}%")
    
    # 保存到parameter_tuning目录
    output_dir = os.path.join(SCRIPT_DIR, 'results')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'test_time': datetime.now().isoformat(),
            'elapsed_minutes': elapsed,
            'results': all_results_sorted
        }, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"💾 结果: {output_file}")
    print(f"⏱️  耗时: {elapsed:.1f} 分钟")
    
    # 恢复
    if os.path.exists('src/config.py.backup'):
        shutil.copy('src/config.py.backup', 'src/config.py')
        print("✅ 已恢复原始配置")
    
    # 最优配置
    best = all_results_sorted[0]
    print(f"\n✅ 最优配置:")
    print(f"   CHUNK_SIZE = {best['params']['chunk_size']}")
    print(f"   CHUNK_OVERLAP = {best['params']['chunk_overlap']}")
    print(f"   THRESHOLD_CAN_ANSWER = {best['params']['threshold']}")
    print(f"   准确率 = {best['accuracy']:.1f}%")


if __name__ == "__main__":
    main()