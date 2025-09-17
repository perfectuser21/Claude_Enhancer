#!/usr/bin/env python3
import time
import subprocess
from modules.git_cache import get_git_cache

# 测试原始方式
start = time.time()
for i in range(3):
    subprocess.run(['git', 'status'], capture_output=True)
    subprocess.run(['git', 'diff', '--cached'], capture_output=True)
    subprocess.run(['git', 'diff'], capture_output=True)
old_time = time.time() - start

# 测试缓存方式
gc = get_git_cache()
start = time.time()
for i in range(3):
    gc.batch_git_status()
new_time = time.time() - start

print(f"原始方式: {old_time:.3f}秒")
print(f"缓存方式: {new_time:.3f}秒")
print(f"性能提升: {(1 - new_time/old_time) * 100:.1f}%")
