#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

print("1. 导入数据库模块...")
try:
    from modules.database import DatabaseManager, DatabaseConfig
    print("2. 数据库模块导入成功")
except Exception as e:
    print(f"2. 数据库模块导入失败: {e}")
    exit(1)

print("3. 创建配置...")
config = DatabaseConfig()
print("4. 配置创建成功")

print("5. 测试完成")