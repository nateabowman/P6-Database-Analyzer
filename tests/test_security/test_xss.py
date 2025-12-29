"""Tests for XSS prevention."""

import pytest
from utils.security import SecurityValidator


class TestXSSPrevention:
    """Test cases for XSS prevention."""
    
    def test_xss_in_html_output(self):
        """Test that XSS attempts are escaped in HTML output."""
        xss_attempts = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<body onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='evil.com'></iframe>",
            "<svg onload=alert('XSS')>",
        ]
        
        for xss_attempt in xss_attempts:
            sanitized = SecurityValidator.sanitize_for_html(xss_attempt)
            assert "<script>" not in sanitized
            assert "onerror=" not in sanitized
            assert "onload=" not in sanitized
            assert "javascript:" not in sanitized.lower()
            assert "&lt;" in sanitized or "&gt;" in sanitized
    
    def test_html_escaping_complete(self):
        """Test that all HTML special characters are escaped."""
        test_cases = {
            "<": "&lt;",
            ">": "&gt;",
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;",
        }
        
        for char, expected_escape in test_cases.items():
            result = SecurityValidator.sanitize_for_html(char)
            assert expected_escape in result
    
    def test_safe_html_preserved(self):
        """Test that safe HTML-like text is still escaped."""
        safe_text = "This is <b>bold</b> text"
        sanitized = SecurityValidator.sanitize_for_html(safe_text)
        # Should be escaped, not interpreted
        assert "&lt;b&gt;" in sanitized
        assert "<b>" not in sanitized

