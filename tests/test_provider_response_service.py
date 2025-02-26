import unittest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
from flask import Flask
from lxml import etree
from datetime import datetime, timedelta
import pytz

# Import the app and the service to test
from app import app
from app.provider_response_service import (
    verify_security, process_submit_request, process_avx_message,
    process_fica_message, process_idx_message, process_ivx_message,
    create_response, add_security_header, create_fault_response,
    provider_response_service, health_check
)
from app.constants import WSSE_NS, WSU_NS, SOAP_NS, DS_NS, ENC_NS


class TestProviderResponseService(unittest.TestCase):
    """Test cases for the Provider Response Service."""

    def setUp(self):
        """Set up test client and other test variables."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create a basic SOAP envelope for testing
        self.soap_envelope = etree.Element(f"{{{SOAP_NS}}}Envelope", nsmap={
            'soap': SOAP_NS,
            'wsu': WSU_NS,
            'wsse': WSSE_NS,
            'ds': DS_NS
        })
        
        # Add header and body
        self.header = etree.SubElement(self.soap_envelope, f"{{{SOAP_NS}}}Header")
        self.body = etree.SubElement(self.soap_envelope, f"{{{SOAP_NS}}}Body")
        
        # Add security element to header
        self.security = etree.SubElement(self.header, f"{{{WSSE_NS}}}Security")
        
        # Add timestamp to security
        self.timestamp = etree.SubElement(self.security, f"{{{WSU_NS}}}Timestamp")
        
        # Add created and expires elements to timestamp
        utc = pytz.UTC
        created = datetime.now(utc)
        expires = created + timedelta(minutes=5)
        
        self.created = etree.SubElement(self.timestamp, f"{{{WSU_NS}}}Created")
        self.created.text = created.replace(microsecond=0).isoformat() + 'Z'
        
        self.expires = etree.SubElement(self.timestamp, f"{{{WSU_NS}}}Expires")
        self.expires.text = expires.replace(microsecond=0).isoformat() + 'Z'

    def test_verify_security_success(self):
        """Test verify_security with valid security elements."""
        # Add signature element
        signature = etree.SubElement(self.security, f"{{{DS_NS}}}Signature")
        
        # Verify security
        result, error = verify_security(self.soap_envelope)
        self.assertTrue(result)
        self.assertIsNone(error)

    def test_verify_security_no_header(self):
        """Test verify_security with no header."""
        # Remove header
        self.soap_envelope.remove(self.header)
        
        # Verify security
        result, error = verify_security(self.soap_envelope)
        self.assertFalse(result)
        self.assertEqual(error, "No Header element found in the request")

    def test_verify_security_no_security(self):
        """Test verify_security with no security element."""
        # Remove security
        self.header.remove(self.security)
        
        # Verify security
        result, error = verify_security(self.soap_envelope)
        self.assertFalse(result)
        self.assertEqual(error, "No Security element found in the request")

    def test_verify_security_expired_timestamp(self):
        """Test verify_security with expired timestamp."""
        # Set expires to a past time
        utc = pytz.UTC
        past_time = datetime.now(utc) - timedelta(minutes=5)
        self.expires.text = past_time.replace(microsecond=0).isoformat() + 'Z'
        
        # Verify security
        result, error = verify_security(self.soap_envelope)
        self.assertFalse(result)
        self.assertEqual(error, "Security timestamp has expired")

    def test_process_submit_request_security_failure(self):
        """Test process_submit_request with security verification failure."""
        # Remove security
        self.header.remove(self.security)
        
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertFalse(result)

    def test_process_submit_request_no_body(self):
        """Test process_submit_request with no body element."""
        # Remove body
        self.soap_envelope.remove(self.body)
        
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertFalse(result)

    def test_process_submit_request_empty_body(self):
        """Test process_submit_request with empty body."""
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertFalse(result)

    @patch('app.provider_response_service.process_avx_message')
    def test_process_submit_request_avx_message(self, mock_process_avx):
        """Test process_submit_request with AvXProviderSubmitMessage."""
        # Mock process_avx_message to return True
        mock_process_avx.return_value = True
        
        # Add AvXProviderSubmitMessage to body
        avx_message = etree.SubElement(self.body, "{http://AvX.Contract/V1}AvXProviderSubmitMessage")
        
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertTrue(result)
        mock_process_avx.assert_called_once_with(avx_message)

    @patch('app.provider_response_service.process_fica_message')
    def test_process_submit_request_fica_message(self, mock_process_fica):
        """Test process_submit_request with FicaProviderSubmitMessage."""
        # Mock process_fica_message to return True
        mock_process_fica.return_value = True
        
        # Add FicaProviderSubmitMessage to body
        fica_message = etree.SubElement(self.body, "{http://FicaX.Contract/V1}FicaProviderSubmitMessage")
        
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertTrue(result)
        mock_process_fica.assert_called_once_with(fica_message)

    @patch('app.provider_response_service.process_idx_message')
    def test_process_submit_request_idx_message(self, mock_process_idx):
        """Test process_submit_request with IDXProviderSubmitMessage."""
        # Mock process_idx_message to return True
        mock_process_idx.return_value = True
        
        # Add IDXProviderSubmitMessage to body
        idx_message = etree.SubElement(self.body, "{http://IDX.Contract/V1}IDXProviderSubmitMessage")
        
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertTrue(result)
        mock_process_idx.assert_called_once_with(idx_message)

    @patch('app.provider_response_service.process_ivx_message')
    def test_process_submit_request_ivx_message(self, mock_process_ivx):
        """Test process_submit_request with IVXProviderSubmitMessage."""
        # Mock process_ivx_message to return True
        mock_process_ivx.return_value = True
        
        # Add IVXProviderSubmitMessage to body
        ivx_message = etree.SubElement(self.body, "{http://IVX.Contract/V1}IVXProviderSubmitMessage")
        
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertTrue(result)
        mock_process_ivx.assert_called_once_with(ivx_message)

    def test_process_submit_request_unknown_message(self):
        """Test process_submit_request with unknown message type."""
        # Add unknown message to body
        etree.SubElement(self.body, "{http://Unknown.Contract/V1}UnknownMessage")
        
        # Process request
        result = process_submit_request(self.soap_envelope)
        self.assertFalse(result)

    def test_process_avx_message(self):
        """Test process_avx_message."""
        # Create AvXProviderSubmitMessage
        avx_message = etree.Element("{http://AvX.Contract/V1}AvXProviderSubmitMessage")
        
        # Add AvxResponseDetail
        avx_response_detail = etree.SubElement(avx_message, "{http://AvX.Contract/V1}AvxResponseDetail")
        status = etree.SubElement(avx_response_detail, "{http://AvX.Contract/V1}Status")
        status.text = "Success"
        
        # Process message
        result = process_avx_message(avx_message)
        self.assertTrue(result)

    def test_process_fica_message(self):
        """Test process_fica_message."""
        # Create FicaProviderSubmitMessage
        fica_message = etree.Element("{http://FicaX.Contract/V1}FicaProviderSubmitMessage")
        
        # Add Data
        data = etree.SubElement(fica_message, "{http://FicaX.Contract/V1}Data")
        
        # Process message
        result = process_fica_message(fica_message)
        self.assertTrue(result)

    def test_process_idx_message(self):
        """Test process_idx_message."""
        # Create IDXProviderSubmitMessage
        idx_message = etree.Element("{http://IDX.Contract/V1}IDXProviderSubmitMessage")
        
        # Add account information
        account_name = etree.SubElement(idx_message, "{http://IDX.Contract/V1}AccountName")
        account_name.text = "Test Account"
        
        account_number = etree.SubElement(idx_message, "{http://IDX.Contract/V1}AccountNumber")
        account_number.text = "12345678"
        
        account_type = etree.SubElement(idx_message, "{http://IDX.Contract/V1}AccountType")
        account_type.text = "Savings"
        
        # Process message
        result = process_idx_message(idx_message)
        self.assertTrue(result)

    def test_process_ivx_message(self):
        """Test process_ivx_message."""
        # Create IVXProviderSubmitMessage
        ivx_message = etree.Element("{http://IVX.Contract/V1}IVXProviderSubmitMessage")
        
        # Add Data
        data = etree.SubElement(ivx_message, "{http://IVX.Contract/V1}Data")
        
        # Process message
        result = process_ivx_message(ivx_message)
        self.assertTrue(result)

    def test_create_response(self):
        """Test create_response."""
        # Create response with success=True
        response = create_response(True)
        
        # Check response structure
        self.assertEqual(response.tag, f"{{{SOAP_NS}}}Envelope")
        body = response.find(f".//{{{SOAP_NS}}}Body")
        self.assertIsNotNone(body)
        
        value = body.find(".//{http://SecureX.ProviderSubmitService/V1}Value")
        self.assertIsNotNone(value)
        self.assertEqual(value.text, "true")
        
        # Create response with success=False
        response = create_response(False)
        value = response.find(".//{http://SecureX.ProviderSubmitService/V1}Value")
        self.assertEqual(value.text, "false")

    def test_add_security_header(self):
        """Test add_security_header."""
        # Create a simple envelope
        envelope = etree.Element(f"{{{SOAP_NS}}}Envelope")
        
        # Add security header
        result = add_security_header(envelope)
        
        # Check result
        header = result.find(f".//{{{SOAP_NS}}}Header")
        self.assertIsNotNone(header)
        
        security = header.find(f".//{{{WSSE_NS}}}Security")
        self.assertIsNotNone(security)
        self.assertEqual(security.get(f"{{{SOAP_NS}}}mustUnderstand"), "1")
        
        timestamp = security.find(f".//{{{WSU_NS}}}Timestamp")
        self.assertIsNotNone(timestamp)
        
        created = timestamp.find(f".//{{{WSU_NS}}}Created")
        self.assertIsNotNone(created)
        
        expires = timestamp.find(f".//{{{WSU_NS}}}Expires")
        self.assertIsNotNone(expires)

    def test_create_fault_response(self):
        """Test create_fault_response."""
        # Create fault response
        code = 500
        errors = ["Error 1", "Error 2"]
        response = create_fault_response(code, errors)
        
        # Check response structure
        self.assertEqual(response.tag, f"{{{SOAP_NS}}}Envelope")
        
        body = response.find(f".//{{{SOAP_NS}}}Body")
        self.assertIsNotNone(body)
        
        fault = body.find(f".//{{{SOAP_NS}}}Fault")
        self.assertIsNotNone(fault)
        
        code_elem = fault.find(".//Code")
        self.assertIsNotNone(code_elem)
        self.assertEqual(code_elem.text, "500")
        
        detail = fault.find(".//Detail")
        self.assertIsNotNone(detail)
        
        securex_fault = detail.find(".//{http://SecureX.Fault/V1}SecureXFault")
        self.assertIsNotNone(securex_fault)
        
        errors_elem = securex_fault.find(".//Errors")
        self.assertIsNotNone(errors_elem)
        
        error_strings = errors_elem.findall(".//string")
        self.assertEqual(len(error_strings), 2)
        self.assertEqual(error_strings[0].text, "Error 1")
        self.assertEqual(error_strings[1].text, "Error 2")

    @patch('app.provider_response_service.process_submit_request')
    def test_provider_response_service_success(self, mock_process):
        """Test provider_response_service with successful processing."""
        # Mock process_submit_request to return True
        mock_process.return_value = True
        
        # Create SOAP request
        soap_request = etree.tostring(self.soap_envelope, encoding='utf-8')
        
        # Make the request
        response = self.client.post(
            '/ProviderResponseService',
            data=soap_request,
            content_type='application/soap+xml'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/soap+xml; charset=utf-8')
        
        # Parse the response XML
        response_xml = etree.fromstring(response.data)
        
        # Check response structure
        body = response_xml.find(f".//{{{SOAP_NS}}}Body")
        self.assertIsNotNone(body)
        
        value = body.find(".//{http://SecureX.ProviderSubmitService/V1}Value")
        self.assertIsNotNone(value)
        self.assertEqual(value.text, "true")

    @patch('app.provider_response_service.process_submit_request')
    def test_provider_response_service_failure(self, mock_process):
        """Test provider_response_service with processing failure."""
        # Mock process_submit_request to return False
        mock_process.return_value = False
        
        # Create SOAP request
        soap_request = etree.tostring(self.soap_envelope, encoding='utf-8')
        
        # Make the request
        response = self.client.post(
            '/ProviderResponseService',
            data=soap_request,
            content_type='application/soap+xml'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/soap+xml; charset=utf-8')
        
        # Parse the response XML
        response_xml = etree.fromstring(response.data)
        
        # Check response structure
        body = response_xml.find(f".//{{{SOAP_NS}}}Body")
        self.assertIsNotNone(body)
        
        value = body.find(".//{http://SecureX.ProviderSubmitService/V1}Value")
        self.assertIsNotNone(value)
        self.assertEqual(value.text, "false")

    @patch('app.provider_response_service.process_submit_request')
    def test_provider_response_service_exception(self, mock_process):
        """Test provider_response_service with exception."""
        # Mock process_submit_request to raise an exception
        mock_process.side_effect = Exception("Test error")
        
        # Create SOAP request
        soap_request = etree.tostring(self.soap_envelope, encoding='utf-8')
        
        # Make the request
        response = self.client.post(
            '/ProviderResponseService',
            data=soap_request,
            content_type='application/soap+xml'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.content_type, 'application/soap+xml; charset=utf-8')
        
        # Parse the response XML
        response_xml = etree.fromstring(response.data)
        
        # Check response structure
        body = response_xml.find(f".//{{{SOAP_NS}}}Body")
        self.assertIsNotNone(body)
        
        fault = body.find(f".//{{{SOAP_NS}}}Fault")
        self.assertIsNotNone(fault)

    @patch('app.provider_response_service.client')
    def test_health_check_healthy(self, mock_client):
        """Test health_check when service is healthy."""
        # Mock client to be not None
        mock_client.__bool__.return_value = True
        
        # Make the request
        response = self.client.get('/health')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'mcauto-soap-client')

    def test_health_check_unhealthy(self):
        """Test health_check when service is unhealthy."""
        # Use a context manager to patch the client to None
        with patch('app.provider_response_service.client', None):
            # Make the request
            response = self.client.get('/health')
            
            # Check the response
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'unhealthy')
            self.assertEqual(data['service'], 'mcauto-soap-client')
            self.assertEqual(data['reason'], 'WSDL not loaded')
        
        # Make the request
        response = self.client.get('/health')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'unhealthy')
        self.assertEqual(data['service'], 'mcauto-soap-client')
        self.assertEqual(data['reason'], 'WSDL not loaded')


if __name__ == '__main__':
    unittest.main()