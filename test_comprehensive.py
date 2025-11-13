# test_comprehensive.py
"""
测试功能2：多RAG综合回答
"""

import sys
sys.path.insert(0, '.')

from src.chat import ask

# 测试问题
TEST_QUESTIONS = [
    # 综合性问题（应该触发功能2）
    "What do I need to do before moving out?",
    "Who is responsible for repairs?",
    "What are my payment obligations?",
    "What happens if I want to terminate the tenancy early?",
    
    # 普通问题（应该用功能1）
    "When is my rent due?",
    "Can I keep pets?",
]

print("="*80)
print("🧪 测试功能2：多RAG综合回答")
print("="*80)

for i, question in enumerate(TEST_QUESTIONS, 1):
    print(f"\n{'='*80}")
    print(f"问题 {i}: {question}")
    print("="*80)
    
    try:
        response = ask(question)
        
        print(f"\n✅ 回答成功!")
        print(f"   是否综合回答: {response.get('is_comprehensive', False)}")
        print(f"   能否回答: {response.get('can_answer', False)}")
        
        if response.get('is_comprehensive'):
            print(f"   使用条款数: {response.get('num_clauses_used', 0)}")
            print(f"   覆盖主题: {response.get('topics_covered', [])}")
            
            if response.get('reference'):
                ref = response['reference']
                print(f"   引用页码: {ref.get('pages', [])}")
        else:
            print(f"   分数: {response.get('score', 1.0):.3f}")
        
        print(f"\n📝 答案:")
        print("-"*80)
        answer = response.get('answer', '')
        # 只显示前500字符
        if len(answer) > 500:
            print(answer[:500] + "...")
        else:
            print(answer)
        print("-"*80)
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*80}")
print("✅ 测试完成!")
print("="*80)