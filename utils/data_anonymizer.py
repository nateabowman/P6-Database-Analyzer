"""Data anonymization utilities for PII protection."""

import re
from typing import Any, Dict, List, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)


class DataAnonymizer:
    """Anonymizes personally identifiable information (PII)."""
    
    # Patterns for detecting PII
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b')
    IP_ADDRESS_PATTERN = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    
    def __init__(self, anonymization_level: str = "medium"):
        """
        Initialize data anonymizer.
        
        Args:
            anonymization_level: Level of anonymization (low, medium, high)
        """
        self.anonymization_level = anonymization_level
    
    def anonymize_text(self, text: str) -> str:
        """
        Anonymize PII in text.
        
        Args:
            text: Text to anonymize
        
        Returns:
            Anonymized text
        """
        if not text:
            return text
        
        # Anonymize emails
        text = self.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)
        
        # Anonymize phone numbers
        text = self.PHONE_PATTERN.sub('[PHONE_REDACTED]', text)
        
        # Anonymize SSN
        text = self.SSN_PATTERN.sub('[SSN_REDACTED]', text)
        
        # Anonymize credit cards
        text = self.CREDIT_CARD_PATTERN.sub('[CARD_REDACTED]', text)
        
        # Anonymize IP addresses
        if self.anonymization_level in ['medium', 'high']:
            text = self.IP_ADDRESS_PATTERN.sub('[IP_REDACTED]', text)
        
        return text
    
    def anonymize_dict(self, data: Dict[str, Any], fields_to_anonymize: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Anonymize PII in dictionary.
        
        Args:
            data: Dictionary to anonymize
            fields_to_anonymize: Specific fields to anonymize (if None, auto-detect)
        
        Returns:
            Anonymized dictionary
        """
        anonymized = {}
        
        # Common PII field names
        pii_fields = fields_to_anonymize or [
            'email', 'phone', 'ssn', 'credit_card', 'ip_address',
            'username', 'password', 'name', 'address'
        ]
        
        for key, value in data.items():
            key_lower = key.lower()
            
            if any(pii_field in key_lower for pii_field in pii_fields):
                anonymized[key] = '[REDACTED]'
            elif isinstance(value, str):
                anonymized[key] = self.anonymize_text(value)
            elif isinstance(value, dict):
                anonymized[key] = self.anonymize_dict(value, fields_to_anonymize)
            elif isinstance(value, list):
                anonymized[key] = [
                    self.anonymize_dict(item, fields_to_anonymize) if isinstance(item, dict)
                    else self.anonymize_text(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                anonymized[key] = value
        
        return anonymized
    
    def detect_pii(self, text: str) -> List[Dict[str, str]]:
        """
        Detect PII in text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of detected PII with types
        """
        detected = []
        
        # Detect emails
        for match in self.EMAIL_PATTERN.finditer(text):
            detected.append({'type': 'email', 'value': match.group(), 'position': match.span()})
        
        # Detect phone numbers
        for match in self.PHONE_PATTERN.finditer(text):
            detected.append({'type': 'phone', 'value': match.group(), 'position': match.span()})
        
        # Detect SSN
        for match in self.SSN_PATTERN.finditer(text):
            detected.append({'type': 'ssn', 'value': match.group(), 'position': match.span()})
        
        return detected


# Global anonymizer instance
_anonymizer: Optional[DataAnonymizer] = None


def get_anonymizer(level: str = "medium") -> DataAnonymizer:
    """Get the global data anonymizer instance."""
    global _anonymizer
    if _anonymizer is None or _anonymizer.anonymization_level != level:
        _anonymizer = DataAnonymizer(level)
    return _anonymizer

