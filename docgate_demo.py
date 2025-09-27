#!/usr/bin/env python3
"""
DocGate Agent 核心功能演示
"""

import sys
import os
sys.path.append('/home/xx/dev/Claude Enhancer 5.0')

from docgate_agent import DocGateAgent

def quick_demo():
    """快速演示核心功能"""
    print("🚀 DocGate Agent - 文档质量分析专家")
    print("=" * 50)

    # 初始化Agent
    docgate = DocGateAgent()

    # 找一个存在的文档文件
    test_files = [
        "/home/xx/dev/Claude Enhancer 5.0/README.md",
        "/home/xx/dev/Claude Enhancer 5.0/CLAUDE.md",
        "/home/xx/dev/Claude Enhancer 5.0/.claude/WORKFLOW.md"
    ]

    target_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            target_file = file_path
            break

    if not target_file:
        print("❌ 未找到测试文档文件")
        return

    print(f"\n📖 分析文档: {os.path.basename(target_file)}")

    # 1. 文档质量分析
    print("\n🔍 1. 文档质量分析")
    try:
        quality_result = docgate.analyze_document_quality(target_file)
        if 'error' not in quality_result:
            print(f"   ✅ 质量评分: {quality_result['overall_score']:.1f}/100")
            print(f"   ✅ 质量等级: {quality_result['quality_level']}")
            print(f"   ✅ 文档类型: {quality_result['document_type']}")

            metrics = quality_result['metrics']
            print(f"   📊 字数: {metrics['word_count']}")
            print(f"   📊 段落数: {metrics['paragraph_count']}")
            print(f"   📊 标题数: {metrics['heading_count']}")
            print(f"   📊 可读性: {metrics['readability_score']:.1f}/100")
            print(f"   📊 结构性: {metrics['structure_score']:.1f}/100")
            print(f"   📊 完整性: {metrics['completeness_score']:.1f}/100")

            print(f"   ⚠️  发现 {len(quality_result['issues'])} 个问题")
            if quality_result['issues']:
                for issue in quality_result['issues'][:2]:  # 只显示前2个
                    print(f"      - {issue['description']}")

            print(f"   💡 生成 {len(quality_result['suggestions'])} 条建议")
            if quality_result['suggestions']:
                for suggestion in quality_result['suggestions'][:2]:  # 只显示前2个
                    print(f"      - {suggestion}")
        else:
            print(f"   ❌ 分析失败: {quality_result['error']}")
    except Exception as e:
        print(f"   ❌ 分析异常: {str(e)}")

    # 2. 自动生成摘要
    print("\n📝 2. 自动生成摘要")
    try:
        summary_result = docgate.generate_document_summary(target_file, max_sentences=2)
        if 'error' not in summary_result:
            print(f"   ✅ 文档标题: {summary_result['title']}")
            print(f"   ✅ 摘要: {summary_result['summary'][:150]}...")
            print(f"   ✅ 关键点: {len(summary_result['key_points'])} 个")
            for point in summary_result['key_points'][:3]:  # 只显示前3个
                print(f"      - {point}")
            print(f"   ✅ 预估阅读时间: {summary_result['estimated_reading_time']}")
        else:
            print(f"   ❌ 摘要生成失败: {summary_result['error']}")
    except Exception as e:
        print(f"   ❌ 摘要生成异常: {str(e)}")

    # 3. 文档覆盖度分析
    print("\n📊 3. 文档覆盖度分析")
    try:
        project_path = os.path.dirname(target_file)
        coverage_result = docgate.analyze_documentation_coverage(project_path)
        if 'error' not in coverage_result:
            print(f"   ✅ 代码文件数: {coverage_result['total_code_files']}")
            print(f"   ✅ 文档文件数: {coverage_result['total_doc_files']}")
            print(f"   ✅ 覆盖率: {coverage_result['coverage_percentage']:.1f}%")

            missing = coverage_result.get('missing_documentation', [])
            if missing:
                print(f"   ⚠️  缺失的标准文档: {', '.join(missing[:3])}")

            recommendations = coverage_result.get('recommendations', [])
            if recommendations:
                print(f"   💡 建议:")
                for rec in recommendations[:2]:
                    print(f"      - {rec}")
        else:
            print(f"   ❌ 覆盖度分析失败: {coverage_result['error']}")
    except Exception as e:
        print(f"   ❌ 覆盖度分析异常: {str(e)}")

    # 4. 相似度检测（简化版）
    print("\n🔍 4. 相似度检测能力演示")
    try:
        # 查找多个文档文件
        doc_files = []
        for root, dirs, files in os.walk(os.path.dirname(target_file)):
            for file in files:
                if file.endswith('.md'):
                    doc_files.append(os.path.join(root, file))
                if len(doc_files) >= 3:  # 只取前3个进行演示
                    break
            if len(doc_files) >= 3:
                break

        if len(doc_files) >= 2:
            similarity_results = docgate.detect_document_similarity(doc_files[:2])
            if similarity_results:
                result = similarity_results[0]
                print(f"   ✅ 比较了2个文档")
                print(f"   ✅ 相似度: {result.similarity_ratio:.1%}")
                print(f"   ✅ 相似度类型: {result.similarity_type}")
                print(f"   ✅ 共同行数: {len(result.common_lines)}")
            else:
                print(f"   ❌ 相似度检测失败")
        else:
            print(f"   ⚠️  文档文件不足，跳过相似度检测")
    except Exception as e:
        print(f"   ❌ 相似度检测异常: {str(e)}")

    print(f"\n🎉 DocGate Agent 核心功能演示完成!")
    print(f"\n💡 核心能力总结:")
    print(f"   ✅ 文档质量分析 - 多维度评估文档质量")
    print(f"   ✅ 自动生成摘要 - 提取关键信息生成摘要")
    print(f"   ✅ 相似度检测 - 识别重复和相似内容")
    print(f"   ✅ 覆盖度分析 - 评估项目文档完整性")
    print(f"   ✅ 改进建议 - 提供具体的优化建议")
    print(f"\n🔧 技术特点:")
    print(f"   - 独立运行，不调用其他Agent")
    print(f"   - 支持Markdown、RST、TXT等格式")
    print(f"   - 基于多种指标的综合质量评估")
    print(f"   - 可配置的质量标准和阈值")

if __name__ == "__main__":
    quick_demo()