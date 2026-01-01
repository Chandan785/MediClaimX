"""
Unit tests for the InputValidator class.

Tests file upload validation functionality including format checking,
size validation, and error handling.
"""

import pytest
import io
from unittest.mock import Mock
from src.validation import InputValidator


class TestInputValidator:
    """Test cases for InputValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()
    
    def create_mock_file(self, name: str, content: bytes, size: int = None):
        """Create a mock file object for testing."""
        mock_file = Mock()
        mock_file.name = name
        mock_file.size = size if size is not None else len(content)
        mock_file.read = Mock(return_value=content)
        mock_file.seek = Mock()
        mock_file.type = "application/pdf" if name.endswith('.pdf') else "image/jpeg"
        return mock_file
    
    def test_validate_file_format_valid_pdf(self):
        """Test validation of valid PDF file."""
        # Create mock PDF file with proper header
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        mock_file = self.create_mock_file("policy.pdf", pdf_content)
        
        is_valid, error = self.validator.validate_file_format(mock_file, ['pdf'], 'policy')
        
        assert is_valid is True
        assert error is None
    
    def test_validate_file_format_invalid_extension(self):
        """Test validation with invalid file extension."""
        mock_file = self.create_mock_file("policy.txt", b'some content')
        
        is_valid, error = self.validator.validate_file_format(mock_file, ['pdf'], 'policy')
        
        assert is_valid is False
        assert "Invalid file format" in error
        assert "PDF" in error
    
    def test_validate_file_format_corrupted_pdf(self):
        """Test validation of corrupted PDF file."""
        # Create mock file with PDF extension but invalid content
        mock_file = self.create_mock_file("policy.pdf", b'not a pdf file')
        
        is_valid, error = self.validator.validate_file_format(mock_file, ['pdf'], 'policy')
        
        assert is_valid is False
        assert "corrupted" in error.lower() or "valid PDF" in error
    
    def test_validate_file_format_valid_jpeg(self):
        """Test validation of valid JPEG file."""
        # Create mock JPEG file with proper header
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        mock_file = self.create_mock_file("bill.jpg", jpeg_content)
        
        is_valid, error = self.validator.validate_file_format(mock_file, ['jpg', 'jpeg'], 'bill')
        
        assert is_valid is True
        assert error is None
    
    def test_validate_file_format_valid_png(self):
        """Test validation of valid PNG file."""
        # Create mock PNG file with proper header
        png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
        mock_file = self.create_mock_file("bill.png", png_content)
        
        is_valid, error = self.validator.validate_file_format(mock_file, ['png'], 'bill')
        
        assert is_valid is True
        assert error is None
    
    def test_validate_file_size_valid(self):
        """Test validation of file within size limits."""
        mock_file = self.create_mock_file("test.pdf", b'content', size=1024*1024)  # 1MB
        
        is_valid, error = self.validator.validate_file_size(mock_file, max_size_mb=5)
        
        assert is_valid is True
        assert error is None
    
    def test_validate_file_size_too_large(self):
        """Test validation of file exceeding size limits."""
        mock_file = self.create_mock_file("test.pdf", b'content', size=10*1024*1024)  # 10MB
        
        is_valid, error = self.validator.validate_file_size(mock_file, max_size_mb=5)
        
        assert is_valid is False
        assert "exceeds maximum" in error
    
    def test_validate_file_size_empty_file(self):
        """Test validation of empty file."""
        mock_file = self.create_mock_file("test.pdf", b'', size=0)
        
        is_valid, error = self.validator.validate_file_size(mock_file)
        
        assert is_valid is False
        assert "empty" in error.lower()
    
    def test_validate_policy_file_valid(self):
        """Test comprehensive policy file validation."""
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        mock_file = self.create_mock_file("policy.pdf", pdf_content, size=1024*1024)
        
        is_valid, errors = self.validator.validate_policy_file(mock_file)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_policy_file_invalid_format(self):
        """Test policy file validation with invalid format."""
        mock_file = self.create_mock_file("policy.txt", b'content', size=1024)
        
        is_valid, errors = self.validator.validate_policy_file(mock_file)
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("format" in error.lower() for error in errors)
    
    def test_validate_bill_file_valid_pdf(self):
        """Test bill file validation with valid PDF."""
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        mock_file = self.create_mock_file("bill.pdf", pdf_content, size=1024*1024)
        
        is_valid, errors = self.validator.validate_bill_file(mock_file)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_bill_file_valid_image(self):
        """Test bill file validation with valid image."""
        jpeg_content = b'\xff\xd8\xff\xe0\x00\x10JFIF'
        mock_file = self.create_mock_file("bill.jpg", jpeg_content, size=1024*1024)
        
        is_valid, errors = self.validator.validate_bill_file(mock_file)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_both_files_valid(self):
        """Test validation of both files when both are valid."""
        pdf_content = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        policy_file = self.create_mock_file("policy.pdf", pdf_content, size=1024*1024)
        bill_file = self.create_mock_file("bill.pdf", pdf_content, size=1024*1024)
        
        is_valid, errors = self.validator.validate_both_files(policy_file, bill_file)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_both_files_invalid(self):
        """Test validation when both files are invalid."""
        policy_file = self.create_mock_file("policy.txt", b'content', size=1024)
        bill_file = self.create_mock_file("bill.txt", b'content', size=1024)
        
        is_valid, errors = self.validator.validate_both_files(policy_file, bill_file)
        
        assert is_valid is False
        assert len(errors) >= 2  # Should have errors for both files
        assert any("Policy:" in error for error in errors)
        assert any("Bill:" in error for error in errors)
    
    def test_validate_file_format_none_file(self):
        """Test validation with None file."""
        is_valid, error = self.validator.validate_file_format(None, ['pdf'], 'policy')
        
        assert is_valid is False
        assert "No policy file provided" in error
    
    def test_validate_file_size_none_file(self):
        """Test size validation with None file."""
        is_valid, error = self.validator.validate_file_size(None)
        
        assert is_valid is False
        assert "No file provided" in error


if __name__ == "__main__":
    pytest.main([__file__])