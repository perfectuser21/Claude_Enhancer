# DocGate Agent - 文档质量分析专家

DocGate Agent是一个专门用于文档质量分析的独立Python Agent，具备完整的文档分析、摘要生成、相似度检测和改进建议功能。

## 🎯 核心功能

### 1. 文档质量分析
- **多维度评估**：可读性、结构性、完整性
- **综合评分**：0-100分的质量评分系统
- **问题检测**：自动识别质量问题和潜在改进点
- **质量等级**：excellent, good, fair, poor, very_poor

### 2. 自动生成摘要
- **智能提取**：自动提取文档标题、关键点和核心内容
- **可配置长度**：支持指定摘要句子数量
- **阅读时间估算**：基于平均阅读速度的时间预估
- **元数据提取**：自动识别作者、日期、版本等信息

### 3. 相似度检测
- **重复内容识别**：检测文档间的重复和相似内容
- **相似度类型**：identical, high, medium, low四个等级
- **详细分析**：提供相同行数和相似度比例
- **批量比较**：支持多文档间的两两比较

### 4. 文档覆盖度分析
- **项目级分析**：评估整个项目的文档覆盖情况
- **标准文档检查**：检查README、CHANGELOG等标准文档
- **缺失文档识别**：自动识别应该存在但缺失的文档
- **改进建议**：提供具体的文档完善建议

### 5. 批量分析
- **模式匹配**：支持文件模式匹配进行批量处理
- **统计分析**：生成项目级的文档质量统计
- **问题汇总**：分析常见问题和改进方向
- **质量分布**：可视化质量等级分布

## 📊 质量评估指标

### 基础指标
- **字数统计**：文档内容长度分析
- **结构分析**：标题、段落、列表、表格等结构元素
- **链接检查**：外部链接有效性验证
- **代码示例**：代码块和示例的完整性

### 高级指标
- **可读性评分**：基于Flesch Reading Ease的可读性分析
- **结构评分**：文档组织结构和层次的评估
- **完整性评分**：必要信息的完整性检查
- **综合质量**：多维度指标的加权综合评分

## 🚀 使用方法

### 基本使用

```python
from docgate_agent import DocGateAgent

# 初始化Agent
docgate = DocGateAgent()

# 1. 分析单个文档质量
quality_result = docgate.analyze_document_quality("README.md")
print(f"质量评分: {quality_result['overall_score']:.1f}/100")
print(f"质量等级: {quality_result['quality_level']}")

# 2. 生成文档摘要
summary_result = docgate.generate_document_summary("README.md", max_sentences=3)
print(f"标题: {summary_result['title']}")
print(f"摘要: {summary_result['summary']}")

# 3. 检测文档相似度
similarity_results = docgate.detect_document_similarity(["doc1.md", "doc2.md"])
for result in similarity_results:
    print(f"相似度: {result.similarity_ratio:.1%}")

# 4. 分析项目文档覆盖度
coverage_result = docgate.analyze_documentation_coverage("/path/to/project")
print(f"覆盖率: {coverage_result['coverage_percentage']:.1f}%")

# 5. 批量分析文档
batch_result = docgate.batch_analyze_documents(["*.md", "*.rst"])
stats = batch_result['summary_statistics']
print(f"平均质量: {stats['average_quality']:.1f}/100")
```

### 高级功能

```python
# 生成项目质量报告
report_file = docgate.generate_quality_report()
print(f"报告已保存: {report_file}")

# 自定义质量标准
docgate.quality_standards.update({
    'min_word_count': 200,
    'similarity_threshold': 0.7,
    'readability_target': 80
})
```

## 📋 输出格式

### 质量分析结果
```json
{
    "file_path": "/path/to/document.md",
    "document_type": "readme",
    "metrics": {
        "word_count": 500,
        "sentence_count": 25,
        "paragraph_count": 8,
        "heading_count": 6,
        "readability_score": 75.5,
        "structure_score": 80.0,
        "completeness_score": 70.0,
        "quality_score": 75.2
    },
    "overall_score": 72.8,
    "quality_level": "fair",
    "issues": [
        {
            "type": "readability",
            "severity": "minor",
            "location": "sentence 5",
            "description": "句子过长（30个单词）",
            "suggestion": "考虑分解为多个较短的句子"
        }
    ],
    "suggestions": [
        "提高可读性：使用更简单的词汇和更短的句子",
        "完善文档内容：添加使用示例和安装说明"
    ]
}
```

### 摘要生成结果
```json
{
    "file_path": "/path/to/document.md",
    "title": "Project Documentation",
    "summary": "This document provides an overview of...",
    "key_points": [
        "Main feature description",
        "Installation instructions",
        "Usage examples"
    ],
    "metadata": {
        "author": "John Doe",
        "date": "2024-01-15",
        "version": "1.0"
    },
    "estimated_reading_time": "3 minutes"
}
```

## ⚙️ 配置选项

### 质量标准配置
```python
quality_standards = {
    'min_word_count': 100,        # 最小字数
    'max_word_count': 5000,       # 最大字数
    'min_headings': 2,            # 最少标题数
    'max_sentence_length': 25,    # 最大句子长度
    'similarity_threshold': 0.8,  # 相似度阈值
    'readability_target': 70      # 可读性目标分数
}
```

### 文档类型模式
```python
doc_patterns = {
    'readme': r'readme\.md$',
    'api_doc': r'api\.md$|swagger\.md$',
    'changelog': r'changelog\.md$|changes\.md$',
    'install': r'install\.md$|setup\.md$',
    'config': r'config\.md$|configuration\.md$',
    'guide': r'guide\.md$|tutorial\.md$'
}
```

## 🔧 技术特点

### 独立性
- **无外部依赖**：不调用其他Agent，避免嵌套调用
- **纯Python实现**：使用标准库，无复杂依赖
- **模块化设计**：可独立运行或集成到其他系统

### 扩展性
- **可配置标准**：支持自定义质量标准和阈值
- **插件式架构**：易于添加新的分析算法
- **多格式支持**：Markdown、RST、TXT等格式

### 性能
- **批量处理**：支持大量文档的批量分析
- **缓存机制**：避免重复分析相同文档
- **内存优化**：大文件分段处理，避免内存溢出

## 📈 质量评分算法

### 可读性评分（Flesch Reading Ease简化版）
```
score = 206.835 - (1.015 × 平均句长) - (84.6 × 平均音节数)
```

### 结构评分
- 标题结构：20分
- 段落组织：15分
- 链接使用：10分
- 代码示例：15分
- 列表使用：10分
- 表格使用：15分
- 标题层次：15分

### 完整性评分
- 文档长度：20分
- 介绍部分：15分
- 使用说明：15分
- 示例代码：20分
- 联系信息：10分
- 更新日期：10分
- 目录结构：10分

## 🐛 常见问题

### Q: DocGate Agent可以分析哪些文档格式？
A: 目前支持Markdown(.md)、reStructuredText(.rst)、纯文本(.txt)和AsciiDoc(.adoc)格式。

### Q: 如何提高文档的质量评分？
A: 主要关注以下几个方面：
1. 添加清晰的标题结构
2. 包含使用示例和代码块
3. 控制句子长度，提高可读性
4. 确保文档内容完整（介绍、安装、使用等）
5. 添加适当的链接和参考资料

### Q: 相似度检测的准确性如何？
A: 使用Python的difflib库进行序列匹配，对于结构化文档（如Markdown）有较好的检测效果。建议人工review高相似度（>80%）的文档。

### Q: 批量分析会不会很慢？
A: 对于大量文档，建议使用文件模式过滤，避免分析无关文件。系统会自动缓存分析结果，重复分析速度较快。

## 📝 更新日志

### v1.0.0 (2024-09-27)
- ✅ 实现文档质量分析核心功能
- ✅ 添加自动摘要生成
- ✅ 实现相似度检测算法
- ✅ 完成文档覆盖度分析
- ✅ 支持批量文档处理
- ✅ 添加质量报告生成功能

---

*DocGate Agent - 让文档质量管理变得简单高效*