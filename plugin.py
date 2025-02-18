from lxml import etree
from zeep import Plugin
from crypto import encrypt

class encryptPlugin(Plugin):

    def ingress(self, envelope, http_headers, operation):
        #print(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        # Format the request body as pretty printed XML
        xml = etree.tostring( envelope, pretty_print = True, encoding = 'unicode')
        print( f'\nRequest\n-------\nHeaders:\n{http_headers}\n\nBody:\n{xml}' )
        #return envelope, http_headers