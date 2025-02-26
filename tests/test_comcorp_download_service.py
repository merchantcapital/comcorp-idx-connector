import unittest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
from lxml import etree

# Import the app and the service to test
from app import app
from app.comcorp_download_service import comcorp_download_request, check_auth, authenticate, requires_auth


class TestComcorpDownloadService(unittest.TestCase):
    """Test cases for the ComCorp Download Service."""

    def setUp(self):
        """Set up test client and other test variables."""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Sample valid payload for testing
        self.valid_payload = {
            "AccountNumber": "12345678",
            "AccountType": "Savings",
            "BranchCode": "123",
            "DateFrom": "2023-01-01",
            "DateTo": "2023-12-31",
            "EmailAddress": "test@example.com",
            "JointAccount": "No",
            "PhysicalEntities": [
                {
                    "IdentificationNo": "1234567890123",
                    "IdentificationType": "ID",
                    "Initials": "AB",
                    "Name": "Test User"
                }
            ]
        }

    @patch('app.comcorp_download_service.check_auth')
    def test_requires_auth_decorator(self, mock_check_auth):
        """Test that the requires_auth decorator works correctly."""
        # Mock check_auth to return True
        mock_check_auth.return_value = True
        
        # Create a test function with the decorator
        @requires_auth
        def test_function():
            return "Success"
        
        # Call the function with a mock request
        with self.app.test_request_context(headers={
            'Authorization': 'Basic dXNlcjpwYXNz'  # user:pass in base64
        }):
            result = test_function()
            self.assertEqual(result, "Success")
        
        # Mock check_auth to return False
        mock_check_auth.return_value = False
        
        # Call the function with a mock request
        with self.app.test_request_context(headers={
            'Authorization': 'Basic dXNlcjpwYXNz'  # user:pass in base64
        }):
            result = test_function()
            self.assertEqual(result.status_code, 401)
            self.assertIn('WWW-Authenticate', result.headers)

    @patch('app.comcorp_download_service.os.getenv')
    def test_check_auth(self, mock_getenv):
        """Test the check_auth function."""
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            'BASIC_AUTH_USERNAME': 'testuser',
            'BASIC_AUTH_PASSWORD': 'testpass'
        }.get(key)
        
        # Test with correct credentials
        self.assertTrue(check_auth('testuser', 'testpass'))
        
        # Test with incorrect username
        self.assertFalse(check_auth('wronguser', 'testpass'))
        
        # Test with incorrect password
        self.assertFalse(check_auth('testuser', 'wrongpass'))
        
        # Test with both incorrect
        self.assertFalse(check_auth('wronguser', 'wrongpass'))

    def test_authenticate(self):
        """Test the authenticate function."""
        response = authenticate()
        self.assertEqual(response.status_code, 401)
        self.assertIn('WWW-Authenticate', response.headers)
        self.assertEqual(response.headers['WWW-Authenticate'], 'Basic realm="Login Required"')

    @patch('app.comcorp_download_service.zeep.Client')
    @patch('app.comcorp_download_service.getHeader')
    @patch('app.comcorp_download_service.getDecryptedBody')
    @patch('app.comcorp_download_service.check_auth')
    def test_comcorp_download_request_success(self, mock_check_auth, mock_get_body, mock_get_header, mock_client):
        """Test successful SOAP request in comcorp_download_request."""
        # Mock authentication
        mock_check_auth.return_value = True
        
        # Mock SOAP client and response
        mock_soap = MagicMock()
        mock_client.return_value = mock_soap
        
        # Mock header and body
        mock_header = {'Header': 'test_header'}
        mock_get_header.return_value = mock_header
        
        mock_body = {'Body': 'test_body'}
        mock_get_body.return_value = mock_body
        
        # Mock SOAP response
        mock_result = MagicMock()
        mock_result.__dict__ = {
            'Status': 'Success',
            'Reference': '12345',
            'Message': 'Request processed successfully'
        }
        mock_soap.service.Submit.return_value = mock_result
        
        # Create a mock history plugin
        mock_history = MagicMock()
        mock_history.last_sent = {'envelope': etree.fromstring('<test>request</test>')}
        mock_history.last_received = {'envelope': etree.fromstring('<test>response</test>')}
        
        # Patch the HistoryPlugin to return our mock
        with patch('app.comcorp_download_service.HistoryPlugin', return_value=mock_history):
            # Make the request
            response = self.client.post(
                '/comcorp-download-request',
                headers={'Authorization': 'Basic dXNlcjpwYXNz'},  # user:pass in base64
                json=self.valid_payload,
                content_type='application/json'
            )
            
            # Check the response
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['status'], 'success')
            self.assertEqual(data['data']['Status'], 'Success')
            self.assertEqual(data['data']['Reference'], '12345')
            self.assertEqual(data['data']['Message'], 'Request processed successfully')
            
            # Verify SOAP client was called correctly
            mock_soap.service.Submit.assert_called_once_with(
                mock_body, _soapheaders={'Header': mock_header}
            )

    @patch('app.comcorp_download_service.check_auth')
    def test_comcorp_download_request_no_payload(self, mock_check_auth):
        """Test comcorp_download_request with no payload."""
        # Mock authentication
        mock_check_auth.return_value = True
        
        # Make the request with no payload
        response = self.client.post(
            '/comcorp-download-request',
            headers={'Authorization': 'Basic dXNlcjpwYXNz'},  # user:pass in base64
            content_type='application/json'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'No JSON payload provided')

    @patch('app.comcorp_download_service.zeep.Client')
    @patch('app.comcorp_download_service.check_auth')
    def test_comcorp_download_request_soap_error(self, mock_check_auth, mock_client):
        """Test comcorp_download_request with SOAP error."""
        # Mock authentication
        mock_check_auth.return_value = True
        
        # Mock SOAP client to raise an exception
        mock_soap = MagicMock()
        mock_client.return_value = mock_soap
        mock_soap.service.Submit.side_effect = Exception("SOAP Error")
        
        # Make the request
        response = self.client.post(
            '/comcorp-download-request',
            headers={'Authorization': 'Basic dXNlcjpwYXNz'},  # user:pass in base64
            json=self.valid_payload,
            content_type='application/json'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'SOAP Error')


if __name__ == '__main__':
    unittest.main()