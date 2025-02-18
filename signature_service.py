from zeep import Client
from zeep.wsse.signature import BinarySignature
from zeep.wsse import utils
from datetime import datetime, timedelta
import pytz
import base64
from constants import PRIVATE_KEY, PUBLIC_KEY
from crypto import encrypt, decrypt, encode

class BinarySignatureTimestamp(BinarySignature):
    def apply(self, envelope, headers):
        security = utils.get_security_header(envelope)
        
        encoded_public_key = encode(PUBLIC_KEY)
        binarySecurityToken = utils.WSU('BinarySecurityToken',encoded_public_key)
        #security.append(binarySecurityToken)

        utc = pytz.UTC
        created = datetime.now(utc)
        expired = created + timedelta(seconds=1 * 60)

        timestamp = utils.WSU('Timestamp')
        timestamp.append(utils.WSU('Created', created.replace(microsecond=0).isoformat()+'Z'))
        timestamp.append(utils.WSU('Expires', expired.replace(microsecond=0).isoformat()+'Z'))

        security.append(timestamp)

        super().apply(envelope, headers)
        return envelope, headers

# Override response verification and skip response verification for now...
# Zeep does not supprt Signature verification with different certificate...
# Ref. https://github.com/mvantellingen/python-zeep/pull/822/  "Add support for different signing and verification certificates #822"
    def verify(self, envelope):
        return envelope