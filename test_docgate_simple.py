#!/usr/bin/env python3
"""
简化版DocGate Agent测试
"""

import sys
import os
sys.path.append('/home/xx/dev/Claude Enhancer 5.0')

from docgate_agent import DocGateAgent

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 DocGate Agent 基本功能测试")
    print("=" * 40)

    # 初始化Agent
    docgate = DocGateAgent()

    # 测试1: 分析README文档
    readme_path = "/home/xx/dev/Claude Enhancer 5.0/README.md"
    if os.path.exists(readme_path):
        print(f"\n📖 测试1: 分析 {readme_path}")

        # 质量分析
        quality_result = docgate.analyze_document_quality(readme_path)
        if 'error' not in quality_result:
            print(f"✅ 质量评分: {quality_result['overall_score']:.1f}/100")
            print(f"✅ 质量等级: {quality_result['quality_level']}")
            print(f"✅ 文档类型: {quality_result['document_type']}")

            metrics = quality_result['metrics']
            print(f"✅ 字数: {metrics['word_count']}")
            print(f"✅ 段落数: {metrics['paragraph_count']}")
            print(f"✅ 标题数: {metrics['heading_count']}")

            print(f"✅ 发现 {len(quality_result['issues'])} 个问题")
            print(f"✅ 生成 {len(quality_result['suggestions'])} 条建议")
        else:
            print(f"❌ 质量分析失败: {quality_result['error']}")

    # 测试2: 生成摘要
    if os.path.exists(readme_path):
        print(f"\n📝 测试2: 生成摘要")

        summary_result = docgate.generate_document_summary(readme_path, max_sentences=2)
        if 'error' not in summary_result:
            print(f"✅ 标题: {summary_result['title']}")
            print(f"✅ 摘要: {summary_result['summary']}")
            print(f"✅ 关键点数量: {len(summary_result['key_points'])}")
            print(f"✅ 预估阅读时间: {summary_result['estimated_reading_time']}")
        else:
            print(f"❌ 摘要生成失败: {summary_result['error']}")

    # 测试3: 查找文档文件
    print(f"\n🔍 测试3: 查找文档文件")
    doc_files = docgate._find_documentation_files(os.path.dirname(readme_path))
    print(f"✅ 找到 {len(doc_files)} 个文档文件")
    for doc_file in doc_files[:5]:  # 只显示前5个
        print(f"   - {os.path.basename(doc_file)}")

    # 测试4: 批量分析（小规模）
    print(f"\n📊 测试4: 批量分析")
    if len(doc_files) > 0:
        # 只分析前3个文档以避免超时
        sample_files = doc_files[:3]
        batch_result = docgate.batch_analyze_documents(['*.md'])

        if 'error' not in batch_result:
            stats = batch_result.get('summary_statistics', {})
            if stats:
                print(f"✅ 分析了 {stats.get('total_documents', 0)} 个文档")
                print(f"✅ 平均质量: {stats.get('average_quality', 0):.1f}/100")
                print(f"✅ 最高质量: {stats.get('highest_quality', 0):.1f}/100")
                print(f"✅ 最低质量: {stats.get('lowest_quality', 0):.1f}/100")

            print(f"✅ 生成了 {len(batch_result.get('global_recommendations', []))} 条全局建议")
        else:
            print(f"❌ 批量分析失败: {batch_result['error']}")

    print(f"\n🎉 基本功能测试完成!")

if __name__ == "__main__":
    test_basic_functionality()