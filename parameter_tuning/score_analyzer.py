# parameter_tuning/score_analyzer.py
"""
分数分布分析工具
在进行网格搜索前，先分析当前系统的分数分布特征
这样可以更有针对性地设置阈值范围

运行方式：
python parameter_tuning/score_analyzer.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retriever import search
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

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


def analyze_score_distribution():
    """分析分数分布"""
    print("\n" + "="*80)
    print("📊 分数分布分析")
    print("="*80)
    print("目的: 了解不同类别问题的检索分数分布，为阈值设置提供依据\n")
    
    pdf_path = "./data/tenancy_agreement.pdf"
    
    # 收集所有分数
    score_data = {
        "High": [],
        "Medium": [],
        "Low": []
    }
    
    detailed_results = []
    
    print("🔍 正在检索所有测试问题...")
    for expected_confidence, questions in TEST_CASES.items():
        print(f"\n处理 {expected_confidence} 类别...")
        for question in questions:
            try:
                results = search(
                    question,
                    top_k=5,
                    with_scores=True,
                    active_pdf_path=pdf_path
                )
                
                if results:
                    top_score = results[0].metadata.get('score', 1.0)
                    score_data[expected_confidence].append(top_score)
                    
                    # 计算分数差距
                    gap = 0
                    if len(results) >= 2:
                        gap = results[1].metadata.get('score', 1.0) - top_score
                    
                    detailed_results.append({
                        'question': question,
                        'expected_class': expected_confidence,
                        'top_score': top_score,
                        'score_gap': gap,
                        'top5_scores': [r.metadata.get('score', 1.0) for r in results[:5]]
                    })
                    
                    print(f"  ✓ {question[:50]}... → {top_score:.3f}")
                else:
                    print(f"  ✗ {question[:50]}... → 无结果")
                    
            except Exception as e:
                print(f"  ✗ {question[:50]}... → 错误: {str(e)}")
    
    # 统计分析
    print("\n" + "="*80)
    print("📈 统计结果")
    print("="*80)
    
    statistics = {}
    for cls, scores in score_data.items():
        if scores:
            statistics[cls] = {
                'min': float(np.min(scores)),
                'max': float(np.max(scores)),
                'mean': float(np.mean(scores)),
                'median': float(np.median(scores)),
                'std': float(np.std(scores)),
                'q25': float(np.percentile(scores, 25)),
                'q75': float(np.percentile(scores, 75)),
                'count': len(scores)
            }
            
            print(f"\n【{cls}类别】（{len(scores)}个问题）")
            print(f"  最小值: {statistics[cls]['min']:.3f}")
            print(f"  25分位: {statistics[cls]['q25']:.3f}")
            print(f"  中位数: {statistics[cls]['median']:.3f}")
            print(f"  平均值: {statistics[cls]['mean']:.3f}")
            print(f"  75分位: {statistics[cls]['q75']:.3f}")
            print(f"  最大值: {statistics[cls]['max']:.3f}")
            print(f"  标准差: {statistics[cls]['std']:.3f}")
    
    # 推荐阈值
    print("\n" + "="*80)
    print("💡 阈值推荐")
    print("="*80)
    
    if score_data['High'] and score_data['Medium']:
        # 基于数据推荐阈值
        high_max = statistics['High']['max']
        medium_min = statistics['Medium']['min']
        medium_max = statistics['Medium']['max']
        
        # 推荐策略：
        # HIGH阈值 = High类别的75分位 + 10%安全边际
        # MEDIUM阈值 = Medium类别的75分位 + 10%安全边际
        
        recommended_high = statistics['High']['q75'] * 1.1
        recommended_medium = statistics['Medium']['q75'] * 1.1
        
        print(f"\n基于数据分布的推荐值:")
        print(f"  THRESHOLD_HIGH:   {recommended_high:.3f}")
        print(f"  THRESHOLD_MEDIUM: {recommended_medium:.3f}")
        
        print(f"\n说明:")
        print(f"  - High类别最大值: {high_max:.3f}")
        print(f"  - Medium类别范围: {medium_min:.3f} - {medium_max:.3f}")
        print(f"  - 推荐HIGH阈值覆盖了{statistics['High']['q75']}分位的High问题")
        print(f"  - 推荐MEDIUM阈值覆盖了{statistics['Medium']['q75']}分位的Medium问题")
    
    # 分析分数差距
    print("\n" + "="*80)
    print("📏 分数差距分析")
    print("="*80)
    
    gaps = [r['score_gap'] for r in detailed_results if r['score_gap'] > 0]
    if gaps:
        print(f"\n分数差距统计:")
        print(f"  平均差距: {np.mean(gaps):.3f}")
        print(f"  中位差距: {np.median(gaps):.3f}")
        print(f"  最小差距: {np.min(gaps):.3f}")
        print(f"  最大差距: {np.max(gaps):.3f}")
        
        # 推荐gap阈值
        recommended_gap = float(np.percentile(gaps, 25))  # 25分位作为阈值
        print(f"\n推荐 SCORE_GAP_THRESHOLD: {recommended_gap:.3f}")
        print(f"  （当差距小于此值时，视为模糊结果）")
    
    # 生成可视化
    print("\n📊 生成可视化图表...")
    _create_visualization(score_data, statistics, detailed_results)
    
    # 保存结果
    output = {
        'analysis_time': str(np.datetime64('now')),
        'statistics': statistics,
        'detailed_results': detailed_results,
        'recommended_thresholds': {
            'threshold_high': float(recommended_high) if 'recommended_high' in locals() else None,
            'threshold_medium': float(recommended_medium) if 'recommended_medium' in locals() else None,
            'score_gap_threshold': float(recommended_gap) if 'recommended_gap' in locals() else None
        }
    }
    
    output_file = 'parameter_tuning/score_analysis.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 分析结果已保存: {output_file}")
    
    return output


def _create_visualization(score_data, statistics, detailed_results):
    """创建可视化图表"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('检索分数分布分析', fontsize=16, fontweight='bold')
    
    # 1. 箱线图
    ax1 = axes[0, 0]
    data_to_plot = [score_data['High'], score_data['Medium'], score_data['Low']]
    labels = ['High', 'Medium', 'Low']
    colors = ['#51cf66', '#ffd43b', '#ff6b6b']
    
    bp = ax1.boxplot(data_to_plot, labels=labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    
    ax1.set_ylabel('检索分数', fontsize=12)
    ax1.set_title('分数分布箱线图', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # 2. 直方图
    ax2 = axes[0, 1]
    for cls, scores in score_data.items():
        if scores:
            ax2.hist(scores, bins=20, alpha=0.5, label=cls)
    
    ax2.set_xlabel('检索分数', fontsize=12)
    ax2.set_ylabel('频数', fontsize=12)
    ax2.set_title('分数分布直方图', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(alpha=0.3)
    
    # 3. 散点图
    ax3 = axes[1, 0]
    for cls, color in zip(['High', 'Medium', 'Low'], colors):
        cls_data = [r for r in detailed_results if r['expected_class'] == cls]
        scores = [r['top_score'] for r in cls_data]
        gaps = [r['score_gap'] for r in cls_data]
        ax3.scatter(scores, gaps, alpha=0.6, label=cls, color=color, s=100)
    
    ax3.set_xlabel('Top-1 分数', fontsize=12)
    ax3.set_ylabel('分数差距 (Top2-Top1)', fontsize=12)
    ax3.set_title('分数 vs 差距', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(alpha=0.3)
    
    # 4. 统计表格
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = []
    table_data.append(['类别', '最小', '中位', '平均', '最大'])
    for cls in ['High', 'Medium', 'Low']:
        if cls in statistics:
            s = statistics[cls]
            table_data.append([
                cls,
                f"{s['min']:.3f}",
                f"{s['median']:.3f}",
                f"{s['mean']:.3f}",
                f"{s['max']:.3f}"
            ])
    
    table = ax4.table(cellText=table_data, cellLoc='center',
                     loc='center', bbox=[0, 0.3, 1, 0.6])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # 设置表头样式
    for i in range(5):
        table[(0, i)].set_facecolor('#e9ecef')
        table[(0, i)].set_text_props(weight='bold')
    
    ax4.set_title('统计摘要', fontsize=14, fontweight='bold', pad=20)
    
    plt.tight_layout()
    output_file = 'parameter_tuning/score_distribution.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"✅ 可视化图表已保存: {output_file}")


if __name__ == "__main__":
    print("\n🔍 开始分析检索分数分布...")
    result = analyze_score_distribution()
    print("\n✅ 分析完成！")
    print("\n💡 下一步:")
    print("  1. 查看生成的图表: parameter_tuning/score_distribution.png")
    print("  2. 根据推荐阈值运行网格搜索: python parameter_tuning/grid_search.py --quick")