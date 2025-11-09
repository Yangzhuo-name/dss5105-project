# test_classification_accuracy.py
"""
分类准确率测试：验证三级置信度分类是否准确
目标：准确率 ≥ 85%
"""

from src.chat import ask
import json
from datetime import datetime

# 测试用例：分三个置信度级别
TEST_CASES = {
    "High": [
        "When is my rent due each month?",
        "What is the security deposit amount?",
        "Who pays for electricity and water?",
        "What's the diplomatic clause?",
        "Who is responsible for air conditioning maintenance?",
        "Can I keep pets?",
        "Who pays for repairs under $200?",
    ],
    
    "Medium": [
        "Can I paint the walls?",
        "What happens if I want to install a washing machine?",
        "Can I hang pictures on the wall?",
        "What if I need to break the lease due to job loss?",
    ],
    
    "Low": [
        "How do I negotiate a rent reduction?",
        "What's the average rent in this area?",
        "Can I get a tax deduction for my rent?",
        "Which moving company do you recommend?",
        "How do I apply for a housing loan?",
    ]
}

def test_classification_accuracy():
    """测试分类准确率"""
    print("="*80)
    print("CLASSIFICATION ACCURACY TEST")
    print("="*80)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_questions = sum(len(questions) for questions in TEST_CASES.values())
    print(f"Total Questions: {total_questions}")
    print(f"  - High: {len(TEST_CASES['High'])}")
    print(f"  - Medium: {len(TEST_CASES['Medium'])}")
    print(f"  - Low: {len(TEST_CASES['Low'])}")
    print("="*80)
    
    all_results = []
    correct_count = 0
    confusion_matrix = {
        "High": {"High": 0, "Medium": 0, "Low": 0},
        "Medium": {"High": 0, "Medium": 0, "Low": 0},
        "Low": {"High": 0, "Medium": 0, "Low": 0}
    }
    
    # 测试每个类别
    for expected_confidence, questions in TEST_CASES.items():
        print(f"\n{'='*80}")
        print(f"Testing {expected_confidence} Confidence Questions")
        print("="*80)
        
        for question in questions:
            # 执行查询
            response = ask(question)
            
            # 提取信息
            actual_confidence = response.get('confidence', 'Unknown')
            score = response.get('score', 0.0)
            has_reference = response.get('reference') is not None
            
            # 判断是否正确
            is_correct = (actual_confidence == expected_confidence)
            if is_correct:
                correct_count += 1
                symbol = "✅"
            else:
                symbol = "❌"
            
            # 更新混淆矩阵
            confusion_matrix[expected_confidence][actual_confidence] += 1
            
            print(f"\n{symbol} Q: {question}")
            print(f"   Expected: {expected_confidence} | Got: {actual_confidence} | Score: {score:.3f}")
            
            # 保存结果
            all_results.append({
                'question': question,
                'expected': expected_confidence,
                'actual': actual_confidence,
                'score': score,
                'has_reference': has_reference,
                'correct': is_correct
            })
    
    # 计算准确率
    accuracy = (correct_count / total_questions) * 100
    
    # 显示混淆矩阵
    print("\n" + "="*80)
    print("CONFUSION MATRIX")
    print("="*80)
    print("\n             Predicted →")
    print("Actual ↓     High    Medium    Low")
    print("-" * 40)
    for expected in ["High", "Medium", "Low"]:
        counts = confusion_matrix[expected]
        print(f"{expected:8}     {counts['High']:4}    {counts['Medium']:6}    {counts['Low']:3}")
    
    # 分类别准确率
    print("\n" + "="*80)
    print("PER-CLASS ACCURACY")
    print("="*80)
    for expected in ["High", "Medium", "Low"]:
        total_in_class = len(TEST_CASES[expected])
        correct_in_class = confusion_matrix[expected][expected]
        class_accuracy = (correct_in_class / total_in_class) * 100 if total_in_class > 0 else 0
        print(f"{expected:8}: {correct_in_class}/{total_in_class} = {class_accuracy:.1f}%")
    
    # 总结
    print("\n" + "="*80)
    print("OVERALL SUMMARY")
    print("="*80)
    print(f"\nTotal Questions: {total_questions}")
    print(f"Correctly Classified: {correct_count}")
    print(f"Misclassified: {total_questions - correct_count}")
    print(f"\n📊 Overall Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 85:
        print("\n✅ Target achieved! (≥85%)")
    else:
        print(f"\n⚠️  Below target. Need {85 - accuracy:.1f}% improvement")
    
    # 显示错误案例
    errors = [r for r in all_results if not r['correct']]
    if errors:
        print("\n" + "="*80)
        print(f"MISCLASSIFIED CASES ({len(errors)})")
        print("="*80)
        for err in errors:
            print(f"\nQ: {err['question']}")
            print(f"   Expected: {err['expected']} → Got: {err['actual']} (Score: {err['score']:.3f})")
    
    # 保存结果
    output = {
        'test_time': datetime.now().isoformat(),
        'total_questions': total_questions,
        'correct': correct_count,
        'accuracy': accuracy,
        'confusion_matrix': confusion_matrix,
        'per_class_accuracy': {
            level: (confusion_matrix[level][level] / len(TEST_CASES[level])) * 100
            for level in ["High", "Medium", "Low"]
        },
        'results': all_results
    }
    
    with open('classification_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80
    print(f"Results saved to: classification_test_results.json")
    print("="*80)
    
    return output


if __name__ == "__main__":
    test_classification_accuracy()