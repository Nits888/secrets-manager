"""
cry_encryption
~~~~~~~~~~~~~~

This module provides utilities for symmetric encryption and decryption using
the Fernet symmetric encryption and PBKDF2HMAC key derivation. It includes
functions to generate encryption keys, encrypt and decrypt strings, and handle
custom encryption-related exceptions.

"""

import base64
import os
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_LENGTH = 16  # 128 bits


class EncryptionError(Exception):
    """Custom exception raised for encryption-related errors."""
    pass


class DecryptionError(Exception):
    """Custom exception raised for decryption-related errors."""
    pass


def generate_key():
    """Generates a new Fernet symmetric encryption key.

    Returns:
        bytes: A new Fernet encryption key.
    """
    return Fernet.generate_key()


def generate_key_basic(salt):
    """Generates a key using PBKDF2HMAC key derivation.

    Args:
        salt (bytes): Salt to use in key derivation.

    Returns:
        bytes: A derived key.
    """
    passphrase = 'SW5kaWFJc0Jlc3RDb3VudHJ5aW5AMDIwMgo='
    if not passphrase:
        raise EncryptionError("Passphrase not found.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))


def encrypt_string(plaintext, salt):
    """Encrypts a plaintext string.

    Args:
        plaintext (str): The plaintext string to encrypt.
        salt (bytes): Salt for the key derivation.

    Returns:
        bytes: The encrypted ciphertext.
    """
    derived_key = generate_key_basic(salt)
    fernet = Fernet(derived_key)
    return fernet.encrypt(plaintext.encode())


def decrypt_string(encrypted_text, salt):
    """Decrypts an encrypted string.

    Args:
        encrypted_text (bytes): The encrypted text to decrypt.
        salt (bytes): Salt for the key derivation.

    Returns:
        str: The decrypted plaintext string.
    """
    derived_key = generate_key_basic(salt)
    fernet = Fernet(derived_key)
    return fernet.decrypt(encrypted_text).decode()


def encrypt_text(text):
    """Encrypts a text using a generated key and salt.

    Args:
        text (str): The plaintext to encrypt.

    Returns:
        dict: A dictionary containing the encrypted text and its salt.
    """
    try:
        salt = os.urandom(SALT_LENGTH)
        key = generate_key_basic(salt)
        fernet = Fernet(key)
        encrypted_text = fernet.encrypt(text.encode())
        return {
            'encrypted_text': base64.urlsafe_b64encode(encrypted_text).decode(),
            'salt': base64.urlsafe_b64encode(salt).decode(),
        }
    except InvalidToken as e:
        raise EncryptionError(f"InvalidToken during encryption: {str(e)}")
    except Exception as e:
        raise EncryptionError(f"Unexpected error during encryption: {str(e)}")


def decrypt_text(encrypted_text, salt_provided):
    """Decrypts an encrypted text using the provided salt.

    Args:
        encrypted_text (str): The encrypted text to decrypt.
        salt_provided (str): The salt used during encryption.

    Returns:
        dict: A dictionary containing the decrypted text.
    """
    try:
        salt = base64.urlsafe_b64decode(salt_provided.encode())
        key = generate_key_basic(salt)
        fernet = Fernet(key)
        decrypted_text = fernet.decrypt(base64.urlsafe_b64decode(encrypted_text)).decode()
        return {
            'decrypted_text': decrypted_text
        }
    except InvalidToken as e:
        raise DecryptionError(f"InvalidToken during decryption: {str(e)}")
    except Exception as e:
        raise DecryptionError(f"Unexpected error during decryption: {str(e)}")
