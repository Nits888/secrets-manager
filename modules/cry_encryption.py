import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_key():
    return Fernet.generate_key()


def encrypt_string(key, plaintext, salt):
    cipher = Fernet(key + salt)
    encrypted_text = cipher.encrypt(plaintext)
    return encrypted_text


def decrypt_string(key, encrypted_text, salt):
    cipher = Fernet(key + salt)
    decrypted_text = cipher.decrypt(encrypted_text)
    return decrypted_text


def generate_key_basic(salt):
    my_code = 'TW81dk5DY1B1P3hYNz5MVkBVO2lXJmQjCg=='
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(base64.b64decode(my_code)))


def encrypt_text(text):
    salt = os.urandom(16)
    key = generate_key_basic(salt)
    fernet = Fernet(key)
    encrypted_text = fernet.encrypt(text.encode())
    return {
        'encrypted_text': base64.urlsafe_b64encode(encrypted_text).decode(),
        'salt': base64.urlsafe_b64encode(salt).decode(),
    }


def decrypt_text(encrypted_text, salt):
    salt = base64.urlsafe_b64decode(salt.encode())
    key = generate_key_basic(salt)
    fernet = Fernet(key)
    decrypted_text = fernet.decrypt(base64.urlsafe_b64decode(encrypted_text)).decode()
    return {
        'decrypted_text': decrypted_text
    }
