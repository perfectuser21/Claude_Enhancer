#!/usr/bin/env python3
"""
DocGate Agent 性能测试
测试不同规模文档的处理性能
"""

import sys
import os
import time
import tempfile
from pathlib import Path
sys.path.append('/home/xx/dev/Claude Enhancer 5.0')

from docgate_agent import DocGateAgent

def create_test_document(word_count: int, title: str = "Test Document") -> str:
    """创建测试文档"""
    content = f"# {title}\n\n"

    # 生成指定字数的内容
    words_per_paragraph = 50
    paragraphs_needed = max(1, word_count // words_per_paragraph)

    sample_text = """
    This is a sample paragraph that demonstrates typical documentation content.
    It includes technical terms, explanations, and various sentence structures
    that would be found in real documentation. The content covers features,
    implementation details, usage examples, and best practices.
    """

    sample_words = sample_text.split()
    current_word_count = 0

    for i in range(paragraphs_needed):
        content += f"\n## Section {i+1}\n\n"

        paragraph_words = []
        while len(paragraph_words) < words_per_paragraph and current_word_count < word_count:
            word_index = current_word_count % len(sample_words)
            paragraph_words.append(sample_words[word_index])
            current_word_count += 1

        content += " ".join(paragraph_words) + "\n\n"

        if current_word_count >= word_count:
            break

    # 添加一些结构元素
    content += """
## Features

- Feature one with detailed explanation
- Feature two with code examples
- Feature three with performance metrics

## Code Example

```python
def example_function():
    return "Hello, World!"
```

## Links

- [Documentation](https://example.com/docs)
- [GitHub Repository](https://github.com/example/repo)

## Table

| Feature | Status | Notes |
|---------|--------|-------|
| Quality | ✅ | High |
| Speed   | ✅ | Fast |
| Memory  | ⚠️  | Medium |
"""

    return content

def performance_test_single_document():
    """测试单文档分析性能"""
    print("📊 单文档分析性能测试")
    print("-" * 40)

    docgate = DocGateAgent()

    # 测试不同大小的文档
    test_sizes = [100, 500, 1000, 2000, 5000]  # 字数

    results = []

    for word_count in test_sizes:
        print(f"\n📝 测试 {word_count} 字文档:")

        # 创建测试文档
        content = create_test_document(word_count, f"Test Doc {word_count} words")

        # 写入临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_file = f.name

        try:
            # 测试质量分析
            start_time = time.time()
            quality_result = docgate.analyze_document_quality(temp_file)
            quality_time = time.time() - start_time

            # 测试摘要生成
            start_time = time.time()
            summary_result = docgate.generate_document_summary(temp_file)
            summary_time = time.time() - start_time

            if 'error' not in quality_result and 'error' not in summary_result:
                print(f"   ✅ 质量分析: {quality_time:.3f}s (评分: {quality_result['overall_score']:.1f})")
                print(f"   ✅ 摘要生成: {summary_time:.3f}s")

                results.append({
                    'word_count': word_count,
                    'quality_time': quality_time,
                    'summary_time': summary_time,
                    'total_time': quality_time + summary_time,
                    'quality_score': quality_result['overall_score']
                })
            else:
                print(f"   ❌ 分析失败")

        finally:
            # 清理临时文件
            os.unlink(temp_file)

    # 分析性能趋势
    if results:
        print(f"\n📈 性能分析:")
        print(f"   最快分析: {min(r['total_time'] for r in results):.3f}s")
        print(f"   最慢分析: {max(r['total_time'] for r in results):.3f}s")

        # 计算处理速度（字/秒）
        speeds = [r['word_count'] / r['total_time'] for r in results]
        avg_speed = sum(speeds) / len(speeds)
        print(f"   平均处理速度: {avg_speed:.0f} 字/秒")

    return results

def performance_test_batch_processing():
    """测试批量处理性能"""
    print("\n🔄 批量处理性能测试")
    print("-" * 40)

    docgate = DocGateAgent()

    # 创建多个测试文档
    test_files = []
    temp_dir = tempfile.mkdtemp()

    try:
        # 创建不同大小的文档
        for i in range(5):
            word_count = 200 + i * 100  # 200, 300, 400, 500, 600字
            content = create_test_document(word_count, f"Batch Test Doc {i+1}")

            file_path = os.path.join(temp_dir, f"test_doc_{i+1}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            test_files.append(file_path)

        print(f"📝 创建了 {len(test_files)} 个测试文档")

        # 测试批量分析
        start_time = time.time()
        batch_result = docgate.batch_analyze_documents(['*.md'])
        batch_time = time.time() - start_time

        if 'error' not in batch_result:
            analyzed_count = len(batch_result.get('analyzed_files', []))
            stats = batch_result.get('summary_statistics', {})

            print(f"✅ 批量分析完成:")
            print(f"   处理时间: {batch_time:.3f}s")
            print(f"   分析文档数: {analyzed_count}")
            if stats:
                print(f"   平均质量: {stats.get('average_quality', 0):.1f}/100")

            if analyzed_count > 0:
                print(f"   平均单文档时间: {batch_time/analyzed_count:.3f}s")
        else:
            print(f"❌ 批量分析失败: {batch_result['error']}")

    finally:
        # 清理临时文件
        for file_path in test_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(temp_dir)

def performance_test_similarity_detection():
    """测试相似度检测性能"""
    print("\n🔍 相似度检测性能测试")
    print("-" * 40)

    docgate = DocGateAgent()

    # 创建测试文档对
    temp_dir = tempfile.mkdtemp()
    test_files = []

    try:
        # 创建相似和不同的文档对
        base_content = create_test_document(500, "Base Document")

        # 原始文档
        file1 = os.path.join(temp_dir, "original.md")
        with open(file1, 'w', encoding='utf-8') as f:
            f.write(base_content)
        test_files.append(file1)

        # 略微修改的文档（高相似度）
        modified_content = base_content.replace("Feature one", "Enhanced feature one")
        file2 = os.path.join(temp_dir, "modified.md")
        with open(file2, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        test_files.append(file2)

        # 完全不同的文档（低相似度）
        different_content = create_test_document(500, "Different Document")
        file3 = os.path.join(temp_dir, "different.md")
        with open(file3, 'w', encoding='utf-8') as f:
            f.write(different_content)
        test_files.append(file3)

        print(f"📝 创建了 {len(test_files)} 个文档用于相似度测试")

        # 测试相似度检测
        start_time = time.time()
        similarity_results = docgate.detect_document_similarity(test_files)
        similarity_time = time.time() - start_time

        print(f"✅ 相似度检测完成:")
        print(f"   处理时间: {similarity_time:.3f}s")
        print(f"   比较对数: {len(similarity_results)}")

        for i, result in enumerate(similarity_results, 1):
            doc_a = os.path.basename(result.document_a)
            doc_b = os.path.basename(result.document_b)
            print(f"   {i}. {doc_a} vs {doc_b}: {result.similarity_ratio:.1%} ({result.similarity_type})")

    finally:
        # 清理临时文件
        for file_path in test_files:
            if os.path.exists(file_path):
                os.unlink(file_path)
        os.rmdir(temp_dir)

def performance_test_memory_usage():
    """测试内存使用情况"""
    print("\n💾 内存使用测试")
    print("-" * 40)

    try:
        import psutil
        process = psutil.Process()

        # 记录初始内存
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"📊 初始内存使用: {initial_memory:.1f} MB")

        docgate = DocGateAgent()

        # 创建大文档测试内存使用
        large_content = create_test_document(10000, "Large Document")

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(large_content)
            temp_file = f.name

        try:
            # 分析大文档
            memory_before = process.memory_info().rss / 1024 / 1024
            result = docgate.analyze_document_quality(temp_file)
            memory_after = process.memory_info().rss / 1024 / 1024

            print(f"📊 分析前内存: {memory_before:.1f} MB")
            print(f"📊 分析后内存: {memory_after:.1f} MB")
            print(f"📊 内存增长: {memory_after - memory_before:.1f} MB")

            if 'error' not in result:
                print(f"✅ 大文档分析成功 (评分: {result['overall_score']:.1f})")
            else:
                print(f"❌ 大文档分析失败")

        finally:
            os.unlink(temp_file)

    except ImportError:
        print("⚠️ psutil未安装，跳过内存测试")
    except Exception as e:
        print(f"❌ 内存测试失败: {str(e)}")

def main():
    """运行性能测试"""
    print("🚀 DocGate Agent 性能测试")
    print("=" * 50)

    try:
        # 单文档性能测试
        single_results = performance_test_single_document()

        # 批量处理性能测试
        performance_test_batch_processing()

        # 相似度检测性能测试
        performance_test_similarity_detection()

        # 内存使用测试
        performance_test_memory_usage()

        print(f"\n🎉 性能测试完成!")

        # 总结
        if single_results:
            total_words = sum(r['word_count'] for r in single_results)
            total_time = sum(r['total_time'] for r in single_results)
            avg_quality = sum(r['quality_score'] for r in single_results) / len(single_results)

            print(f"\n📈 测试总结:")
            print(f"   总处理字数: {total_words:,}")
            print(f"   总处理时间: {total_time:.3f}s")
            print(f"   整体处理速度: {total_words/total_time:.0f} 字/秒")
            print(f"   平均质量评分: {avg_quality:.1f}/100")

        print(f"\n💡 性能优化建议:")
        print(f"   - 对于大型项目，建议使用文件模式过滤")
        print(f"   - 批量处理比单个处理更高效")
        print(f"   - 定期清理缓存以节省内存")
        print(f"   - 考虑异步处理大量文档")

    except KeyboardInterrupt:
        print(f"\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    main()