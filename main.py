from constants import REQUESTING_MEMBER_WSDL, PRIVATE_KEY_PATH, PUBLIC_KEY_PATH, PRIVATE_KEY_FILE, PUBLIC_KEY_FILE
from plugin import encryptPlugin
import zeep
from zeep.wsse.signature import Signature
from pathlib import Path
from zeep.transports import Transport
from requests import Session
from zeep.plugins import HistoryPlugin
from lxml import etree
from zeep.wsse.utils import WSU
from signature_service import BinarySignatureTimestamp
import datetime
from crypto import encrypt, decrypt, encode


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

    secureXHeader = soap.get_type('ns3:SecureXHeader')
    header = secureXHeader(ConsumerBusinessUnit='your_business_unit_here',
                           ConsumerReference='your_reference_here', 
                           ExchangeReference='your_exchange_reference_here',
                           InitiatingIP='your_ip_here',
                           ProductId='your_product_id_here',
                           ProviderBusinessUnit='your_business_unit_here',
                           ProviderReference='your_reference_here',
                           TransactionStatus='your_status_here')

    Entity = soap.get_type('ns1:Entity')
    entity = Entity(IdentificationNo='foo', 
                    IdentificationType='foo', 
                    Initials='foo',
                    Name='foo')

    ArrayOfEntity = soap.get_type('ns1:ArrayOfEntity')
    array_of_entity = ArrayOfEntity(Entity=[entity])

    IDXConsumerSubmitMessage = soap.get_type('ns1:IDXConsumerSubmitMessage')
    body = IDXConsumerSubmitMessage(AccountNumber='your_account_number_here',
                                    AccountType='your_reference_here',
                                    BranchCode='your_exchange_reference_here',
                                    DateFrom='your_ip_here',
                                    DateTo='your_product_id_here',
                                    EmailAddress='your_business_unit_here',
                                    JointAccount='your_reference_here',
                                    PhysicalEntities=array_of_entity)

    # Serialize the body to a string
    body_str = zeep.helpers.serialize_object(body)
    body_str = str(body_str)

    soap.settings.raw_response = True
    # Replace 'Submit' with the correct operation name and parameters
    result = soap.service.Submit(encrypt(body_str), _soapheaders={'Header': header})
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