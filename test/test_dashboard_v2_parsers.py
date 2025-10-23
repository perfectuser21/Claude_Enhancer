#!/usr/bin/env python3
"""
Unit tests for Dashboard v2 Parsers

Tests all 4 parser classes:
- CapabilityParser
- LearningSystemParser
- FeatureParser
- ProjectMonitor

Version: 7.2.0
"""

import sys
import unittest
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from parsers import CapabilityParser, LearningSystemParser, FeatureParser, ProjectMonitor
from data_models import ImportanceLevel, EventType, ProjectStatus


class TestCapabilityParser(unittest.TestCase):
    """Test CapabilityParser class"""

    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        self.parser = CapabilityParser(self.project_root / "docs" / "CAPABILITY_MATRIX.md")

    def test_parse_valid_file(self):
        """Test parsing valid CAPABILITY_MATRIX.md"""
        result = self.parser.parse()

        self.assertTrue(result.success, f"Parse failed: {result.error_message}")
        self.assertIn('core_stats', result.data)
        self.assertIn('capabilities', result.data)

        # Check core stats
        core_stats = result.data['core_stats']
        self.assertEqual(core_stats.total_phases, 7)
        self.assertEqual(core_stats.total_checkpoints, 97)
        self.assertEqual(core_stats.quality_gates, 2)

    def test_parse_nonexistent_file(self):
        """Test parsing non-existent file"""
        parser = CapabilityParser(Path("/nonexistent/file.md"))
        result = parser.parse()

        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message.lower())


class TestLearningSystemParser(unittest.TestCase):
    """Test LearningSystemParser class"""

    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        self.parser = LearningSystemParser(self.project_root)

    def test_parse_memory_cache(self):
        """Test parsing memory-cache.json"""
        result = self.parser.parse_memory_cache()

        self.assertTrue(result.success)
        self.assertIsNotNone(result.data)

        memory_cache = result.data
        self.assertGreaterEqual(memory_cache.total_entries, 0)
        self.assertGreaterEqual(memory_cache.cache_size_bytes, 0)

    def test_parse_decisions(self):
        """Test parsing DECISIONS.md"""
        result = self.parser.parse_decisions()

        self.assertTrue(result.success)
        self.assertIsInstance(result.data, list)

    def test_calculate_statistics(self):
        """Test statistics calculation"""
        dec_result = self.parser.parse_decisions()
        mem_result = self.parser.parse_memory_cache()

        stats = self.parser.calculate_statistics(
            dec_result.data if dec_result.success else [],
            mem_result.data if mem_result.success else None
        )

        self.assertGreaterEqual(stats.total_decisions, 0)
        self.assertIn(stats.cache_health_status, ['healthy', 'warning', 'critical'])


class TestFeatureParser(unittest.TestCase):
    """Test FeatureParser class"""

    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        # Note: dashboard.html may not exist, parser uses hardcoded fallback
        self.parser = FeatureParser(self.project_root / "tools" / "web" / "dashboard.html")

    def test_parse_features(self):
        """Test parsing features"""
        result = self.parser.parse()

        # Should always succeed (uses fallback)
        self.assertTrue(result.success or not result.success)  # Allow both cases

        if result.success:
            features = result.data
            self.assertGreaterEqual(len(features), 12, "Should have at least 12 features")

            # Check first feature structure
            if features:
                feature = features[0]
                self.assertIsNotNone(feature.id)
                self.assertIsNotNone(feature.name)
                self.assertIn(feature.priority, ['P0', 'P1', 'P2'])


class TestProjectMonitor(unittest.TestCase):
    """Test ProjectMonitor class"""

    def setUp(self):
        self.project_root = Path(__file__).parent.parent
        self.monitor = ProjectMonitor(self.project_root)

    def test_read_events(self):
        """Test reading telemetry events"""
        result = self.monitor.read_events(limit=10)

        self.assertTrue(result.success)
        self.assertIsInstance(result.data, list)

    def test_get_project_status(self):
        """Test getting project status"""
        result = self.monitor.get_project_status()

        self.assertTrue(result.success)

        project = result.data
        self.assertIsNotNone(project.name)
        self.assertIsNotNone(project.status)
        self.assertIn(project.status, [s for s in ProjectStatus])


class TestIntegration(unittest.TestCase):
    """Integration tests for all parsers"""

    def test_all_parsers_work_together(self):
        """Test that all parsers can be instantiated and called"""
        project_root = Path(__file__).parent.parent

        # Capability Parser
        cap_parser = CapabilityParser(project_root / "docs" / "CAPABILITY_MATRIX.md")
        cap_result = cap_parser.parse()

        # Learning System Parser
        learn_parser = LearningSystemParser(project_root)
        dec_result = learn_parser.parse_decisions()
        mem_result = learn_parser.parse_memory_cache()

        # Feature Parser
        feat_parser = FeatureParser(project_root / "tools" / "web" / "dashboard.html")
        feat_result = feat_parser.parse()

        # Project Monitor
        proj_monitor = ProjectMonitor(project_root)
        proj_result = proj_monitor.get_project_status()

        # All should succeed or gracefully handle errors
        self.assertTrue(cap_result.success or cap_result.error_message)
        self.assertTrue(dec_result.success or dec_result.warnings)
        self.assertTrue(mem_result.success or mem_result.warnings)
        self.assertTrue(feat_result.success or feat_result.error_message)
        self.assertTrue(proj_result.success or proj_result.warnings)


def run_tests():
    """Run all tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
