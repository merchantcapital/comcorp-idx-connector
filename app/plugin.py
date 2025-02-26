from lxml import etree
from zeep import Plugin
from zeep.wsse.utils import get_security_header
from app.crypto_wsse import encrypt
from app.constants import PRIVATE_KEY_FILE, PUBLIC_KEY_FILE

class encryptPlugin(Plugin):

    def ingress(self, envelope, http_headers, operation):
        #print(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        # Format the request body as pretty printed XML
        xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode')

        # Get the security header from the envelope
        security = get_security_header(envelope)
        print(security)

        # Convert the envelope to a string before passing it to the encrypt function
        envelope_str = etree.tostring(envelope, encoding='unicode', pretty_print=True)
        encrypted_envelope = encrypt(envelope_str, PUBLIC_KEY_FILE)

        # Ensure the envelope is an Element object after encryption
        if isinstance(encrypted_envelope, (bytes, str)):
            encrypted_envelope = etree.fromstring(encrypted_envelope)

        xml = etree.tostring(encrypted_envelope, pretty_print=True, encoding='unicode')
        print( f'\nRequest\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}' )

        return encrypted_envelope, http_headers