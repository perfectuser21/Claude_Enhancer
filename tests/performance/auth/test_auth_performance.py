#!/usr/bin/env python3
"""
Perfect21认证系统性能测试
测试并发登录、响应时间等性能指标
"""

import pytest
import os
import sys
import time
import asyncio
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from features.auth_system.auth_manager import AuthManager
from api.auth_api import auth_router
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestAuthenticationPerformance:
    """认证性能测试"""

    @pytest.fixture
    def auth_manager(self, mock_env):
        """创建认证管理器实例"""
        return AuthManager("data/test_auth_performance.db")

    def test_password_hashing_performance(self, auth_manager):
        """测试密码哈希性能"""
        password = "TestPassword123!"
        hash_times = []

        # 测试多次密码哈希
        for i in range(10):
            start_time = time.time()
            hashed = auth_manager.user_service._hash_password(password)
            end_time = time.time()
            hash_times.append(end_time - start_time)

        # 计算统计数据
        avg_time = statistics.mean(hash_times)
        max_time = max(hash_times)
        min_time = min(hash_times)

        print(f"Password hashing performance:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  Min time: {min_time:.4f}s")

        # 密码哈希应该足够慢以防止暴力破解，但不能太慢影响用户体验
        assert avg_time > 0.05  # 至少50ms（防暴力破解）
        assert avg_time < 2.0   # 不超过2秒（用户体验）

    def test_token_generation_performance(self, auth_manager):
        """测试令牌生成性能"""
        user_id = "test_user_123"
        generation_times = []

        # 测试多次令牌生成
        for i in range(100):
            start_time = time.time()
            token = auth_manager.token_manager.generate_access_token(user_id)
            end_time = time.time()
            generation_times.append(end_time - start_time)

        # 计算统计数据
        avg_time = statistics.mean(generation_times)
        max_time = max(generation_times)
        p95_time = statistics.quantiles(generation_times, n=20)[18]  # 95th percentile

        print(f"Token generation performance:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  P95 time: {p95_time:.4f}s")

        # 令牌生成应该很快
        assert avg_time < 0.01   # 平均小于10ms
        assert p95_time < 0.05   # P95小于50ms

    def test_token_verification_performance(self, auth_manager):
        """测试令牌验证性能"""
        user_id = "test_user_123"
        token = auth_manager.token_manager.generate_access_token(user_id)
        verification_times = []

        # 测试多次令牌验证
        for i in range(100):
            start_time = time.time()
            payload = auth_manager.token_manager.verify_access_token(token)
            end_time = time.time()
            verification_times.append(end_time - start_time)

        # 计算统计数据
        avg_time = statistics.mean(verification_times)
        max_time = max(verification_times)
        p95_time = statistics.quantiles(verification_times, n=20)[18]

        print(f"Token verification performance:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  P95 time: {p95_time:.4f}s")

        # 令牌验证应该很快
        assert avg_time < 0.01   # 平均小于10ms
        assert p95_time < 0.05   # P95小于50ms

    def test_login_performance(self, auth_manager):
        """测试登录性能"""
        # 注册测试用户
        username = "perfuser"
        email = "perf@example.com"
        password = "PerfPass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        login_times = []

        # 测试多次登录
        for i in range(20):
            start_time = time.time()
            result = auth_manager.login(
                identifier=username,
                password=password
            )
            end_time = time.time()

            assert result['success'] == True
            login_times.append(end_time - start_time)

        # 计算统计数据
        avg_time = statistics.mean(login_times)
        max_time = max(login_times)
        p95_time = statistics.quantiles(login_times, n=20)[18]

        print(f"Login performance:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  P95 time: {p95_time:.4f}s")

        # 登录应该在合理时间内完成
        assert avg_time < 1.0    # 平均小于1秒
        assert p95_time < 2.0    # P95小于2秒


class TestConcurrentAuthentication:
    """并发认证测试"""

    @pytest.fixture
    def auth_manager(self, mock_env):
        """创建认证管理器实例"""
        return AuthManager("data/test_auth_concurrent.db")

    def test_concurrent_registrations(self, auth_manager):
        """测试并发注册"""
        def register_user(user_index):
            """注册单个用户"""
            start_time = time.time()
            result = auth_manager.register(
                username=f"concuser{user_index}",
                email=f"conc{user_index}@example.com",
                password="ConcPass123!"
            )
            end_time = time.time()
            return {
                'result': result,
                'time': end_time - start_time,
                'user_index': user_index
            }

        # 并发注册用户
        concurrent_users = 20
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_user = {
                executor.submit(register_user, i): i
                for i in range(concurrent_users)
            }

            results = []
            for future in as_completed(future_to_user):
                result_data = future.result()
                results.append(result_data)

        # 验证结果
        successful_registrations = [r for r in results if r['result']['success']]
        registration_times = [r['time'] for r in results]

        print(f"Concurrent registration results:")
        print(f"  Total attempts: {len(results)}")
        print(f"  Successful: {len(successful_registrations)}")
        print(f"  Average time: {statistics.mean(registration_times):.4f}s")
        print(f"  Max time: {max(registration_times):.4f}s")

        # 大部分注册应该成功
        assert len(successful_registrations) >= concurrent_users * 0.8

    def test_concurrent_logins_same_user(self, auth_manager):
        """测试同一用户的并发登录"""
        # 注册用户
        username = "sameuser"
        email = "same@example.com"
        password = "SamePass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        def login_attempt():
            """单次登录尝试"""
            start_time = time.time()
            result = auth_manager.login(
                identifier=username,
                password=password
            )
            end_time = time.time()
            return {
                'result': result,
                'time': end_time - start_time
            }

        # 并发登录
        concurrent_logins = 10
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_attempt) for _ in range(concurrent_logins)]
            results = [future.result() for future in as_completed(futures)]

        # 验证结果
        successful_logins = [r for r in results if r['result']['success']]
        login_times = [r['time'] for r in results]

        print(f"Concurrent login results (same user):")
        print(f"  Total attempts: {len(results)}")
        print(f"  Successful: {len(successful_logins)}")
        print(f"  Average time: {statistics.mean(login_times):.4f}s")

        # 所有登录都应该成功
        assert len(successful_logins) == concurrent_logins

    def test_concurrent_logins_different_users(self, auth_manager):
        """测试不同用户的并发登录"""
        # 注册多个用户
        users = []
        for i in range(10):
            username = f"user{i}"
            email = f"user{i}@example.com"
            password = f"Pass{i}123!"

            auth_manager.register(
                username=username,
                email=email,
                password=password
            )
            users.append((username, password))

        def login_user(user_data):
            """用户登录"""
            username, password = user_data
            start_time = time.time()
            result = auth_manager.login(
                identifier=username,
                password=password
            )
            end_time = time.time()
            return {
                'result': result,
                'time': end_time - start_time,
                'username': username
            }

        # 并发登录
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(login_user, user) for user in users]
            results = [future.result() for future in as_completed(futures)]

        # 验证结果
        successful_logins = [r for r in results if r['result']['success']]
        login_times = [r['time'] for r in results]

        print(f"Concurrent login results (different users):")
        print(f"  Total attempts: {len(results)}")
        print(f"  Successful: {len(successful_logins)}")
        print(f"  Average time: {statistics.mean(login_times):.4f}s")

        # 所有登录都应该成功
        assert len(successful_logins) == len(users)

    def test_concurrent_token_operations(self, auth_manager):
        """测试并发令牌操作"""
        # 注册并登录用户获取初始令牌
        username = "tokenuser"
        email = "token@example.com"
        password = "TokenPass123!"

        auth_manager.register(
            username=username,
            email=email,
            password=password
        )

        login_result = auth_manager.login(
            identifier=username,
            password=password
        )
        refresh_token = login_result['refresh_token']

        def token_operation():
            """令牌操作"""
            start_time = time.time()
            # 随机执行刷新或验证操作
            import random
            if random.choice([True, False]):
                # 刷新令牌
                result = auth_manager.refresh_token(refresh_token)
            else:
                # 验证令牌
                result = auth_manager.verify_token(login_result['access_token'])

            end_time = time.time()
            return {
                'result': result,
                'time': end_time - start_time
            }

        # 并发令牌操作
        concurrent_operations = 20
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(token_operation) for _ in range(concurrent_operations)]
            results = [future.result() for future in as_completed(futures)]

        # 验证结果
        successful_operations = [r for r in results if r['result']['success']]
        operation_times = [r['time'] for r in results]

        print(f"Concurrent token operations:")
        print(f"  Total operations: {len(results)}")
        print(f"  Successful: {len(successful_operations)}")
        print(f"  Average time: {statistics.mean(operation_times):.4f}s")

        # 大部分操作应该成功
        assert len(successful_operations) >= concurrent_operations * 0.8


class TestAPIPerformance:
    """API性能测试"""

    @pytest.fixture
    def app(self, mock_env):
        """创建测试应用"""
        app = FastAPI()
        app.include_router(auth_router)
        return app

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)

    def test_api_registration_performance(self, client):
        """测试API注册性能"""
        registration_times = []

        for i in range(10):
            registration_data = {
                "username": f"apiuser{i}",
                "email": f"api{i}@example.com",
                "password": "ApiPass123!"
            }

            start_time = time.time()
            response = client.post("/api/auth/register", json=registration_data)
            end_time = time.time()

            assert response.status_code == 200
            registration_times.append(end_time - start_time)

        # 计算统计数据
        avg_time = statistics.mean(registration_times)
        max_time = max(registration_times)
        p95_time = statistics.quantiles(registration_times, n=20)[18]

        print(f"API registration performance:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  P95 time: {p95_time:.4f}s")

        # API注册应该在合理时间内完成
        assert avg_time < 1.0    # 平均小于1秒
        assert p95_time < 2.0    # P95小于2秒

    def test_api_login_performance(self, client):
        """测试API登录性能"""
        # 先注册用户
        registration_data = {
            "username": "apiloginperf",
            "email": "apiloginperf@example.com",
            "password": "ApiLoginPerf123!"
        }
        client.post("/api/auth/register", json=registration_data)

        login_times = []

        for i in range(20):
            login_data = {
                "identifier": "apiloginperf",
                "password": "ApiLoginPerf123!"
            }

            start_time = time.time()
            response = client.post("/api/auth/login", json=login_data)
            end_time = time.time()

            assert response.status_code == 200
            login_times.append(end_time - start_time)

        # 计算统计数据
        avg_time = statistics.mean(login_times)
        max_time = max(login_times)
        p95_time = statistics.quantiles(login_times, n=20)[18]

        print(f"API login performance:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  P95 time: {p95_time:.4f}s")

        # API登录应该在合理时间内完成
        assert avg_time < 1.0    # 平均小于1秒
        assert p95_time < 2.0    # P95小于2秒

    def test_api_token_verification_performance(self, client):
        """测试API令牌验证性能"""
        # 注册并登录获取令牌
        registration_data = {
            "username": "apitokenperf",
            "email": "apitokenperf@example.com",
            "password": "ApiTokenPerf123!"
        }
        client.post("/api/auth/register", json=registration_data)

        login_data = {
            "identifier": "apitokenperf",
            "password": "ApiTokenPerf123!"
        }
        login_response = client.post("/api/auth/login", json=login_data)
        access_token = login_response.json()['access_token']

        verification_times = []

        for i in range(50):
            headers = {"Authorization": f"Bearer {access_token}"}

            start_time = time.time()
            response = client.get("/api/auth/verify", headers=headers)
            end_time = time.time()

            assert response.status_code == 200
            verification_times.append(end_time - start_time)

        # 计算统计数据
        avg_time = statistics.mean(verification_times)
        max_time = max(verification_times)
        p95_time = statistics.quantiles(verification_times, n=20)[18]

        print(f"API token verification performance:")
        print(f"  Average time: {avg_time:.4f}s")
        print(f"  Max time: {max_time:.4f}s")
        print(f"  P95 time: {p95_time:.4f}s")

        # 令牌验证应该很快
        assert avg_time < 0.2    # 平均小于200ms
        assert p95_time < 0.5    # P95小于500ms


class TestLoadTesting:
    """负载测试"""

    @pytest.fixture
    def auth_manager(self, mock_env):
        """创建认证管理器实例"""
        return AuthManager("data/test_auth_load.db")

    def test_high_volume_registrations(self, auth_manager):
        """测试大量用户注册"""
        def register_batch(start_index, batch_size):
            """批量注册用户"""
            results = []
            for i in range(start_index, start_index + batch_size):
                start_time = time.time()
                result = auth_manager.register(
                    username=f"loaduser{i}",
                    email=f"load{i}@example.com",
                    password="LoadPass123!"
                )
                end_time = time.time()
                results.append({
                    'success': result['success'],
                    'time': end_time - start_time
                })
            return results

        # 使用多线程进行大量注册
        total_users = 100
        batch_size = 10
        batches = total_users // batch_size

        all_results = []
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i in range(batches):
                future = executor.submit(register_batch, i * batch_size, batch_size)
                futures.append(future)

            for future in as_completed(futures):
                batch_results = future.result()
                all_results.extend(batch_results)

        total_time = time.time() - start_time

        # 计算统计数据
        successful_registrations = [r for r in all_results if r['success']]
        registration_times = [r['time'] for r in all_results]

        print(f"High volume registration results:")
        print(f"  Total users: {len(all_results)}")
        print(f"  Successful: {len(successful_registrations)}")
        print(f"  Success rate: {len(successful_registrations)/len(all_results)*100:.2f}%")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Throughput: {len(all_results)/total_time:.2f} registrations/sec")
        print(f"  Average registration time: {statistics.mean(registration_times):.4f}s")

        # 验证性能指标
        success_rate = len(successful_registrations) / len(all_results)
        throughput = len(all_results) / total_time

        assert success_rate > 0.95  # 95%以上成功率
        assert throughput > 5       # 每秒至少5个注册

    def test_sustained_login_load(self, auth_manager):
        """测试持续登录负载"""
        # 预先注册用户
        users = []
        for i in range(20):
            username = f"sustainuser{i}"
            email = f"sustain{i}@example.com"
            password = "SustainPass123!"

            auth_manager.register(
                username=username,
                email=email,
                password=password
            )
            users.append((username, password))

        def sustained_login_worker(user_data, duration_seconds):
            """持续登录工作线程"""
            username, password = user_data
            login_count = 0
            start_time = time.time()

            while time.time() - start_time < duration_seconds:
                result = auth_manager.login(
                    identifier=username,
                    password=password
                )
                if result['success']:
                    login_count += 1
                # 短暂休息
                time.sleep(0.1)

            return login_count

        # 运行持续负载测试
        duration = 10  # 10秒测试
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for user in users[:10]:  # 使用前10个用户
                future = executor.submit(sustained_login_worker, user, duration)
                futures.append(future)

            total_logins = sum(future.result() for future in as_completed(futures))

        print(f"Sustained login load results:")
        print(f"  Duration: {duration}s")
        print(f"  Total logins: {total_logins}")
        print(f"  Average throughput: {total_logins/duration:.2f} logins/sec")

        # 验证吞吐量
        throughput = total_logins / duration
        assert throughput > 10  # 每秒至少10次登录


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])  # -s显示print输出