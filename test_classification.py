# test_binary_classification.py
"""
二分类测试：能回答 vs 不能回答
目标：准确率 ≥ 85%
"""

from src.chat import ask
import json
from datetime import datetime

# 二分类测试用例
TEST_CASES = {
    "CanAnswer": [
        # 合同中明确有答案的
        "When is my rent due each month?",
        "What is the security deposit amount?",
        "Who pays for electricity and water?",
        "What's the diplomatic clause?",
        "Who is responsible for air conditioning maintenance?",
        "Can I keep pets?",
        "Who pays for repairs under $200?",
        
        # 需要推理但能从合同推出的
        "Can I install a dishwasher?",
        "What if the aircon breaks during the first week?",
        "Can my parents visit and stay for 2 months?",
    ],
    
    "CannotAnswer": [
        # 完全不在合同中的问题
        "What's the best internet service provider in Singapore?",
        "How do I apply for a work permit?",
        "Where can I buy furniture nearby?",
        "What's the weather like in Singapore?",
        "How do I open a bank account in DBS?",
        "Which primary school is good for my children?",
        "Where is the nearest MRT station?",
    ]
}

def test_binary_classification():
    """测试二分类准确率"""
    print("="*80)
    print("🧪 BINARY CLASSIFICATION TEST")
    print("="*80)
    print(f"⏰ Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target Accuracy: ≥85%")
    
    total_questions = sum(len(questions) for questions in TEST_CASES.values())
    print(f"\n📝 Total Questions: {total_questions}")
    print(f"   - CanAnswer: {len(TEST_CASES['CanAnswer'])}")
    print(f"   - CannotAnswer: {len(TEST_CASES['CannotAnswer'])}")
    print("="*80)
    
    all_results = []
    correct_count = 0
    confusion_matrix = {
        "CanAnswer": {"CanAnswer": 0, "CannotAnswer": 0},
        "CannotAnswer": {"CanAnswer": 0, "CannotAnswer": 0}
    }
    
    # 测试每个类别
    for expected, questions in TEST_CASES.items():
        print(f"\n{'='*80}")
        print(f"🔍 Testing {expected} Questions")
        print("="*80)
        
        for i, question in enumerate(questions, 1):
            print(f"\n[{i}/{len(questions)}] {question}")
            
            try:
                response = ask(question)
                
                # 提取信息
                can_answer = response.get('can_answer', False)
                actual = "CanAnswer" if can_answer else "CannotAnswer"
                score = response.get('score', 0.0)
                
                # 判断是否正确
                is_correct = (actual == expected)
                if is_correct:
                    correct_count += 1
                    symbol = "✅"
                else:
                    symbol = "❌"
                
                # 更新混淆矩阵
                confusion_matrix[expected][actual] += 1
                
                print(f"   {symbol} Expected: {expected} | Got: {actual} | Score: {score:.3f}")
                
                # 保存结果
                all_results.append({
                    'question': question,
                    'expected': expected,
                    'actual': actual,
                    'score': score,
                    'correct': is_correct
                })
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                all_results.append({
                    'question': question,
                    'expected': expected,
                    'actual': 'Error',
                    'score': 1.0,
                    'correct': False
                })
    
    # 计算准确率
    accuracy = (correct_count / total_questions) * 100
    
    # 显示混淆矩阵
    print("\n" + "="*80)
    print("📊 CONFUSION MATRIX")
    print("="*80)
    print("\n                    Predicted →")
    print("Actual ↓         CanAnswer  CannotAnswer")
    print("-" * 50)
    for expected in ["CanAnswer", "CannotAnswer"]:
        counts = confusion_matrix[expected]
        print(f"{expected:15}  {counts['CanAnswer']:10}  {counts['CannotAnswer']:12}")
    
    # 分类别准确率
    print("\n" + "="*80)
    print("📈 PER-CLASS ACCURACY")
    print("="*80)
    
    for expected in ["CanAnswer", "CannotAnswer"]:
        total_in_class = len(TEST_CASES[expected])
        correct_in_class = confusion_matrix[expected][expected]
        class_accuracy = (correct_in_class / total_in_class) * 100 if total_in_class > 0 else 0
        
        if class_accuracy >= 85:
            marker = "✅"
        elif class_accuracy >= 70:
            marker = "⚠️ "
        else:
            marker = "❌"
        
        print(f"{marker} {expected:15}: {correct_in_class}/{total_in_class} = {class_accuracy:.1f}%")
    
    # 总结
    print("\n" + "="*80)
    print("🎯 OVERALL SUMMARY")
    print("="*80)
    print(f"\n📝 Total Questions: {total_questions}")
    print(f"✅ Correctly Classified: {correct_count}")
    print(f"❌ Misclassified: {total_questions - correct_count}")
    print(f"\n📊 Overall Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 85:
        print(f"\n🎉 TARGET ACHIEVED! (≥85%)")
    else:
        print(f"\n⚠️  Below target. Need {85 - accuracy:.1f}% improvement")
    
    # 显示错误案例
    errors = [r for r in all_results if not r['correct']]
    if errors:
        print("\n" + "="*80)
        print(f"❌ MISCLASSIFIED CASES ({len(errors)})")
        print("="*80)
        for err in errors:
            print(f"\nQ: {err['question']}")
            print(f"   Expected: {err['expected']} → Got: {err['actual']}")
            print(f"   Score: {err.get('score', 'N/A'):.3f}")
    
    # 保存结果
    output = {
        'test_time': datetime.now().isoformat(),
        'classification_type': 'binary',
        'total_questions': total_questions,
        'correct': correct_count,
        'accuracy': accuracy,
        'confusion_matrix': confusion_matrix,
        'results': all_results
    }
    
    with open('binary_classification_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print(f"💾 Results saved to: binary_classification_results.json")
    print("="*80)
    
    return output


if __name__ == "__main__":
    print("\n🚀 Starting binary classification test...\n")
    results = test_binary_classification()
    
    print(f"\n✅ Test complete!")
    print(f"🎯 Final Accuracy: {results['accuracy']:.1f}%")