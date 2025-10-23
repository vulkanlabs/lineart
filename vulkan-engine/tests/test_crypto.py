"""
Tests for encryption and decryption functionality.

Tests the CryptoHandler class and related security utilities.
"""

import base64
import os

import pytest
from vulkan_engine.security import (
    CryptoHandler,
    DecryptionError,
    EncryptionError,
    decrypt_secret,
    encrypt_secret,
)


class TestCryptoHandler:
    """Test cases for CryptoHandler class."""

    @pytest.fixture
    def encryption_key(self):
        """Generate a valid 32-byte encryption key for testing."""
        return os.urandom(32)

    @pytest.fixture
    def crypto_handler(self, encryption_key):
        """Create a CryptoHandler instance with test key."""
        return CryptoHandler(encryption_key=encryption_key)

    def test_encrypt_decrypt_roundtrip(self, crypto_handler):
        """Test that encryption and decryption work correctly."""
        plaintext = "my_super_secret_password"
        encrypted = crypto_handler.encrypt(plaintext)
        decrypted = crypto_handler.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_returns_different_values(self, crypto_handler):
        """Test that encrypting the same plaintext twice produces different ciphertexts."""
        plaintext = "secret"
        encrypted1 = crypto_handler.encrypt(plaintext)
        encrypted2 = crypto_handler.encrypt(plaintext)
        # Should be different due to random nonces
        assert encrypted1 != encrypted2
        # But both should decrypt to the same value
        assert crypto_handler.decrypt(encrypted1) == plaintext
        assert crypto_handler.decrypt(encrypted2) == plaintext

    def test_encrypt_empty_string_raises_error(self, crypto_handler):
        """Test that encrypting empty string raises EncryptionError."""
        with pytest.raises(EncryptionError, match="Cannot encrypt empty string"):
            crypto_handler.encrypt("")

    def test_decrypt_empty_string_raises_error(self, crypto_handler):
        """Test that decrypting empty string raises DecryptionError."""
        with pytest.raises(DecryptionError, match="Cannot decrypt empty string"):
            crypto_handler.decrypt("")

    def test_decrypt_invalid_data_raises_error(self, crypto_handler):
        """Test that decrypting invalid data raises DecryptionError."""
        with pytest.raises(DecryptionError):
            crypto_handler.decrypt("invalid_base64_data")

    def test_decrypt_tampered_data_raises_error(self, crypto_handler):
        """Test that decrypting tampered data raises DecryptionError."""
        plaintext = "secret"
        encrypted = crypto_handler.encrypt(plaintext)

        # Tamper with the encrypted data
        encrypted_bytes = base64.b64decode(encrypted)
        tampered = bytearray(encrypted_bytes)
        tampered[-1] ^= 1  # Flip one bit
        tampered_encrypted = base64.b64encode(bytes(tampered)).decode("utf-8")

        with pytest.raises(DecryptionError, match="corrupted or tampered"):
            crypto_handler.decrypt(tampered_encrypted)

    def test_decrypt_with_different_key_raises_error(self, encryption_key):
        """Test that decrypting with a different key raises DecryptionError."""
        handler1 = CryptoHandler(encryption_key=encryption_key)
        handler2 = CryptoHandler(encryption_key=os.urandom(32))

        encrypted = handler1.encrypt("secret")

        with pytest.raises(DecryptionError):
            handler2.decrypt(encrypted)

    def test_invalid_key_length_raises_error(self):
        """Test that invalid key length raises EncryptionError."""
        with pytest.raises(EncryptionError, match="must be 32 bytes"):
            CryptoHandler(encryption_key=b"short_key")

    def test_encrypt_special_characters(self, crypto_handler):
        """Test encryption of strings with special characters."""
        plaintext = "secret!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        encrypted = crypto_handler.encrypt(plaintext)
        decrypted = crypto_handler.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_unicode_characters(self, crypto_handler):
        """Test encryption of strings with unicode characters."""
        plaintext = "秘密🔐パスワード"
        encrypted = crypto_handler.encrypt(plaintext)
        decrypted = crypto_handler.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_long_string(self, crypto_handler):
        """Test encryption of long strings."""
        plaintext = "a" * 10000
        encrypted = crypto_handler.encrypt(plaintext)
        decrypted = crypto_handler.decrypt(encrypted)
        assert decrypted == plaintext


class TestCryptoConvenienceFunctions:
    """Test cases for convenience functions."""

    @pytest.fixture(autouse=True)
    def setup_encryption_key(self, monkeypatch):
        """Set up ENCRYPTION_KEY environment variable for tests."""
        key = base64.b64encode(os.urandom(32)).decode()
        monkeypatch.setenv("ENCRYPTION_KEY", key)

    def test_encrypt_decrypt_secret_roundtrip(self):
        """Test convenience functions encrypt_secret and decrypt_secret."""
        plaintext = "my_secret"
        encrypted = encrypt_secret(plaintext)
        decrypted = decrypt_secret(encrypted)
        assert decrypted == plaintext

    def test_missing_encryption_key_raises_error(self, monkeypatch):
        """Test that missing ENCRYPTION_KEY raises EncryptionError."""
        monkeypatch.delenv("ENCRYPTION_KEY")

        # Reset the global handler to force re-initialization
        import vulkan_engine.security.crypto as crypto_module

        crypto_module._crypto_handler = None

        with pytest.raises(
            EncryptionError, match="ENCRYPTION_KEY environment variable not set"
        ):
            encrypt_secret("secret")

    def test_invalid_encryption_key_format_raises_error(self, monkeypatch):
        """Test that invalid ENCRYPTION_KEY format raises EncryptionError."""
        monkeypatch.setenv("ENCRYPTION_KEY", "not_valid_base64!")

        # Reset the global handler to force re-initialization
        import vulkan_engine.security.crypto as crypto_module

        crypto_module._crypto_handler = None

        with pytest.raises(EncryptionError, match="Invalid ENCRYPTION_KEY format"):
            encrypt_secret("secret")


class TestEncryptionKeyGeneration:
    """Test cases for encryption key generation helper."""

    def test_key_generation_command(self):
        """Test that the key generation command in error message works."""
        # This is the command suggested in the error message
        key = base64.b64encode(os.urandom(32)).decode()

        # Verify it produces a valid key
        assert len(base64.b64decode(key)) == 32

        # Verify it can be used to create a handler
        handler = CryptoHandler(encryption_key=base64.b64decode(key))
        encrypted = handler.encrypt("test")
        decrypted = handler.decrypt(encrypted)
        assert decrypted == "test"
