from pathlib import Path
import os

REQUESTING_MEMBER_WSDL = 'RequestingMemberSubmitService.wsdl'
PROVIDER_RESPONSE_WSDL = 'ProviderResponseService.wsdl'

# Use paths relative to the Docker container working directory
PRIVATE_KEY_PATH = Path('certs/private_key.pem')
PUBLIC_KEY_PATH = Path('certs/comcorp_uat.crt')

PRIVATE_KEY_FILE = 'certs/private_key.pem'
PUBLIC_KEY_FILE = 'certs/comcorp.cer'

# Load the keys into memory only if the files exist
try:
    with open(PRIVATE_KEY_PATH, 'r') as key_file:
        PRIVATE_KEY = key_file.read()
        
    with open(PUBLIC_KEY_PATH, 'r') as cert_file:
        PUBLIC_KEY = cert_file.read()
except FileNotFoundError:
    # Log the error but don't crash the application
    print(f"Warning: Certificate files not found at {PRIVATE_KEY_PATH} or {PUBLIC_KEY_PATH}")
    PRIVATE_KEY = ""
    PUBLIC_KEY = ""

# SOAP envelope
SOAP_NS = 'http://www.w3.org/2003/05/soap-envelope'
# xmldsig
DS_NS = 'http://www.w3.org/2000/09/xmldsig#'
# xmlenc
ENC_NS = 'http://www.w3.org/2001/04/xmlenc#'

WSS_BASE = 'http://docs.oasis-open.org/wss/2004/01/'
# WS-Security
WSSE_NS = WSS_BASE + 'oasis-200401-wss-wssecurity-secext-1.0.xsd'
# WS-Utility
WSU_NS = WSS_BASE + 'oasis-200401-wss-wssecurity-utility-1.0.xsd'

BASE64B = WSS_BASE + 'oasis-200401-wss-soap-message-security-1.0#Base64Binary'
X509TOKEN = WSS_BASE + 'oasis-200401-wss-x509-token-profile-1.0#X509v3'