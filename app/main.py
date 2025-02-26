from app.constants import REQUESTING_MEMBER_WSDL, PRIVATE_KEY_FILE, PUBLIC_KEY_FILE
from app.plugin import encryptPlugin
import zeep
import zeep.xsd
from zeep.plugins import HistoryPlugin
from lxml import etree
from app.signature_service import BinarySignatureTimestamp
from app.object_service import getHeader, getDecryptedBody


def main():
    encrypt_Plugin = encryptPlugin()
    history = HistoryPlugin()
    wsdl = REQUESTING_MEMBER_WSDL
    private_key_filename = PRIVATE_KEY_FILE
    public_key_filename = PUBLIC_KEY_FILE
    
    soap = zeep.Client(wsdl=wsdl, 
                       service_name="ConsumerDecryptedService",
                       port_name="CustomBinding_IConsumerDecryptedService",
                       wsse=BinarySignatureTimestamp(private_key_filename, public_key_filename, ''),
                       plugins=[encrypt_Plugin, history])

    header = getHeader(soap)
    body = getDecryptedBody(soap)                

    # soap.settings.raw_response = True
    result = soap.service.Submit(body, _soapheaders={'Header': header})
    print(result)

    print(history.last_sent)
    print(history.last_received)
    try:
        for hist in [history.last_sent, history.last_received]:
            print(etree.tostring(hist["envelope"], encoding="unicode", pretty_print=True))
    except (IndexError, TypeError):
        # catch cases where it fails before being put on the wire
        pass
    

if __name__ == '__main__':
    main()