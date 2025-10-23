"""
Encryption and decryption utilities for sensitive data.

Uses AES-256-GCM for authenticated encryption of secrets like CLIENT_SECRET.
The encryption key should be stored securely as an environment variable.
"""

import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class EncryptionError(Exception):
    """Raised when encryption operations fail."""

    pass


class DecryptionError(Exception):
    """Raised when decryption operations fail."""

    pass


class CryptoHandler:
    """
    Handles encryption and decryption of sensitive data using AES-256-GCM.

    The encryption key must be 32 bytes (256 bits) and should be stored
    securely as an environment variable (ENCRYPTION_KEY).
    """

    def __init__(self, encryption_key: bytes | None = None):
        """
        Initialize the crypto handler.

        Args:
            encryption_key: 32-byte encryption key. If None, reads from
                          ENCRYPTION_KEY environment variable.

        Raises:
            EncryptionError: If encryption key is missing or invalid.
        """
        if encryption_key is None:
            key_b64 = os.getenv("ENCRYPTION_KEY")
            if not key_b64:
                raise EncryptionError(
                    "ENCRYPTION_KEY environment variable not set. "
                    "Generate with: python -c 'import os, base64; "
                    "print(base64.b64encode(os.urandom(32)).decode())'"
                )
            try:
                encryption_key = base64.b64decode(key_b64)
            except Exception as e:
                raise EncryptionError(f"Invalid ENCRYPTION_KEY format: {e}")

        if len(encryption_key) != 32:
            raise EncryptionError(
                f"Encryption key must be 32 bytes, got {len(encryption_key)}"
            )

        self.aesgcm = AESGCM(encryption_key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt.

        Returns:
            Base64-encoded string containing nonce + ciphertext.

        Raises:
            EncryptionError: If encryption fails.
        """
        if not plaintext:
            raise EncryptionError("Cannot encrypt empty string")

        try:
            # Generate a random 96-bit nonce (12 bytes)
            nonce = os.urandom(12)

            # Encrypt the plaintext
            plaintext_bytes = plaintext.encode("utf-8")
            ciphertext = self.aesgcm.encrypt(nonce, plaintext_bytes, None)

            # Combine nonce + ciphertext and encode as base64
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode("utf-8")

        except Exception as e:
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            encrypted_data: Base64-encoded string containing nonce + ciphertext.

        Returns:
            The decrypted plaintext string.

        Raises:
            DecryptionError: If decryption fails or data is tampered.
        """
        if not encrypted_data:
            raise DecryptionError("Cannot decrypt empty string")

        try:
            # Decode from base64
            encrypted_bytes = base64.b64decode(encrypted_data)

            # Extract nonce (first 12 bytes) and ciphertext (rest)
            if len(encrypted_bytes) < 12:
                raise DecryptionError("Invalid encrypted data format")

            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            # Decrypt the ciphertext
            plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext_bytes.decode("utf-8")

        except InvalidTag:
            raise DecryptionError(
                "Decryption failed: data may be corrupted or tampered with"
            )
        except Exception as e:
            raise DecryptionError(f"Decryption failed: {e}")


# Global instance for convenience
_crypto_handler: CryptoHandler | None = None


def get_crypto_handler() -> CryptoHandler:
    """
    Get the global CryptoHandler instance.

    Creates the instance on first call using ENCRYPTION_KEY environment variable.

    Returns:
        The global CryptoHandler instance.

    Raises:
        EncryptionError: If ENCRYPTION_KEY is not set or invalid.
    """
    global _crypto_handler
    if _crypto_handler is None:
        _crypto_handler = CryptoHandler()
    return _crypto_handler


def encrypt_secret(plaintext: str) -> str:
    """
    Convenience function to encrypt a secret using the global crypto handler.

    Args:
        plaintext: The secret to encrypt.

    Returns:
        Base64-encoded encrypted data.
    """
    return get_crypto_handler().encrypt(plaintext)


def decrypt_secret(encrypted_data: str) -> str:
    """
    Convenience function to decrypt a secret using the global crypto handler.

    Args:
        encrypted_data: Base64-encoded encrypted data.

    Returns:
        The decrypted plaintext.
    """
    return get_crypto_handler().decrypt(encrypted_data)
