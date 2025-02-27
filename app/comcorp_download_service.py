import os
from flask import request, jsonify, Response
from functools import wraps
import zeep
from zeep.plugins import HistoryPlugin
from lxml import etree
import logging
import base64

from app import app
from app.constants import REQUESTING_MEMBER_WSDL, PRIVATE_KEY_FILE, PUBLIC_KEY_FILE
from app.plugin import encryptPlugin
from app.signature_service import BinarySignatureTimestamp
from app.object_service import getHeader, getDecryptedBody

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_auth(username, password):
    """Check if the provided username and password match the environment variables."""
    expected_username = os.getenv('BASIC_AUTH_USERNAME')
    expected_password = os.getenv('BASIC_AUTH_PASSWORD')
    return username == expected_username and password == expected_password

def authenticate():
    """Send a 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials',
        401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )

def requires_auth(f):
    """Decorator that requires basic authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

@app.route('/comcorp-download-request', methods=['POST'])
@requires_auth
def comcorp_download_request():
    """
    REST endpoint for comcorp-download-request.
    
    Receives a JSON payload with parameters for the SOAP request,
    makes the SOAP request, and returns the response.
    
    Expected JSON payload:
    {
        "AccountNumber": "string",
        "AccountType": "string",
        "BranchCode": "string",
        "DateFrom": "string",
        "DateTo": "string",
        "EmailAddress": "string",
        "JointAccount": "string",
        "PhysicalEntities": [
            {
                "IdentificationNo": "string",
                "IdentificationType": "string",
                "Initials": "string",
                "Name": "string"
            }
        ]
    }
    
    Returns:
        JSON response containing the SOAP response or error details
    """
    try:
        # Get the JSON payload
        payload = request.json
        if not payload:
            return jsonify({
                'status': 'error',
                'message': 'No JSON payload provided'
            }), 400
        
        logger.info(f"Received request with payload: {payload}")
        
        # Initialize SOAP client
        encrypt_plugin = encryptPlugin()
        history = HistoryPlugin()
        private_key_filename = PRIVATE_KEY_FILE
        public_key_filename = PUBLIC_KEY_FILE
        
        # Try to load WSDL with absolute path first, then fall back to relative path
        try:
            # Absolute path for Docker container
            wsdl_path = f"/app/wsdl/{REQUESTING_MEMBER_WSDL}"
            logger.info(f"Attempting to load WSDL from: {wsdl_path}")
            
            soap = zeep.Client(
                wsdl=wsdl_path, 
                service_name="ConsumerDecryptedService",
                port_name="CustomBinding_IConsumerDecryptedService",
                wsse=BinarySignatureTimestamp(private_key_filename, public_key_filename, ''),
                plugins=[encrypt_plugin, history]
            )
            logger.info("WSDL loaded successfully using absolute path")
        except FileNotFoundError:
            # Relative path for local development
            wsdl_path = f"wsdl/{REQUESTING_MEMBER_WSDL}"
            logger.info(f"Absolute path failed, trying relative path: {wsdl_path}")
            
            soap = zeep.Client(
                wsdl=wsdl_path, 
                service_name="ConsumerDecryptedService",
                port_name="CustomBinding_IConsumerDecryptedService",
                wsse=BinarySignatureTimestamp(private_key_filename, public_key_filename, ''),
                plugins=[encrypt_plugin, history]
            )
            logger.info("WSDL loaded successfully using relative path")
        
        # Get header and body
        header = getHeader(soap)
        body = getDecryptedBody(soap, payload)
        
        # Make SOAP request
        result = soap.service.Submit(body, _soapheaders={'Header': header})
        
        # Convert result to a serializable format
        response_data = {}
        
        # Process the result based on its type
        if hasattr(result, '__dict__'):
            # If result is an object with attributes
            for key, value in result.__dict__.items():
                if key.startswith('_'):
                    continue
                response_data[key] = str(value)
        else:
            # If result is a simple type
            response_data['result'] = str(result)
        
        # Add request and response XML for debugging
        debug_info = {}
        try:
            for hist_type, hist in [('request', history.last_sent), ('response', history.last_received)]:
                if hist and 'envelope' in hist:
                    debug_info[f'{hist_type}_xml'] = etree.tostring(hist['envelope'], encoding='unicode', pretty_print=True)
        except (IndexError, TypeError) as e:
            logger.error(f"Error extracting request/response XML: {str(e)}")
        
        # Return the response
        return jsonify({
            'status': 'success',
            'data': response_data,
            'debug': debug_info
        })
    
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500