import zeep
import zeep.xsd
import lxml.builder
from lxml import etree as ET

def getHeader(Client):
    soap = Client

    secureXHeader = soap.get_type('ns3:SecureXHeader')
    header = secureXHeader(ConsumerBusinessUnit='your_business_unit_here',
                           ConsumerReference='your_reference_here', 
                           ExchangeReference='your_exchange_reference_here',
                           InitiatingIP='your_ip_here',
                           ProductId='your_product_id_here',
                           ProviderBusinessUnit='your_business_unit_here',
                           ProviderReference='your_reference_here',
                           TransactionStatus='your_status_here')
    
    return header


def getDecryptedBody(Client, params=None):
    """
    Create a SOAP request body for IDXConsumerSubmitMessage with the provided parameters.
    
    Args:
        Client: The SOAP client instance
        params: A dictionary containing the parameters for the request body:
                - AccountNumber: The account number
                - AccountType: The account type
                - BranchCode: The branch code
                - DateFrom: The start date
                - DateTo: The end date
                - EmailAddress: The email address
                - JointAccount: Whether it's a joint account
                - PhysicalEntities: A list of dictionaries with entity details
                  (IdentificationNo, IdentificationType, Initials, Name)
    
    Returns:
        The SOAP request body
    """
    soap = Client

    # Use default values if params is not provided
    if params is None:
        return
    
    # Create entities
    Entity = soap.get_type('ns1:Entity')
    entities = []
    
    # If PhysicalEntities is provided, use them
    if 'PhysicalEntities' in params and params['PhysicalEntities']:
        for entity_data in params['PhysicalEntities']:
            entity = Entity(
                IdentificationNo=entity_data.get('IdentificationNo', ''),
                IdentificationType=entity_data.get('IdentificationType', ''),
                Initials=entity_data.get('Initials', ''),
                Name=entity_data.get('Name', '')
            )
            entities.append(entity)

    ArrayOfEntity = soap.get_type('ns1:ArrayOfEntity')
    array_of_entity = ArrayOfEntity(Entity=entities)

    IDXConsumerSubmitMessage = soap.get_type('ns1:IDXConsumerSubmitMessage')
    body = IDXConsumerSubmitMessage(
        AccountNumber=params.get('AccountNumber', ''),
        AccountType=params.get('AccountType', ''),
        BranchCode=params.get('BranchCode', ''),
        DateFrom=params.get('DateFrom', ''),
        DateTo=params.get('DateTo', ''),
        EmailAddress=params.get('EmailAddress', ''),
        JointAccount=params.get('JointAccount', ''),
        PhysicalEntities=array_of_entity
    )
    
    return body