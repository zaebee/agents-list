#!/usr/bin/env python3
"""
Unit tests for agent validation functionality.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from validate_agents import parse_agent_file, audit_model_assignments, EXPECTED_MODEL_ASSIGNMENTS


class TestValidateAgents(unittest.TestCase):
    """Test cases for agent validation functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp files
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_agent_file(self, filename: str, frontmatter: str, content: str = "Test content"):
        """Helper to create a test agent file."""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'w') as f:
            f.write(f"---\n{frontmatter}\n---\n\n{content}")
        return file_path

    def test_parse_valid_agent_file(self):
        """Test parsing a valid agent file."""
        frontmatter = """name: test-agent
description: Test agent for unit testing
model: sonnet
tools: Read, Edit, Grep"""
        
        file_path = self.create_test_agent_file("test-agent.md", frontmatter)
        
        metadata = parse_agent_file(file_path)
        
        self.assertNotIn("error", metadata)
        self.assertEqual(metadata["name"], "test-agent")
        self.assertEqual(metadata["description"], "Test agent for unit testing")
        self.assertEqual(metadata["model"], "sonnet")
        self.assertEqual(metadata["tools"], "Read, Edit, Grep")

    def test_parse_file_without_frontmatter(self):
        """Test parsing a file without frontmatter."""
        file_path = Path(self.temp_dir) / "no-frontmatter.md"
        with open(file_path, 'w') as f:
            f.write("Just some content without frontmatter")
        
        metadata = parse_agent_file(file_path)
        
        self.assertIn("error", metadata)
        self.assertEqual(metadata["error"], "No frontmatter found")

    def test_parse_malformed_frontmatter(self):
        """Test parsing a file with malformed frontmatter."""
        frontmatter = """name: test-agent
description-without-colon Test agent
model sonnet"""
        
        file_path = self.create_test_agent_file("malformed.md", frontmatter)
        
        metadata = parse_agent_file(file_path)
        
        # Should still parse what it can
        self.assertEqual(metadata.get("name"), "test-agent")
        # malformed lines should be ignored or handled gracefully

    def test_expected_model_assignments_structure(self):
        """Test that expected model assignments are properly structured."""
        self.assertIn("haiku", EXPECTED_MODEL_ASSIGNMENTS)
        self.assertIn("sonnet", EXPECTED_MODEL_ASSIGNMENTS)
        self.assertIn("opus", EXPECTED_MODEL_ASSIGNMENTS)
        
        for model, agents in EXPECTED_MODEL_ASSIGNMENTS.items():
            self.assertIsInstance(agents, list)
            self.assertGreater(len(agents), 0, f"Model {model} should have at least one agent")
            
            for agent in agents:
                self.assertIsInstance(agent, str)
                self.assertGreater(len(agent), 0, f"Agent name should not be empty")

    def test_model_assignment_completeness(self):
        """Test that model assignments cover all expected agents."""
        all_assigned_agents = set()
        for agents in EXPECTED_MODEL_ASSIGNMENTS.values():
            all_assigned_agents.update(agents)
        
        # Should have a reasonable number of agents (at least 50)
        self.assertGreater(len(all_assigned_agents), 50, "Should have assignments for many agents")
        
        # No duplicates across models
        total_count = sum(len(agents) for agents in EXPECTED_MODEL_ASSIGNMENTS.values())
        self.assertEqual(len(all_assigned_agents), total_count, "No agent should be assigned to multiple models")

    def test_critical_agents_use_opus(self):
        """Test that critical agents are assigned to Opus model."""
        opus_agents = set(EXPECTED_MODEL_ASSIGNMENTS['opus'])
        critical_agents = {
            'security-auditor', 'incident-responder', 'ai-engineer', 
            'cloud-architect', 'performance-engineer'
        }
        
        for agent in critical_agents:
            self.assertIn(agent, opus_agents, f"Critical agent {agent} should use Opus model")

    def test_simple_agents_use_haiku(self):
        """Test that simple agents are assigned to Haiku model."""
        haiku_agents = set(EXPECTED_MODEL_ASSIGNMENTS['haiku'])
        simple_agents = {
            'data-scientist', 'business-analyst', 'content-marketer', 
            'customer-support', 'sales-automator'
        }
        
        for agent in simple_agents:
            self.assertIn(agent, haiku_agents, f"Simple agent {agent} should use Haiku model")


class TestValidationIntegration(unittest.TestCase):
    """Integration tests for validation functionality."""

    def test_audit_function_basic(self):
        """Test that audit function runs without errors."""
        # This is more of a smoke test since it depends on actual files
        try:
            # Save current directory
            original_dir = os.getcwd()
            
            # Change to a temporary directory to avoid affecting real files
            temp_dir = tempfile.mkdtemp()
            os.chdir(temp_dir)
            
            # Create a simple test agent file
            with open("test-agent.md", "w") as f:
                f.write("""---
name: test-agent
description: Test agent
model: sonnet
---

Test agent content""")
            
            # Run audit (should handle the case where most expected agents don't exist)
            result = audit_model_assignments()
            
            # Should return a dictionary with expected keys
            self.assertIsInstance(result, dict)
            expected_keys = ['haiku', 'sonnet', 'opus', 'missing', 'errors']
            for key in expected_keys:
                self.assertIn(key, result)
                self.assertIsInstance(result[key], list)
            
        finally:
            # Restore directory and clean up
            os.chdir(original_dir)
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)