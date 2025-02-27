from flask import request, Response, jsonify
import zeep
from zeep.wsse.signature import BinarySignature
from lxml import etree
import xmlsec
import base64
from OpenSSL import crypto
import uuid
import logging
from datetime import datetime, timedelta
import pytz

from app.constants import PROVIDER_RESPONSE_WSDL, PRIVATE_KEY_FILE, PUBLIC_KEY_FILE, WSSE_NS, WSU_NS, SOAP_NS, DS_NS, ENC_NS
from app.signature_service import BinarySignatureTimestamp
from app.crypto_wsse import decrypt
from app.xml import ns, ensure_id

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the Flask app instance from the package
from app import app

# Load the WSDL
try:
    # Try absolute path for Docker container
    wsdl_path = f"/app/wsdl/{PROVIDER_RESPONSE_WSDL}"
    logger.info(f"Attempting to load WSDL from: {wsdl_path}")
    client = zeep.Client(wsdl=wsdl_path)
    logger.info("WSDL loaded successfully using absolute path")
except FileNotFoundError:
    # Fall back to relative path for local development
    wsdl_path = f"wsdl/{PROVIDER_RESPONSE_WSDL}"
    logger.info(f"Absolute path failed, trying relative path: {wsdl_path}")
    client = zeep.Client(wsdl=wsdl_path)
    logger.info("WSDL loaded successfully using relative path")

def verify_security(envelope):
    """
    Verify the WS-Security elements of the SOAP envelope.
    
    Args:
        envelope: The SOAP envelope as an lxml Element
        
    Returns:
        A tuple (success, error_message)
    """
    try:
        # Find the Security header
        header = envelope.find(f".//{{{SOAP_NS}}}Header")
        if header is None:
            return False, "No Header element found in the request"
            
        security = header.find(f".//{{{WSSE_NS}}}Security")
        if security is None:
            return False, "No Security element found in the request"
            
        # Verify timestamp
        timestamp = security.find(f".//{{{WSU_NS}}}Timestamp")
        if timestamp is not None:
            created = timestamp.find(f".//{{{WSU_NS}}}Created")
            expires = timestamp.find(f".//{{{WSU_NS}}}Expires")
            
            if created is not None and expires is not None:
                created_time = datetime.fromisoformat(created.text.rstrip('Z'))
                expires_time = datetime.fromisoformat(expires.text.rstrip('Z'))
                now = datetime.now(pytz.UTC)
                
                if now > expires_time:
                    return False, "Security timestamp has expired"
                    
                logger.info(f"Timestamp verified: Created={created.text}, Expires={expires.text}")
        
        # In a production environment, you would also verify the signature
        # using the BinarySignature class from zeep.wsse.signature
        # For now, we'll just log that we would verify it
        signature = security.find(f".//{{{DS_NS}}}Signature")
        if signature is not None:
            logger.info("Signature found, would verify in production")
        
        # In a production environment, you would also decrypt any encrypted parts
        # using the decrypt function from crypto_wsse
        # For now, we'll just log that we would decrypt it
        encrypted_data = envelope.find(f".//{{{ENC_NS}}}EncryptedData")
        if encrypted_data is not None:
            logger.info("EncryptedData found, would decrypt in production")
        
        return True, None
    except Exception as e:
        return False, str(e)

def process_submit_request(envelope):
    """
    Process the Submit operation request from the SOAP envelope.
    
    Args:
        envelope: The SOAP envelope as an lxml Element
        
    Returns:
        A boolean response indicating success
    """
    try:
        # Verify security
        security_verified, error_message = verify_security(envelope)
        if not security_verified:
            logger.error(f"Security verification failed: {error_message}")
            return False
        
        # Extract the header
        header_elem = envelope.find(f".//{{{SOAP_NS}}}Header")
        if header_elem is not None:
            # Extract SecureXHeader
            securex_header = header_elem.find(".//{http://SecureX.Common/V1}Header")
            if securex_header is not None:
                logger.info(f"Received SecureXHeader: {etree.tostring(securex_header)}")
        
        # Extract the body
        body_elem = envelope.find(f".//{{{SOAP_NS}}}Body")
        if body_elem is None:
            logger.error("No Body element found in the request")
            return False
        
        # Process the body content based on the message type
        body_content = body_elem.find(".//*")
        if body_content is None:
            logger.error("No content found in Body element")
            return False
        
        # Identify the message type
        tag_name = etree.QName(body_content).localname
        namespace = etree.QName(body_content).namespace
        
        logger.info(f"Processing message of type: {tag_name} in namespace {namespace}")
        
        # Process based on message type
        if "AvXProviderSubmitMessage" in tag_name:
            return process_avx_message(body_content)
        elif "FicaProviderSubmitMessage" in tag_name:
            return process_fica_message(body_content)
        elif "IDXProviderSubmitMessage" in tag_name:
            return process_idx_message(body_content)
        elif "IVXProviderSubmitMessage" in tag_name:
            return process_ivx_message(body_content)
        else:
            logger.error(f"Unknown message type: {tag_name}")
            return False
    except Exception as e:
        logger.error(f"Error processing Submit request: {str(e)}")
        return False
def process_avx_message(message):
    """
    Process an AvXProviderSubmitMessage.
    
    Args:
        message: The message element
        
    Returns:
        A boolean indicating success
    """
    try:
        logger.info("Processing AvXProviderSubmitMessage")
        
        # Extract AvxResponseDetail if present
        avx_response_detail = message.find(".//{http://AvX.Contract/V1}AvxResponseDetail")
        if avx_response_detail is not None:
            logger.info(f"AvxResponseDetail: {etree.tostring(avx_response_detail)}")
            
            # Process the response details
            for child in avx_response_detail:
                logger.info(f"  {etree.QName(child).localname}: {child.text}")
        
        # Extract SerializedAvxRespose if present
        serialized_response = message.find(".//{http://AvX.Contract/V1}SerializedAvxRespose")
        if serialized_response is not None:
            logger.info(f"SerializedAvxRespose: {etree.tostring(serialized_response)}")
        
        return True
    except Exception as e:
        logger.error(f"Error processing AvXProviderSubmitMessage: {str(e)}")
        return False

def process_fica_message(message):
    """
    Process a FicaProviderSubmitMessage.
    
    Args:
        message: The message element
        
    Returns:
        A boolean indicating success
    """
    try:
        logger.info("Processing FicaProviderSubmitMessage")
        
        # Extract Data if present
        data = message.find(".//{http://FicaX.Contract/V1}Data")
        if data is not None:
            logger.info(f"Data: {etree.tostring(data)}")
        
        # Extract Documents if present
        documents = message.find(".//{http://FicaX.Contract/V1}Documents")
        if documents is not None:
            logger.info(f"Documents: {etree.tostring(documents)}")
        
        # Extract SerializedData if present
        serialized_data = message.find(".//{http://FicaX.Contract/V1}SerializedData")
        if serialized_data is not None:
            logger.info(f"SerializedData: {etree.tostring(serialized_data)}")
        
        # Extract SerializedElements if present
        serialized_elements = message.find(".//{http://FicaX.Contract/V1}SerializedElements")
        if serialized_elements is not None:
            logger.info(f"SerializedElements: {etree.tostring(serialized_elements)}")
        
        return True
    except Exception as e:
        logger.error(f"Error processing FicaProviderSubmitMessage: {str(e)}")
        return False

def process_idx_message(message):
    """
    Process an IDXProviderSubmitMessage.
    
    Args:
        message: The message element
        
    Returns:
        A boolean indicating success
    """
    try:
        logger.info("Processing IDXProviderSubmitMessage")
        
        # Extract account information
        account_name = message.find(".//{http://IDX.Contract/V1}AccountName")
        if account_name is not None:
            logger.info(f"AccountName: {account_name.text}")
        
        account_number = message.find(".//{http://IDX.Contract/V1}AccountNumber")
        if account_number is not None:
            logger.info(f"AccountNumber: {account_number.text}")
        
        account_type = message.find(".//{http://IDX.Contract/V1}AccountType")
        if account_type is not None:
            logger.info(f"AccountType: {account_type.text}")
        
        # Extract Data if present
        data = message.find(".//{http://IDX.Contract/V1}Data")
        if data is not None:
            logger.info(f"Data: {etree.tostring(data)}")
            
            # Process statement data
            for statement_data in data.findall(".//{http://IDX.Contract/V1}StatementData"):
                date_from = statement_data.find(".//{http://IDX.Contract/V1}DateFrom")
                date_to = statement_data.find(".//{http://IDX.Contract/V1}DateTo")
                
                if date_from is not None and date_to is not None:
                    logger.info(f"Statement period: {date_from.text} to {date_to.text}")
                
                # Process transactions
                transactions = statement_data.find(".//{http://IDX.Contract/V1}Transactions")
                if transactions is not None:
                    transaction_count = len(transactions.findall(".//{http://IDX.Contract/V1}Transaction"))
                    logger.info(f"Found {transaction_count} transactions")
        
        # Extract Images if present
        images = message.find(".//{http://IDX.Contract/V1}Images")
        if images is not None:
            image_count = len(images.findall(".//{http://IDX.Contract/V1}StatementImage"))
            logger.info(f"Found {image_count} statement images")
        
        return True
    except Exception as e:
        logger.error(f"Error processing IDXProviderSubmitMessage: {str(e)}")
        return False

def process_ivx_message(message):
    """
    Process an IVXProviderSubmitMessage.
    
    Args:
        message: The message element
        
    Returns:
        A boolean indicating success
    """
    try:
        logger.info("Processing IVXProviderSubmitMessage")
        
        # Extract Data if present
        data = message.find(".//{http://IVX.Contract/V1}Data")
        if data is not None:
            logger.info(f"Data: {etree.tostring(data)}")
            
            # Process payslip data
            for payslip_data in data.findall(".//{http://IVX.Contract/V1}PayslipData"):
                timestamp = payslip_data.find(".//{http://IVX.Contract/V1}TimeStamp")
                if timestamp is not None:
                    logger.info(f"Payslip timestamp: {timestamp.text}")
                
                # Process fields
                fields = payslip_data.find(".//{http://SecureX.Common/V1}Fields")
                if fields is not None:
                    field_count = len(fields.findall(".//{http://SecureX.Common/V1}KeyValuePair"))
                    logger.info(f"Found {field_count} fields")
        
        # Extract Images if present
        images = message.find(".//{http://IVX.Contract/V1}Images")
        if images is not None:
            document_count = len(images.findall(".//{http://SecureX.Common/V1}Document"))
            logger.info(f"Found {document_count} documents")
        
        # Extract SerializedData if present
        serialized_data = message.find(".//{http://IVX.Contract/V1}SerializedData")
        if serialized_data is not None:
            logger.info(f"SerializedData: {etree.tostring(serialized_data)}")
        
        # Extract SerializedImages if present
        serialized_images = message.find(".//{http://IVX.Contract/V1}SerializedImages")
        if serialized_images is not None:
            logger.info(f"SerializedImages: {etree.tostring(serialized_images)}")
        
        return True
    except Exception as e:
        logger.error(f"Error processing IVXProviderSubmitMessage: {str(e)}")
        return False
def create_response(success):
    """
    Create a SOAP response for the Submit operation.
    
    Args:
        success: A boolean indicating whether the operation was successful
        
    Returns:
        An lxml Element containing the SOAP response
    """
    # Create the SOAP envelope
    envelope = etree.Element(f"{{{SOAP_NS}}}Envelope", nsmap={
        'soap': SOAP_NS,
        'wsu': WSU_NS,
        'wsse': WSSE_NS,
        'ds': DS_NS,
        'xenc': ENC_NS
    })
    
    # Create the body
    body = etree.SubElement(envelope, f"{{{SOAP_NS}}}Body")
    
    # Create the response element
    value_elem = etree.SubElement(body, "{http://SecureX.ProviderSubmitService/V1}Value")
    value_elem.text = "true" if success else "false"
    
    return envelope
def add_security_header(envelope):
    """
    Add WS-Security header to the SOAP envelope.
    
    Args:
        envelope: The SOAP envelope as an lxml Element
        
    Returns:
        The modified envelope
    """
    # Create the header if it doesn't exist
    header = envelope.find(f".//{{{SOAP_NS}}}Header")
    if header is None:
        header = etree.Element(f"{{{SOAP_NS}}}Header")
        envelope.insert(0, header)
    
    # Create the Security element
    security = etree.SubElement(header, f"{{{WSSE_NS}}}Security")
    security.set(f"{{{SOAP_NS}}}mustUnderstand", "1")
    
    # Add timestamp
    utc = pytz.UTC
    created = datetime.now(utc)
    expires = created + timedelta(minutes=5)
    
    timestamp = etree.SubElement(security, f"{{{WSU_NS}}}Timestamp")
    ensure_id(timestamp)
    
    created_elem = etree.SubElement(timestamp, f"{{{WSU_NS}}}Created")
    created_elem.text = created.replace(microsecond=0).isoformat() + 'Z'
    
    expires_elem = etree.SubElement(timestamp, f"{{{WSU_NS}}}Expires")
    expires_elem.text = expires.replace(microsecond=0).isoformat() + 'Z'
    
    # In a production environment, you would also add a signature
    # using the BinarySignatureTimestamp class
    
    return envelope
def create_fault_response(code, errors):
    """
    Create a SOAP fault response.
    
    Args:
        code: The fault code
        errors: A list of error messages
        
    Returns:
        An lxml Element containing the SOAP fault response
    """
    # Create the SOAP envelope
    envelope = etree.Element(f"{{{SOAP_NS}}}Envelope", nsmap={
        'soap': SOAP_NS,
        'wsu': WSU_NS,
        'wsse': WSSE_NS,
        'ds': DS_NS,
        'xenc': ENC_NS
    })
    
    # Create the body
    body = etree.SubElement(envelope, f"{{{SOAP_NS}}}Body")
    
    # Create the fault element
    fault = etree.SubElement(body, f"{{{SOAP_NS}}}Fault")
    
    # Add fault code and reason
    code_elem = etree.SubElement(fault, "Code")
    code_elem.text = str(code)
    
    # Add fault details
    detail = etree.SubElement(fault, "Detail")
    securex_fault = etree.SubElement(detail, "{http://SecureX.Fault/V1}SecureXFault")
    
    # Add code and errors
    code_elem = etree.SubElement(securex_fault, "Code")
    code_elem.text = str(code)
    
    errors_elem = etree.SubElement(securex_fault, "Errors")
    for error in errors:
        error_elem = etree.SubElement(errors_elem, "string")
        error_elem.text = error
    
    # Add security header
    envelope = add_security_header(envelope)
    
    return envelope
@app.route('/ProviderResponseService', methods=['POST'])
def provider_response_service():
    """
    Handle incoming SOAP requests for the ProviderResponseService.
    """
    try:
        # Get the request content
        content = request.data
        
        # Parse the SOAP envelope
        envelope = etree.fromstring(content)
        
        # Process the request
        success = process_submit_request(envelope)
        
        # Create the response
        response_envelope = create_response(success)
        
        # Convert the response to XML
        response_xml = etree.tostring(response_envelope, encoding='utf-8', xml_declaration=True)
        
        # Return the response
        return Response(response_xml, mimetype='application/soap+xml')
    
    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        
        # Create a fault response
        fault_envelope = create_fault_response(500, [str(e)])
        
        # Convert the fault to XML
        fault_xml = etree.tostring(fault_envelope, encoding='utf-8', xml_declaration=True)
        
        # Return the fault
        return Response(fault_xml, mimetype='application/soap+xml', status=500)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring.
    Returns a 200 OK response if the service is healthy.
    """
    try:
        # Check if WSDL is loaded
        if client is not None:
            return jsonify({
                'status': 'healthy',
                'service': 'mcauto-soap-client',
                'timestamp': datetime.now(pytz.UTC).isoformat()
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'service': 'mcauto-soap-client',
                'reason': 'WSDL not loaded',
                'timestamp': datetime.now(pytz.UTC).isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'service': 'mcauto-soap-client',
            'reason': str(e),
            'timestamp': datetime.now(pytz.UTC).isoformat()
        }), 500

# This is only used when running the file directly, not when imported
if __name__ == '__main__':
    logger.info(f"Starting ProviderResponseService on http://localhost:5000/ProviderResponseService")
    app.run(debug=True)