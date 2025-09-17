#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, '.')

print("1. 导入ResourceManager...")
from modules.resource_manager import ResourceManager
print("2. 导入成功")

print("3. 创建ResourceManager...")
rm = ResourceManager()
print("4. 创建成功")

print("5. 注册资源...")
success = rm.register_resource("test", "data")
print(f"6. 注册: {success}")

print("7. 完成")