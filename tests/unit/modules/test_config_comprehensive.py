#!/usr/bin/env python3
"""
Comprehensive unit tests for modules.config
Target: High coverage for configuration management
"""

import pytest
import os
import yaml
import json
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from modules.config import Config, ConfigError


class TestConfig:
    """Test Config class functionality"""

    def test_config_initialization_default(self):
        """Test config initialization with defaults"""
        with patch('os.path.exists', return_value=False):
            config = Config()
            assert config.config_file is None
            assert isinstance(config.data, dict)

    def test_config_initialization_with_file(self, tmp_path):
        """Test config initialization with file"""
        config_file = tmp_path / "test_config.yaml"
        test_data = {'database': {'url': 'sqlite:///test.db'}, 'debug': True}

        with open(config_file, 'w') as f:
            yaml.dump(test_data, f)

        config = Config(config_file=str(config_file))
        assert config.data['database']['url'] == 'sqlite:///test.db'
        assert config.data['debug'] is True

    def test_config_get_method(self):
        """Test config get method"""
        config = Config()
        config.data = {
            'database': {'url': 'sqlite:///test.db', 'timeout': 30},
            'api': {'host': 'localhost', 'port': 8000}
        }

        # Test nested key access
        assert config.get('database.url') == 'sqlite:///test.db'
        assert config.get('database.timeout') == 30
        assert config.get('api.host') == 'localhost'

        # Test default values
        assert config.get('missing.key', 'default') == 'default'
        assert config.get('missing.key') is None

    def test_config_set_method(self):
        """Test config set method"""
        config = Config()

        # Set nested values
        config.set('database.url', 'postgresql://localhost/test')
        config.set('api.timeout', 60)
        config.set('new.nested.key', 'value')

        assert config.get('database.url') == 'postgresql://localhost/test'
        assert config.get('api.timeout') == 60
        assert config.get('new.nested.key') == 'value'

    def test_config_yaml_loading(self, tmp_path):
        """Test YAML file loading"""
        config_file = tmp_path / "config.yaml"
        test_data = {
            'app': {
                'name': 'Perfect21',
                'version': '3.0.0'
            },
            'features': ['auth', 'workflow', 'monitoring']
        }

        with open(config_file, 'w') as f:
            yaml.dump(test_data, f)

        config = Config(config_file=str(config_file))
        assert config.get('app.name') == 'Perfect21'
        assert config.get('app.version') == '3.0.0'
        assert 'auth' in config.get('features')

    def test_config_json_loading(self, tmp_path):
        """Test JSON file loading"""
        config_file = tmp_path / "config.json"
        test_data = {
            'database': {'driver': 'sqlite', 'path': '/tmp/test.db'},
            'logging': {'level': 'INFO', 'file': '/var/log/app.log'}
        }

        with open(config_file, 'w') as f:
            json.dump(test_data, f)

        config = Config(config_file=str(config_file))
        assert config.get('database.driver') == 'sqlite'
        assert config.get('logging.level') == 'INFO'

    def test_config_environment_override(self):
        """Test environment variable override"""
        config = Config()
        config.data = {'api': {'host': 'localhost', 'port': 8000}}

        with patch.dict(os.environ, {'API_HOST': 'production.host', 'API_PORT': '9000'}):
            config.load_environment_overrides()

        assert config.get('api.host') == 'production.host'
        assert config.get('api.port') == '9000'

    def test_config_validation(self):
        """Test config validation"""
        config = Config()

        # Define validation schema
        schema = {
            'database': {
                'url': {'type': str, 'required': True},
                'timeout': {'type': int, 'min': 1, 'max': 3600}
            }
        }

        config.set_validation_schema(schema)

        # Valid config
        config.data = {
            'database': {
                'url': 'sqlite:///test.db',
                'timeout': 30
            }
        }
        assert config.validate() is True

        # Invalid config - missing required field
        config.data = {'database': {'timeout': 30}}
        with pytest.raises(ConfigError):
            config.validate()

    def test_config_merge(self):
        """Test config merging"""
        config1 = Config()
        config1.data = {
            'database': {'url': 'sqlite:///test.db', 'timeout': 30},
            'api': {'host': 'localhost'}
        }

        config2_data = {
            'database': {'timeout': 60, 'pool_size': 10},
            'api': {'port': 8000},
            'logging': {'level': 'DEBUG'}
        }

        config1.merge(config2_data)

        # Check merged values
        assert config1.get('database.url') == 'sqlite:///test.db'  # Original
        assert config1.get('database.timeout') == 60  # Overridden
        assert config1.get('database.pool_size') == 10  # New
        assert config1.get('api.host') == 'localhost'  # Original
        assert config1.get('api.port') == 8000  # New
        assert config1.get('logging.level') == 'DEBUG'  # New

    def test_config_save(self, tmp_path):
        """Test config saving"""
        config_file = tmp_path / "save_test.yaml"
        config = Config(config_file=str(config_file))

        config.data = {
            'app': {'name': 'Perfect21', 'version': '3.0.0'},
            'database': {'url': 'sqlite:///test.db'}
        }

        config.save()

        # Verify file was saved correctly
        assert config_file.exists()
        with open(config_file) as f:
            saved_data = yaml.safe_load(f)

        assert saved_data['app']['name'] == 'Perfect21'
        assert saved_data['database']['url'] == 'sqlite:///test.db'

    def test_config_reload(self, tmp_path):
        """Test config reloading"""
        config_file = tmp_path / "reload_test.yaml"
        initial_data = {'version': '1.0.0'}

        with open(config_file, 'w') as f:
            yaml.dump(initial_data, f)

        config = Config(config_file=str(config_file))
        assert config.get('version') == '1.0.0'

        # Modify file
        updated_data = {'version': '2.0.0', 'new_feature': True}
        with open(config_file, 'w') as f:
            yaml.dump(updated_data, f)

        # Reload
        config.reload()
        assert config.get('version') == '2.0.0'
        assert config.get('new_feature') is True

    def test_config_backup_restore(self, tmp_path):
        """Test config backup and restore"""
        config_file = tmp_path / "backup_test.yaml"
        config = Config(config_file=str(config_file))

        config.data = {'original': 'value', 'number': 42}
        config.save()

        # Create backup
        backup_path = config.create_backup()
        assert Path(backup_path).exists()

        # Modify config
        config.data = {'modified': 'value', 'number': 99}
        config.save()

        # Restore from backup
        config.restore_from_backup(backup_path)
        assert config.get('original') == 'value'
        assert config.get('number') == 42

    def test_config_watch_file_changes(self, tmp_path):
        """Test file change watching"""
        config_file = tmp_path / "watch_test.yaml"
        initial_data = {'watched': 'value'}

        with open(config_file, 'w') as f:
            yaml.dump(initial_data, f)

        config = Config(config_file=str(config_file))

        # Mock file modification time change
        import time
        with patch('os.path.getmtime') as mock_mtime:
            mock_mtime.return_value = time.time() + 1000

            # Should detect change and reload
            has_changed = config.has_file_changed()
            assert has_changed is True

    def test_config_error_handling(self, tmp_path):
        """Test config error handling"""
        # Test invalid YAML
        config_file = tmp_path / "invalid.yaml"
        with open(config_file, 'w') as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(ConfigError):
            Config(config_file=str(config_file))

        # Test file not found
        with pytest.raises(ConfigError):
            Config(config_file="/nonexistent/config.yaml", strict=True)

    def test_config_nested_operations(self):
        """Test deeply nested config operations"""
        config = Config()

        # Set deeply nested values
        config.set('level1.level2.level3.level4.value', 'deep_value')
        assert config.get('level1.level2.level3.level4.value') == 'deep_value'

        # Test intermediate level access
        level2 = config.get('level1.level2')
        assert isinstance(level2, dict)
        assert level2['level3']['level4']['value'] == 'deep_value'

    @pytest.mark.parametrize("file_type,extension", [
        ("yaml", ".yaml"),
        ("yaml", ".yml"),
        ("json", ".json")
    ])
    def test_config_file_type_detection(self, tmp_path, file_type, extension):
        """Test automatic file type detection"""
        config_file = tmp_path / f"test{extension}"

        if file_type == "yaml":
            test_data = {'yaml_key': 'yaml_value'}
            with open(config_file, 'w') as f:
                yaml.dump(test_data, f)
        else:
            test_data = {'json_key': 'json_value'}
            with open(config_file, 'w') as f:
                json.dump(test_data, f)

        config = Config(config_file=str(config_file))

        if file_type == "yaml":
            assert config.get('yaml_key') == 'yaml_value'
        else:
            assert config.get('json_key') == 'json_value'


class TestConfigEnvironment:
    """Test config environment features"""

    def test_environment_variable_mapping(self):
        """Test environment variable mapping"""
        config = Config()

        # Define environment mapping
        env_mapping = {
            'DATABASE_URL': 'database.url',
            'API_HOST': 'api.host',
            'API_PORT': 'api.port',
            'DEBUG': 'debug'
        }

        config.set_environment_mapping(env_mapping)

        with patch.dict(os.environ, {
            'DATABASE_URL': 'postgresql://localhost/test',
            'API_HOST': '0.0.0.0',
            'API_PORT': '9000',
            'DEBUG': 'true'
        }):
            config.load_environment_overrides()

        assert config.get('database.url') == 'postgresql://localhost/test'
        assert config.get('api.host') == '0.0.0.0'
        assert config.get('api.port') == '9000'
        assert config.get('debug') == 'true'

    def test_environment_type_conversion(self):
        """Test environment variable type conversion"""
        config = Config()

        # Set type converters
        converters = {
            'api.port': int,
            'debug': lambda x: x.lower() == 'true',
            'timeout': float
        }

        config.set_type_converters(converters)

        with patch.dict(os.environ, {
            'API_PORT': '8080',
            'DEBUG': 'True',
            'TIMEOUT': '30.5'
        }):
            config.load_environment_overrides()

        assert config.get('api.port') == 8080
        assert isinstance(config.get('api.port'), int)
        assert config.get('debug') is True
        assert isinstance(config.get('debug'), bool)
        assert config.get('timeout') == 30.5
        assert isinstance(config.get('timeout'), float)


class TestConfigIntegration:
    """Integration tests for Config"""

    def test_config_complete_workflow(self, tmp_path):
        """Test complete config workflow"""
        config_file = tmp_path / "complete.yaml"

        # 1. Create initial config
        config = Config(config_file=str(config_file))
        config.data = {
            'app': {'name': 'Perfect21', 'version': '1.0.0'},
            'database': {'url': 'sqlite:///test.db', 'timeout': 30},
            'features': ['auth', 'workflow']
        }
        config.save()

        # 2. Load in new instance
        config2 = Config(config_file=str(config_file))
        assert config2.get('app.name') == 'Perfect21'

        # 3. Update with environment overrides
        with patch.dict(os.environ, {'APP_VERSION': '2.0.0', 'DATABASE_TIMEOUT': '60'}):
            config2.load_environment_overrides()

        assert config2.get('app.version') == '2.0.0'
        assert config2.get('database.timeout') == '60'

        # 4. Merge additional config
        additional = {'logging': {'level': 'DEBUG'}, 'features': ['monitoring']}
        config2.merge(additional)

        # 5. Validate and save
        assert config2.validate() is True
        config2.save()

        # 6. Verify final state
        config3 = Config(config_file=str(config_file))
        assert config3.get('logging.level') == 'DEBUG'
        assert 'monitoring' in config3.get('features')

    def test_config_concurrent_access(self, tmp_path):
        """Test concurrent config access"""
        import threading
        import time

        config_file = tmp_path / "concurrent.yaml"
        initial_data = {'counter': 0, 'threads': []}

        with open(config_file, 'w') as f:
            yaml.dump(initial_data, f)

        results = []
        errors = []

        def worker(worker_id):
            try:
                config = Config(config_file=str(config_file))
                for i in range(10):
                    current = config.get('counter', 0)
                    config.set('counter', current + 1)

                    threads_list = config.get('threads', [])
                    threads_list.append(f"worker_{worker_id}_{i}")
                    config.set('threads', threads_list)

                    time.sleep(0.001)  # Small delay

                results.append(f"worker_{worker_id}_completed")
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Check results
        assert len(errors) == 0
        assert len(results) == 5

    def test_config_performance(self, tmp_path):
        """Test config performance"""
        import time

        config_file = tmp_path / "performance.yaml"

        # Create large config
        large_data = {}
        for i in range(1000):
            large_data[f'section_{i}'] = {
                f'key_{j}': f'value_{i}_{j}'
                for j in range(10)
            }

        with open(config_file, 'w') as f:
            yaml.dump(large_data, f)

        # Test loading performance
        start_time = time.time()
        config = Config(config_file=str(config_file))
        load_time = time.time() - start_time

        # Should load within reasonable time (< 1 second)
        assert load_time < 1.0

        # Test access performance
        start_time = time.time()
        for i in range(1000):
            value = config.get(f'section_{i % 100}.key_{i % 10}')
            assert value is not None
        access_time = time.time() - start_time

        # Should access quickly (< 0.5 seconds for 1000 accesses)
        assert access_time < 0.5


@pytest.mark.performance
class TestConfigPerformance:
    """Performance tests for Config"""

    def test_large_config_handling(self, tmp_path):
        """Test handling of large configuration files"""
        config_file = tmp_path / "large_config.yaml"

        # Create very large config (10,000 entries)
        large_config = {}
        for i in range(10000):
            large_config[f'item_{i}'] = {
                'id': i,
                'name': f'Item {i}',
                'data': [f'data_{j}' for j in range(10)]
            }

        with open(config_file, 'w') as f:
            yaml.dump(large_config, f)

        # Test loading and access performance
        import time
        start_time = time.time()

        config = Config(config_file=str(config_file))
        load_time = time.time() - start_time

        # Random access test
        import random
        start_time = time.time()
        for _ in range(1000):
            idx = random.randint(0, 9999)
            value = config.get(f'item_{idx}.name')
            assert value == f'Item {idx}'
        access_time = time.time() - start_time

        # Performance assertions
        assert load_time < 5.0  # Load within 5 seconds
        assert access_time < 1.0  # 1000 random accesses within 1 second

    def test_memory_efficiency(self):
        """Test memory efficiency of config storage"""
        import sys

        config = Config()

        # Add many items and measure memory
        initial_size = sys.getsizeof(config.data)

        for i in range(10000):
            config.set(f'item_{i}', f'value_{i}')

        final_size = sys.getsizeof(config.data)

        # Memory growth should be reasonable
        growth_per_item = (final_size - initial_size) / 10000
        assert growth_per_item < 100  # Less than 100 bytes per item


if __name__ == "__main__":
    pytest.main([__file__, "-v"])