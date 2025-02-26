import os
import sys
import pytest
from unittest.mock import patch, mock_open

# Patch the constants before the modules are imported
def pytest_configure(config):
    """Configure pytest before test collection."""
    # Create mock for open function
    mock_file = mock_open(read_data='mock key data')
    
    # Apply patches
    patch('builtins.open', mock_file).start()
    
    # Patch the constants in app.constants
    sys.modules['app.constants'] = type('MockConstants', (), {
        'REQUESTING_MEMBER_WSDL': 'wsdl/requesting_member.wsdl',
        'PROVIDER_RESPONSE_WSDL': 'wsdl/provider_response.wsdl',
        'PRIVATE_KEY_FILE': 'certs/private_key.pem',
        'PUBLIC_KEY_FILE': 'certs/public_key.pem',
        'WSSE_NS': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd',
        'WSU_NS': 'http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd',
        'SOAP_NS': 'http://www.w3.org/2003/05/soap-envelope',
        'DS_NS': 'http://www.w3.org/2000/09/xmldsig#',
        'ENC_NS': 'http://www.w3.org/2001/04/xmlenc#'
    })