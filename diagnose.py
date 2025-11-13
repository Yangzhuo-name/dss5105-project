# diagnostic_scores.py
"""
诊断脚本：查看每个测试问题的实际检索分数
目的：找出为什么所有问题都被判为High
"""

from src.retriever import search
from src.config import THRESHOLD_HIGH, THRESHOLD_MEDIUM

# 测试用例
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

PDF_PATH = "./data/tenancy_agreement.pdf"

print("="*80)
print("🔬 SCORE DISTRIBUTION ANALYSIS")
print("="*80)
print(f"当前阈值设置:")
print(f"  HIGH < {THRESHOLD_HIGH}")
print(f"  MEDIUM < {THRESHOLD_MEDIUM}")
print(f"  LOW >= {THRESHOLD_MEDIUM}")
print("="*80)

all_scores = []

for expected_level, questions in TEST_CASES.items():
    print(f"\n{'='*80}")
    print(f"📊 {expected_level} 类别问题的分数分布")
    print("="*80)
    
    level_scores = []
    
    for question in questions:
        try:
            results = search(
                question,
                top_k=5,
                with_scores=True,
                active_pdf_path=PDF_PATH
            )
            
            if results:
                top_score = results[0].metadata.get('score', 1.0)
                level_scores.append(top_score)
                
                # 判断会被分到哪个级别
                if top_score < THRESHOLD_HIGH:
                    predicted = "HIGH"
                    symbol = "🟢"
                elif top_score < THRESHOLD_MEDIUM:
                    predicted = "MEDIUM"
                    symbol = "🟡"
                else:
                    predicted = "LOW"
                    symbol = "🔴"
                
                # 是否正确
                correct = (predicted == expected_level.upper())
                result_symbol = "✅" if correct else "❌"
                
                print(f"\n{result_symbol} {question}")
                print(f"   分数: {top_score:.4f} → 预测: {symbol} {predicted} (期望: {expected_level.upper()})")
                
                # 修复：使用列表推导式分开处理
                top3_scores = [r.metadata.get('score', 1.0) for r in results[:3]]
                top3_formatted = [f'{s:.4f}' for s in top3_scores]
                print(f"   Top-3 分数: {top3_formatted}")
                
                # 显示检索到的内容预览
                content_preview = results[0].page_content[:150].replace('\n', ' ')
                print(f"   检索内容: {content_preview}...")
                
            else:
                print(f"\n❌ {question}")
                print(f"   没有检索结果")
                
        except Exception as e:
            print(f"\n❌ {question}")
            print(f"   错误: {str(e)}")
    
    # 统计该类别的分数范围
    if level_scores:
        print(f"\n📈 {expected_level} 类别统计:")
        print(f"   最小分数: {min(level_scores):.4f}")
        print(f"   最大分数: {max(level_scores):.4f}")
        print(f"   平均分数: {sum(level_scores)/len(level_scores):.4f}")
        all_scores.extend([(expected_level, s) for s in level_scores])

# 全局分析
print(f"\n{'='*80}")
print("📊 全局分数分布分析")
print("="*80)

high_scores = [s for level, s in all_scores if level == "High"]
medium_scores = [s for level, s in all_scores if level == "Medium"]
low_scores = [s for level, s in all_scores if level == "Low"]

print(f"\nHigh 类别: {len(high_scores)} 个问题")
if high_scores:
    print(f"  范围: {min(high_scores):.4f} - {max(high_scores):.4f}")
    print(f"  平均: {sum(high_scores)/len(high_scores):.4f}")

print(f"\nMedium 类别: {len(medium_scores)} 个问题")
if medium_scores:
    print(f"  范围: {min(medium_scores):.4f} - {max(medium_scores):.4f}")
    print(f"  平均: {sum(medium_scores)/len(medium_scores):.4f}")

print(f"\nLow 类别: {len(low_scores)} 个问题")
if low_scores:
    print(f"  范围: {min(low_scores):.4f} - {max(low_scores):.4f}")
    print(f"  平均: {sum(low_scores)/len(low_scores):.4f}")

# 关键发现
print(f"\n{'='*80}")
print("💡 关键发现")
print("="*80)

all_score_values = [s for _, s in all_scores]
if all_score_values:
    global_min = min(all_score_values)
    global_max = max(all_score_values)
    global_avg = sum(all_score_values) / len(all_score_values)
    
    print(f"\n整体分数范围: {global_min:.4f} - {global_max:.4f}")
    print(f"整体平均分数: {global_avg:.4f}")
    
    # 检查是否所有分数都低于HIGH阈值
    all_below_high = all(s < THRESHOLD_HIGH for s in all_score_values)
    if all_below_high:
        print(f"\n⚠️  警告: 所有问题的分数都 < {THRESHOLD_HIGH} (HIGH阈值)")
        print(f"这意味着所有问题都会被判为HIGH!")
        print(f"\n💡 建议:")
        print(f"  1. 问题可能不在阈值上，而是测试用例设计")
        print(f"  2. Medium/Low问题可能在合同中都能找到相关内容")
        print(f"  3. 需要重新设计测试用例，使用真正'不在合同中'的问题")
    else:
        # 统计各个范围的分布
        high_range = sum(1 for s in all_score_values if s < THRESHOLD_HIGH)
        medium_range = sum(1 for s in all_score_values if THRESHOLD_HIGH <= s < THRESHOLD_MEDIUM)
        low_range = sum(1 for s in all_score_values if s >= THRESHOLD_MEDIUM)
        
        print(f"\n📊 分数分布:")
        print(f"  HIGH范围 (< {THRESHOLD_HIGH}): {high_range} 个问题")
        print(f"  MEDIUM范围 ({THRESHOLD_HIGH}-{THRESHOLD_MEDIUM}): {medium_range} 个问题")
        print(f"  LOW范围 (>= {THRESHOLD_MEDIUM}): {low_range} 个问题")
    
    # 检查Medium和Low的分数是否有区别
    if medium_scores and low_scores:
        medium_avg = sum(medium_scores) / len(medium_scores)
        low_avg = sum(low_scores) / len(low_scores)
        
        print(f"\n📊 Medium vs Low 对比:")
        print(f"   Medium平均: {medium_avg:.4f}")
        print(f"   Low平均: {low_avg:.4f}")
        print(f"   差距: {abs(medium_avg - low_avg):.4f}")
        
        if abs(medium_avg - low_avg) < 0.05:
            print(f"\n⚠️  Medium和Low的平均分数非常接近 (差距<0.05)")
            print(f"   这表明这两类问题在检索上没有明显区别")
        
        # 检查是否有重叠
        medium_max = max(medium_scores)
        low_min = min(low_scores)
        
        if medium_max >= low_min:
            print(f"\n⚠️  发现分数重叠:")
            print(f"   Medium最高分: {medium_max:.4f}")
            print(f"   Low最低分: {low_min:.4f}")
            print(f"   说明仅凭分数无法完全区分这两类")

print(f"\n{'='*80}")
print("🎯 建议的下一步行动")
print("="*80)

if all_score_values:
    all_below_high = all(s < THRESHOLD_HIGH for s in all_score_values)
    
    if all_below_high:
        print("\n1️⃣  重新设计测试用例（推荐）")
        print("   - 使用真正'不在合同中'的问题作为Low类别")
        print("   - 例如: '新加坡天气如何?', '附近哪里买家具?'")
        print("\n2️⃣  或者大幅提高HIGH阈值")
        print(f"   - 当前HIGH阈值: {THRESHOLD_HIGH}")
        print(f"   - 建议改为: {global_max + 0.1:.2f} (最高分+0.1)")
        
    else:
        print("\n1️⃣  微调阈值")
        print(f"   - 当前: HIGH<{THRESHOLD_HIGH}, MEDIUM<{THRESHOLD_MEDIUM}")
        
        # 计算建议阈值
        if medium_scores:
            suggested_high = (max(high_scores) + min(medium_scores)) / 2
            print(f"   - 建议HIGH阈值: {suggested_high:.3f}")
        
        if low_scores:
            suggested_medium = (max(medium_scores) + min(low_scores)) / 2
            print(f"   - 建议MEDIUM阈值: {suggested_medium:.3f}")
        
        print("\n2️⃣  或使用LLM二次判断（advanced_confidence_solution.py）")

print(f"\n{'='*80}")