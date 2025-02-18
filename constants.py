from pathlib import Path

REQUESTING_MEMBER_WSDL = 'RequestingMemberSubmitService.wsdl'
PROVIDER_RESPONSE_WSDL = 'ProviderResponseService.wsdl'

PRIVATE_KEY_PATH = Path('./private_key.pem')
PUBLIC_KEY_PATH = Path('./comcorp_uat.crt')

PRIVATE_KEY_FILE = 'private_key.pem'
PUBLIC_KEY_FILE = 'comcorp_uat.crt'

# Load the keys into memory
with open(PRIVATE_KEY_PATH, 'r') as key_file:
    PRIVATE_KEY = key_file.read()
    
with open(PUBLIC_KEY_PATH, 'r') as cert_file:
    PUBLIC_KEY = cert_file.read()