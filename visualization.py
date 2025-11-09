# demo_visualize.py
"""
用于演示的RAG流程可视化脚本
展示：文档切块、向量化、检索过程
"""

from src.loader import load_and_chunk_pdf
from src.retriever import search
from src.config import CHUNK_SIZE, CHUNK_OVERLAP

def visualize_chunking():
    """可视化展示文档切块过程"""
    print("="*80)
    print("📄 STEP 1: 文档切块演示")
    print("="*80)
    
    pdf_path = "./data/tenancy_agreement.pdf"
    chunks = load_and_chunk_pdf(pdf_path)
    
    print(f"\n 切块统计：")
    print(f"   原始PDF: 10页")
    print(f"   生成chunks: {len(chunks)}个")
    print(f"   Chunk大小: {CHUNK_SIZE} tokens")
    print(f"   重叠部分: {CHUNK_OVERLAP} tokens")
    print(f"   平均每页: {len(chunks)//6} chunks")
    
    # 按页统计
    page_counts = {}
    for chunk in chunks:
        page = chunk.metadata.get('page', 'Unknown')
        page_counts[page] = page_counts.get(page, 0) + 1
    
    print(f"\n 每页的chunk分布：")
    for page in sorted(page_counts.keys()):
        bar = "█" * page_counts[page]
        print(f"   Page {page}: {bar} ({page_counts[page]} chunks)")
    
    # 展示几个chunk的例子
    print(f"\n Chunk示例（前3个）：")
    print("-"*80)
    for i in range(min(3, len(chunks))):
        chunk = chunks[i]
        page = chunk.metadata.get('page', '?')
        text_preview = chunk.page_content[:150].replace('\n', ' ')
        
        print(f"\n【Chunk {i+1}】")
        print(f"   Page: {page}")
        print(f"   长度: {len(chunk.page_content)} 字符")
        print(f"   预览: {text_preview}...")
    
    print("\n" + "="*80)
    return chunks


def visualize_retrieval(query):
    """可视化展示检索过程"""
    print("\n" + "="*80)
    print("🔍 STEP 2: 检索过程演示")
    print("="*80)
    
    print(f"\n❓ 用户问题: \"{query}\"")
    print("\n  正在检索...")
    
    # 执行检索
    results = search(query, top_k=5, with_scores=True)
    
    print(f"\n 找到 {len(results)} 个相关chunks")
    
    # 显示检索结果
    print("\n 检索结果（按相似度排序）：")
    print("-"*80)
    
    for i, doc in enumerate(results, 1):
        score = doc.metadata.get('score', 0)
        page = doc.metadata.get('page', '?')
        text_preview = doc.page_content[:100].replace('\n', ' ')
        
        # 相似度可视化
        similarity = max(0, 1 - (score / 2))  # 转换为0-1的相似度
        bar_length = int(similarity * 30)
        bar = "█" * bar_length + "░" * (30 - bar_length)
        
        # 置信度判断
        if score < 0.70:
            confidence = "🟢 HIGH"
        elif score < 0.90:
            confidence = "🟡 MEDIUM"
        else:
            confidence = "🔴 LOW"
        
        print(f"\n【结果 {i}】")
        print(f"   Score: {score:.3f}  {confidence}")
        print(f"   相似度: {bar} {similarity*100:.1f}%")
        print(f"   来源: Page {page}")
        print(f"   内容: {text_preview}...")
    
    # 显示最终决策
    best_score = results[0].metadata.get('score', 1.0)
    print("\n" + "-"*80)
    print("🎯 最终决策：")
    if best_score < 0.70:
        print("   ✅ 置信度: HIGH")
        print("   📝 行动: 直接生成答案")
    elif best_score < 0.90:
        print("   ⚠️  置信度: MEDIUM")
        print("   📝 行动: 显示条款 + 建议确认")
    else:
        print("   ❌ 置信度: LOW")
        print("   📝 行动: 告知不在合同范围，建议人工支持")
    
    print("="*80)
    return results


def compare_queries():
    """对比不同类型的问题"""
    print("\n" + "="*80)
    print(" STEP 3: 三类问题对比")
    print("="*80)
    
    test_cases = [
        ("When is my rent due?", "HIGH - 合同明确说明"),
        ("Can I paint the walls?", "MEDIUM - 需要解释"),
        ("How to negotiate rent reduction?", "LOW - 合同未提及")
    ]
    
    results_summary = []
    
    for query, expected in test_cases:
        print(f"\n{'='*80}")
        print(f"问题: \"{query}\"")
        print(f"预期: {expected}")
        print("-"*80)
        
        results = search(query, top_k=1, with_scores=True)
        
        if results:
            score = results[0].metadata.get('score', 1.0)
            page = results[0].metadata.get('page', '?')
            
            if score < 0.70:
                actual = "HIGH"
                symbol = "🟢"
            elif score < 0.90:
                actual = "MEDIUM"
                symbol = "🟡"
            else:
                actual = "LOW"
                symbol = "🔴"
            
            print(f"实际: {symbol} {actual} (score: {score:.3f})")
            print(f"来源: Page {page}")
            
            results_summary.append({
                'query': query,
                'expected': expected.split(' - ')[0],
                'actual': actual,
                'score': score,
                'page': page
            })
        else:
            print("❌ 未找到结果")
    
    # 总结表格
    print("\n" + "="*80)
    print("📋 结果汇总")
    print("="*80)
    print(f"\n{'问题':<40} {'预期':<10} {'实际':<10} {'分数':<8} {'页码'}")
    print("-"*80)
    
    for r in results_summary:
        match = "✅" if r['expected'] == r['actual'] else "❌"
        print(f"{r['query']:<40} {r['expected']:<10} {r['actual']:<10} {r['score']:<8.3f} Page {r['page']} {match}")
    
    print("="*80)


def show_vector_concept():
    """展示向量化的概念（简化版）"""
    print("\n" + "="*80)
    print("🔮 附加: 向量化概念演示")
    print("="*80)
    
    print("\n📚 什么是向量化？")
    print("   将文字转换为数字，用于计算相似度")
    
    print("\n🔢 向量维度: 1536维")
    print("   每个chunk → [0.123, -0.456, 0.789, ..., 0.234]")
    
    print("\n📐 相似度计算: Cosine距离")
    print("   距离越小 = 越相似")
    print("   0.0 = 完全相同")
    print("   2.0 = 完全不相关")
    
    print("\n💡 为什么有用？")
    print("   '租金' 和 'rent' → 向量很接近")
    print("   '租金' 和 '猫' → 向量相距很远")
    
    print("="*80)


def full_demo():
    """完整演示流程"""
    print("\n" + "🎬"*40)
    print("RAG系统完整演示")
    print("🎬"*40)
    
    # Step 1: 文档切块
    chunks = visualize_chunking()
    
    input("\n按Enter继续...")
    
    # Step 2: 检索演示
    demo_query = "When is my rent due each month?"
    visualize_retrieval(demo_query)
    
    input("\n按Enter继续...")
    
    # Step 3: 对比不同问题
    compare_queries()
    
    input("\n按Enter继续...")
    
    # Step 4: 向量化概念
    show_vector_concept()
    
    print("\n" + "🎬"*40)
    print("演示结束！")
    print("🎬"*40)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--chunk":
            visualize_chunking()
        elif sys.argv[1] == "--search":
            query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "When is rent due?"
            visualize_retrieval(query)
        elif sys.argv[1] == "--compare":
            compare_queries()
        elif sys.argv[1] == "--vector":
            show_vector_concept()
        else:
            print("用法:")
            print("  python demo_visualize.py              # 完整演示")
            print("  python demo_visualize.py --chunk      # 只看切块")
            print("  python demo_visualize.py --search     # 只看检索")
            print("  python demo_visualize.py --compare    # 只看对比")
            print("  python demo_visualize.py --vector     # 只看向量概念")
    else:
        full_demo()