#!/usr/bin/env python3
"""
Unit tests for enhanced CRM functionality.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'our-crm-ai'))

from crm_enhanced import validate_task_id, retry_api_call, make_api_request


class TestCRMEnhanced(unittest.TestCase):
    """Test cases for enhanced CRM functionality."""

    def test_validate_task_id_valid_uuid(self):
        """Test validation of valid UUID task IDs."""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000",
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        ]
        
        for uuid in valid_uuids:
            self.assertTrue(validate_task_id(uuid), f"Should validate UUID: {uuid}")

    def test_validate_task_id_valid_alphanumeric(self):
        """Test validation of valid alphanumeric task IDs."""
        valid_ids = [
            "abc12345",
            "task123xyz",
            "project-123-abc",
            "longertaskid12345"
        ]
        
        for task_id in valid_ids:
            self.assertTrue(validate_task_id(task_id), f"Should validate ID: {task_id}")

    def test_validate_task_id_invalid(self):
        """Test validation rejects invalid task IDs."""
        invalid_ids = [
            "",  # Empty
            "   ",  # Whitespace only
            "short",  # Too short
            "task@123",  # Invalid characters
            "task id space",  # Spaces
            "task/123",  # Slash
            None,  # None type
            123,  # Non-string
            "task'injection",  # SQL injection attempt
        ]
        
        for task_id in invalid_ids:
            self.assertFalse(validate_task_id(task_id), f"Should reject ID: {task_id}")

    def test_validate_task_id_edge_cases(self):
        """Test validation edge cases."""
        # Minimum length boundary
        self.assertFalse(validate_task_id("1234567"))  # 7 chars - too short
        self.assertTrue(validate_task_id("12345678"))  # 8 chars - minimum valid
        
        # Mixed case
        self.assertTrue(validate_task_id("AbC123-xyz"))

    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_api_call_success(self, mock_sleep):
        """Test retry decorator with successful API call."""
        @retry_api_call(max_retries=3, delay=0.1)
        def mock_api_call():
            return "success"
        
        result = mock_api_call()
        self.assertEqual(result, "success")
        mock_sleep.assert_not_called()  # Should not retry on success

    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_retry_api_call_with_retries(self, mock_sleep):
        """Test retry decorator with eventual success."""
        call_count = 0
        
        @retry_api_call(max_retries=3, delay=0.1)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API error")
            return "success"
        
        result = mock_api_call()
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # Should retry twice

    @patch('time.sleep')
    def test_retry_api_call_max_retries_exceeded(self, mock_sleep):
        """Test retry decorator when max retries exceeded."""
        @retry_api_call(max_retries=2, delay=0.1)
        def mock_api_call():
            raise Exception("Persistent API error")
        
        with self.assertRaises(Exception) as context:
            mock_api_call()
        
        self.assertEqual(str(context.exception), "Persistent API error")
        self.assertEqual(mock_sleep.call_count, 1)  # Should retry 1 time

    @patch('requests.request')
    def test_make_api_request_defaults(self, mock_request):
        """Test that make_api_request applies correct defaults."""
        mock_response = Mock()
        mock_request.return_value = mock_response
        
        # Call without timeout
        make_api_request("GET", "https://api.example.com/test")
        
        # Check that defaults were applied
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        
        self.assertEqual(kwargs['timeout'], 30)  # DEFAULT_TIMEOUT
        self.assertEqual(kwargs['verify'], True)  # SSL verification
        self.assertIn('headers', kwargs)

    @patch('requests.request')
    def test_make_api_request_preserves_custom_args(self, mock_request):
        """Test that make_api_request preserves custom arguments."""
        mock_response = Mock()
        mock_request.return_value = mock_response
        
        custom_headers = {"Custom-Header": "value"}
        
        # Call with custom arguments
        make_api_request("POST", "https://api.example.com/test", 
                        timeout=60, headers=custom_headers, json={"data": "test"})
        
        args, kwargs = mock_request.call_args
        
        self.assertEqual(kwargs['timeout'], 60)  # Custom timeout preserved
        self.assertEqual(kwargs['headers'], custom_headers)  # Custom headers preserved
        self.assertEqual(kwargs['json'], {"data": "test"})  # Custom JSON preserved


class TestCRMSecurityFeatures(unittest.TestCase):
    """Test security-related features of enhanced CRM."""

    def test_task_id_injection_prevention(self):
        """Test that task ID validation prevents injection attacks."""
        injection_attempts = [
            "'; DROP TABLE tasks; --",
            "../../../etc/passwd",
            "<script>alert('xss')</script>",
            "task'; DELETE FROM users; --",
            "admin'/**/UNION/**/SELECT/**/password/**/FROM/**/users--",
        ]
        
        for injection in injection_attempts:
            self.assertFalse(
                validate_task_id(injection), 
                f"Should reject injection attempt: {injection}"
            )

    def test_api_security_headers(self):
        """Test that API requests include security headers."""
        # This would need more sophisticated mocking for full testing
        # but validates the structure is in place
        from crm_enhanced import HEADERS, DEFAULT_TIMEOUT
        
        self.assertIn("Authorization", HEADERS)
        self.assertIn("Content-Type", HEADERS)
        self.assertEqual(HEADERS["Content-Type"], "application/json")
        
        # Verify timeout is reasonable
        self.assertGreater(DEFAULT_TIMEOUT, 0)
        self.assertLess(DEFAULT_TIMEOUT, 120)  # Not too long


if __name__ == '__main__':
    unittest.main(verbosity=2)