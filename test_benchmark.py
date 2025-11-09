# test_benchmark.py
"""
Benchmark测试：验证项目要求的3个标准问题
目标：所有问题都应该达到High confidence
"""

from src.chat import ask
import json
from datetime import datetime

# 项目要求的3个benchmark问题
BENCHMARK_QUESTIONS = [
    "What's the diplomatic clause?",
    "When things are spoiled/broken, who pays to repair?",
    "What to do before returning the unit?",
]

def test_benchmark():
    """测试benchmark问题"""
    print("="*80)
    print("BENCHMARK VALIDATION TEST")
    print("="*80)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Questions: {len(BENCHMARK_QUESTIONS)}")
    print("="*80)
    
    results = []
    passed = 0
    
    for i, question in enumerate(BENCHMARK_QUESTIONS, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}: {question}")
        print("="*80)
        
        # 执行查询
        response = ask(question)
        
        # 提取信息
        confidence = response.get('confidence', 'Unknown')
        score = response.get('score', 0.0)
        has_reference = response.get('reference') is not None
        answer = response.get('answer', '')
        
        # 判断是否通过
        is_pass = confidence == "High"
        
        if is_pass:
            passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
        
        print(f"\nStatus: {status}")
        print(f"Confidence: {confidence}")
        print(f"Score: {score:.4f}")
        print(f"Has Reference: {'Yes' if has_reference else 'No'}")
        
        if has_reference:
            ref_page = response['reference'].get('page', '?')
            print(f"Reference Page: {ref_page}")
        
        print(f"\nAnswer Preview:")
        print(f"{answer[:200]}...")
        
        # 保存结果
        results.append({
            'question': question,
            'confidence': confidence,
            'score': score,
            'has_reference': has_reference,
            'passed': is_pass,
            'answer': answer
        })
    
    # 总结
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\nTotal Questions: {len(BENCHMARK_QUESTIONS)}")
    print(f"Passed: {passed}/{len(BENCHMARK_QUESTIONS)}")
    print(f"Pass Rate: {passed/len(BENCHMARK_QUESTIONS)*100:.1f}%")
    
    if passed == len(BENCHMARK_QUESTIONS):
        print("\n🎉 All benchmark questions passed!")
    else:
        print(f"\n⚠️  {len(BENCHMARK_QUESTIONS) - passed} question(s) failed")
        print("\nFailed questions:")
        for r in results:
            if not r['passed']:
                print(f"  • {r['question']}")
                print(f"    Got: {r['confidence']} (expected: High)")
    
    # 保存结果
    output = {
        'test_time': datetime.now().isoformat(),
        'total': len(BENCHMARK_QUESTIONS),
        'passed': passed,
        'pass_rate': passed/len(BENCHMARK_QUESTIONS),
        'results': results
    }
    
    with open('benchmark_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*80)
    print(f"Results saved to: benchmark_test_results.json")
    print("="*80)
    
    return results


if __name__ == "__main__":
    test_benchmark()