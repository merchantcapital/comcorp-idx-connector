"""
mcauto-soap-client application package.

This package contains the SOAP client and service implementation for the mcauto-soap-client application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# Create the Flask application instance
app = Flask(__name__)

# Import routes to register them with the app
from app import provider_response_service
from app import comcorp_download_service