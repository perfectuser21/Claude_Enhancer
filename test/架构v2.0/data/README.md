# 测试数据目录

此目录包含架构v2.0测试所需的测试数据和fixtures。

## 目录结构

```
data/
├── sample_core_files/      # 测试用核心文件样本
├── sample_features/        # 测试用Feature样本
├── sample_configs/         # 测试用配置文件
└── integrity_hashes/       # 测试用Hash文件
```

## 使用方法

测试脚本会自动从这些目录加载测试数据。

## 注意事项

- 测试数据应该是最小化的，只包含测试必需的内容
- 不要包含真实的敏感数据
- 测试后应自动清理临时数据
