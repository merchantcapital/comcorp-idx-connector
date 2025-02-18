from constants import PRIVATE_KEY, PUBLIC_KEY
import base64
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
from pathlib import Path

BLOCK_SIZE = 16
pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
unpad = lambda s: s[:-ord(s[len(s) - 1:])]
 
def encrypt(raw):
    key = hashlib.sha256(PUBLIC_KEY.encode("utf-8")).digest()
    raw = str.encode(pad(raw)) #convert str to byte 
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return base64.b64encode(iv + cipher.encrypt(raw))
 
def decrypt(enc):
    key = hashlib.sha256(PRIVATE_KEY.encode("utf-8")).digest()
    enc = base64.b64decode(enc)
    iv = enc[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[16:]))

def encode(plain_text):
    message = plain_text.encode('utf-8')
    encodedText=base64.b64encode(message)
    print("Encrypted text",encodedText)
    return encodedText.decode('utf-8')