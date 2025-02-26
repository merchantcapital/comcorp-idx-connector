import os
import sys
import pytest
from unittest.mock import patch, mock_open
from pathlib import Path

# Patch the constants before the modules are imported
def pytest_configure(config):
    """Configure pytest before test collection."""
    # Create mock for open function
    mock_file = mock_open(read_data='mock key data')
    
    # Apply patches
    patch('builtins.open', mock_file).start()
    
    # Mock key data
    mock_private_key = "-----BEGIN PRIVATE KEY-----\nMOCK_PRIVATE_KEY_DATA\n-----END PRIVATE KEY-----"
    mock_public_key = "-----BEGIN CERTIFICATE-----\nMOCK_PUBLIC_KEY_DATA\n-----END CERTIFICATE-----"
    
    # Patch the constants in app.constants
    sys.modules['app.constants'] = type('MockConstants', (), {
        # WSDL paths
        'REQUESTING_MEMBER_WSDL': 'wsdl/requesting_member.wsdl',
        'PROVIDER_RESPONSE_WSDL': 'wsdl/provider_response.wsdl',
        
        # Path objects
        'PRIVATE_KEY_PATH': Path('certs/private_key.pem'),
        'PUBLIC_KEY_PATH': Path('certs/comcorp_uat.crt'),
        
        # File paths as strings
        'PRIVATE_KEY_FILE': 'certs/private_key.pem',
        'PUBLIC_KEY_FILE': 'certs/public_key.pem',
        
        # Key contents
        'PRIVATE_KEY': mock_private_key,
        'PUBLIC_KEY': mock_public_key,
        
        # Namespaces
        'SOAP_NS': 'http://www.w3.org/2003/05/soap-envelope',
        'DS_NS': 'http://www.w3.org/2000/09/xmldsig#',
        'ENC_NS': 'http://www.w3.org/2001/04/xmlenc#',
        'WSS_BASE': 'http://docs.oasis-open.org/wss/2004/01/',
        'WSSE_NS': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
        'WSU_NS': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
        'BASE64B': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary',
        'X509TOKEN': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3'
    })