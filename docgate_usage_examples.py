#!/usr/bin/env python3
"""
DocGate Agent 使用示例
展示各种实际使用场景和最佳实践
"""

import sys
import os
import json
sys.path.append('/home/xx/dev/Claude Enhancer 5.0')

from docgate_agent import DocGateAgent

def example_single_document_analysis():
    """示例1: 单个文档质量分析"""
    print("📋 示例1: 单个文档质量分析")
    print("-" * 40)

    docgate = DocGateAgent()

    # 分析README文档
    readme_path = "/home/xx/dev/Claude Enhancer 5.0/README.md"
    if os.path.exists(readme_path):
        result = docgate.analyze_document_quality(readme_path)

        if 'error' not in result:
            print(f"📊 质量分析结果:")
            print(f"   文档路径: {result['file_path']}")
            print(f"   文档类型: {result['document_type']}")
            print(f"   总体评分: {result['overall_score']:.1f}/100")
            print(f"   质量等级: {result['quality_level']}")

            metrics = result['metrics']
            print(f"\n📈 详细指标:")
            print(f"   字数: {metrics['word_count']}")
            print(f"   段落数: {metrics['paragraph_count']}")
            print(f"   标题数: {metrics['heading_count']}")
            print(f"   链接数: {metrics['link_count']}")
            print(f"   代码块数: {metrics['code_block_count']}")
            print(f"   可读性: {metrics['readability_score']:.1f}/100")
            print(f"   结构性: {metrics['structure_score']:.1f}/100")
            print(f"   完整性: {metrics['completeness_score']:.1f}/100")

            print(f"\n⚠️ 质量问题 ({len(result['issues'])}个):")
            for i, issue in enumerate(result['issues'][:3], 1):
                print(f"   {i}. [{issue['severity']}] {issue['description']}")
                print(f"      建议: {issue['suggestion']}")

            print(f"\n💡 改进建议:")
            for i, suggestion in enumerate(result['suggestions'], 1):
                print(f"   {i}. {suggestion}")
        else:
            print(f"❌ 分析失败: {result['error']}")
    else:
        print(f"❌ 文件不存在: {readme_path}")

def example_document_summary():
    """示例2: 文档摘要生成"""
    print("\n📝 示例2: 文档摘要生成")
    print("-" * 40)

    docgate = DocGateAgent()

    # 生成CLAUDE.md摘要
    claude_md_path = "/home/xx/dev/Claude Enhancer 5.0/CLAUDE.md"
    if os.path.exists(claude_md_path):
        result = docgate.generate_document_summary(claude_md_path, max_sentences=3)

        if 'error' not in result:
            print(f"📖 文档摘要:")
            print(f"   标题: {result['title']}")
            print(f"   摘要: {result['summary']}")
            print(f"   阅读时间: {result['estimated_reading_time']}")
            print(f"   字数: {result['word_count']}")

            print(f"\n🔑 关键点 ({len(result['key_points'])}个):")
            for i, point in enumerate(result['key_points'][:5], 1):
                print(f"   {i}. {point}")

            if result['metadata']:
                print(f"\n📋 文档元数据:")
                for key, value in result['metadata'].items():
                    print(f"   {key}: {value}")
        else:
            print(f"❌ 摘要生成失败: {result['error']}")
    else:
        print(f"❌ 文件不存在: {claude_md_path}")

def example_similarity_detection():
    """示例3: 文档相似度检测"""
    print("\n🔍 示例3: 文档相似度检测")
    print("-" * 40)

    docgate = DocGateAgent()

    # 查找多个.md文档进行比较
    doc_files = []
    project_root = "/home/xx/dev/Claude Enhancer 5.0"

    for file in ['README.md', 'CLAUDE.md', '.claude/WORKFLOW.md']:
        file_path = os.path.join(project_root, file)
        if os.path.exists(file_path):
            doc_files.append(file_path)

    if len(doc_files) >= 2:
        # 只比较前3个文档以节省时间
        results = docgate.detect_document_similarity(doc_files[:3])

        print(f"📊 相似度检测结果:")
        print(f"   比较了 {len(doc_files[:3])} 个文档")

        for i, result in enumerate(results[:3], 1):
            doc_a = os.path.basename(result.document_a)
            doc_b = os.path.basename(result.document_b)
            print(f"\n   {i}. {doc_a} vs {doc_b}")
            print(f"      相似度: {result.similarity_ratio:.1%}")
            print(f"      相似度类型: {result.similarity_type}")
            print(f"      共同行数: {len(result.common_lines)}")

            if result.common_lines and len(result.common_lines) > 0:
                print(f"      示例共同内容: {result.common_lines[0][:50]}...")
    else:
        print(f"❌ 找不到足够的文档文件进行比较")

def example_documentation_coverage():
    """示例4: 文档覆盖度分析"""
    print("\n📊 示例4: 文档覆盖度分析")
    print("-" * 40)

    docgate = DocGateAgent()

    # 分析项目文档覆盖度
    project_path = "/home/xx/dev/Claude Enhancer 5.0"
    result = docgate.analyze_documentation_coverage(project_path)

    if 'error' not in result:
        print(f"📈 覆盖度分析结果:")
        print(f"   项目路径: {result['project_path']}")
        print(f"   代码文件数: {result['total_code_files']}")
        print(f"   文档文件数: {result['total_doc_files']}")
        print(f"   覆盖率: {result['coverage_percentage']:.1f}%")

        coverage_details = result['coverage_details']
        print(f"\n📋 覆盖详情:")
        print(f"   已文档化文件: {coverage_details['documented_files']}")
        print(f"   未文档化文件: {coverage_details['undocumented_files']}")

        missing_docs = result['missing_documentation']
        if missing_docs:
            print(f"\n⚠️ 缺失的标准文档 ({len(missing_docs)}个):")
            for doc in missing_docs:
                print(f"   - {doc}")

        print(f"\n💡 改进建议:")
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"   {i}. {rec}")

        # 文档结构分析
        doc_structure = result['documentation_structure']
        print(f"\n📁 文档结构分析:")
        print(f"   总文档数: {doc_structure['total_files']}")

        print(f"   按类型分布:")
        for doc_type, count in doc_structure['by_type'].items():
            print(f"     {doc_type}: {count}")
    else:
        print(f"❌ 覆盖度分析失败: {result['error']}")

def example_batch_analysis():
    """示例5: 批量文档分析"""
    print("\n🔄 示例5: 批量文档分析")
    print("-" * 40)

    docgate = DocGateAgent()

    # 批量分析Markdown文档
    result = docgate.batch_analyze_documents(['*.md'])

    if 'error' not in result:
        analyzed_files = result['analyzed_files']
        print(f"📊 批量分析结果:")
        print(f"   分析文件数: {len(analyzed_files)}")

        # 统计信息
        stats = result.get('summary_statistics', {})
        if stats:
            print(f"\n📈 质量统计:")
            print(f"   平均质量: {stats['average_quality']:.1f}/100")
            print(f"   质量中位数: {stats['median_quality']:.1f}/100")
            print(f"   最高质量: {stats['highest_quality']:.1f}/100")
            print(f"   最低质量: {stats['lowest_quality']:.1f}/100")
            print(f"   标准差: {stats['quality_std_dev']:.1f}")

        # 质量分布
        quality_dist = result.get('quality_distribution', {})
        if quality_dist:
            print(f"\n📊 质量分布:")
            for level, count in quality_dist.items():
                print(f"   {level}: {count} 个文档")

        # 常见问题
        common_issues = result.get('common_issues', [])
        if common_issues:
            print(f"\n⚠️ 常见问题:")
            for issue_analysis in common_issues:
                if issue_analysis['type'] == 'most_common_issues':
                    print(f"   问题类型分布:")
                    for issue_type, count in list(issue_analysis['data'].items())[:3]:
                        print(f"     {issue_type}: {count}次")

        # 全局建议
        global_recs = result.get('global_recommendations', [])
        if global_recs:
            print(f"\n💡 全局改进建议:")
            for i, rec in enumerate(global_recs, 1):
                print(f"   {i}. {rec}")

        # 显示质量最高和最低的文档
        if analyzed_files:
            sorted_files = sorted(analyzed_files, key=lambda x: x['overall_score'], reverse=True)

            print(f"\n🏆 质量最高的文档:")
            best = sorted_files[0]
            print(f"   {os.path.basename(best['file_path'])}: {best['overall_score']:.1f}/100")

            print(f"\n📉 质量最低的文档:")
            worst = sorted_files[-1]
            print(f"   {os.path.basename(worst['file_path'])}: {worst['overall_score']:.1f}/100")
    else:
        print(f"❌ 批量分析失败: {result['error']}")

def example_generate_quality_report():
    """示例6: 生成质量报告"""
    print("\n📄 示例6: 生成质量报告")
    print("-" * 40)

    docgate = DocGateAgent()

    # 生成项目质量报告
    try:
        report_file = docgate.generate_quality_report()
        print(f"✅ 质量报告已生成:")
        print(f"   文件路径: {report_file}")

        # 显示报告文件大小
        if os.path.exists(report_file):
            file_size = os.path.getsize(report_file)
            print(f"   文件大小: {file_size} bytes")

            # 显示报告前几行
            with open(report_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"   报告内容预览:")
                for line in lines[:5]:
                    print(f"     {line.rstrip()}")
                if len(lines) > 5:
                    print(f"     ... (共{len(lines)}行)")

        print(f"\n💡 建议:")
        print(f"   - 使用Markdown查看器打开报告文件")
        print(f"   - 定期生成报告跟踪文档质量变化")
        print(f"   - 根据报告建议改进文档质量")

    except Exception as e:
        print(f"❌ 报告生成失败: {str(e)}")

def example_custom_configuration():
    """示例7: 自定义配置"""
    print("\n⚙️ 示例7: 自定义配置")
    print("-" * 40)

    docgate = DocGateAgent()

    # 显示当前配置
    print(f"📋 当前质量标准:")
    for key, value in docgate.quality_standards.items():
        print(f"   {key}: {value}")

    # 自定义配置
    print(f"\n🔧 自定义配置示例:")
    custom_standards = {
        'min_word_count': 200,      # 提高最小字数要求
        'similarity_threshold': 0.7, # 降低相似度阈值
        'readability_target': 80,   # 提高可读性目标
        'min_headings': 3           # 要求更多标题
    }

    docgate.quality_standards.update(custom_standards)

    print(f"✅ 已更新配置:")
    for key, value in custom_standards.items():
        print(f"   {key}: {value}")

    # 用新配置重新分析
    readme_path = "/home/xx/dev/Claude Enhancer 5.0/README.md"
    if os.path.exists(readme_path):
        result = docgate.analyze_document_quality(readme_path)
        if 'error' not in result:
            print(f"\n📊 使用新配置的分析结果:")
            print(f"   质量评分: {result['overall_score']:.1f}/100")
            print(f"   质量等级: {result['quality_level']}")
            print(f"   发现问题: {len(result['issues'])}个")

def main():
    """运行所有示例"""
    print("🚀 DocGate Agent 使用示例")
    print("=" * 50)

    try:
        # 运行所有示例
        example_single_document_analysis()
        example_document_summary()
        example_similarity_detection()
        example_documentation_coverage()
        example_batch_analysis()
        example_generate_quality_report()
        example_custom_configuration()

        print(f"\n🎉 所有示例执行完成!")
        print(f"\n📚 更多信息:")
        print(f"   - 查看 DOCGATE_AGENT_README.md 了解详细文档")
        print(f"   - 查看 docgate_agent.py 了解源码实现")
        print(f"   - 使用 python3 docgate_demo.py 运行快速演示")

    except KeyboardInterrupt:
        print(f"\n⏹️ 用户中断执行")
    except Exception as e:
        print(f"\n❌ 执行出错: {str(e)}")

if __name__ == "__main__":
    main()