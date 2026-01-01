"""
Input validation module for the Medical Claims Processor application.

This module provides comprehensive validation for file uploads and user inputs,
ensuring data integrity and security before processing.
"""

import streamlit as st
from typing import List, Optional, Tuple
import io
from pathlib import Path


class InputValidator:
    """
    Handles validation of user inputs including file uploads and data validation.
    """
    
    # File size limits (in MB) - optimized for free-tier usage
    MAX_FILE_SIZE_MB = 20  # Reduced from 200MB for faster processing and lower quota usage
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    
    # Allowed MIME types
    POLICY_MIME_TYPES = {
        'application/pdf'
    }
    
    BILL_MIME_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/jpg', 
        'image/png'
    }
    
    # Allowed file extensions
    POLICY_EXTENSIONS = {'.pdf'}
    BILL_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png'}
    
    def __init__(self):
        """Initialize the InputValidator."""
        pass
    
    def validate_file_format(self, file, allowed_types: List[str], file_type: str = "file") -> Tuple[bool, Optional[str]]:
        """
        Validate file format based on extension and basic content checks.
        
        Args:
            file: Streamlit uploaded file object
            allowed_types: List of allowed file extensions (e.g., ['pdf', 'jpg'])
            file_type: Type of file for error messaging ('policy' or 'bill')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file is None:
            return False, f"No {file_type} file provided"
        
        try:
            # Check file extension
            file_extension = Path(file.name).suffix.lower()
            allowed_extensions = {f'.{ext}' for ext in allowed_types}
            
            if file_extension not in allowed_extensions:
                allowed_str = ', '.join(allowed_types).upper()
                return False, f"Invalid file format. {file_type.title()} files must be {allowed_str} format. Got: {file_extension}"
            
            # Basic content validation by checking file headers
            try:
                # Read first few bytes for basic format validation
                file_bytes = file.read(1024)
                file.seek(0)  # Reset file pointer
                
                if not file_bytes:
                    return False, f"{file_type.title()} file appears to be empty"
                
                # Basic PDF validation - check for PDF header
                if file_extension == '.pdf':
                    if not file_bytes.startswith(b'%PDF-'):
                        return False, f"File appears to be corrupted or not a valid PDF file"
                
                # Basic image validation - check for common image headers
                elif file_extension in ['.jpg', '.jpeg']:
                    if not (file_bytes.startswith(b'\xff\xd8\xff') or file_bytes.startswith(b'\xff\xd8')):
                        return False, f"File appears to be corrupted or not a valid JPEG image"
                
                elif file_extension == '.png':
                    if not file_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                        return False, f"File appears to be corrupted or not a valid PNG image"
                        
            except Exception as e:
                # If we can't read the file, that's also an error
                return False, f"Could not read file content: {str(e)}"
            
        except Exception as e:
            return False, f"Error validating file format: {str(e)}"
        
        return True, None
    
    def validate_file_size(self, file, max_size_mb: int = None) -> Tuple[bool, Optional[str]]:
        """
        Validate file size is within acceptable limits.
        
        Args:
            file: Streamlit uploaded file object
            max_size_mb: Maximum file size in MB (defaults to class constant)
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file is None:
            return False, "No file provided"
        
        try:
            max_size = max_size_mb or self.MAX_FILE_SIZE_MB
            max_bytes = max_size * 1024 * 1024
            
            if not hasattr(file, 'size') or file.size is None:
                return False, "Could not determine file size"
            
            if file.size > max_bytes:
                return False, f"File size ({file.size / (1024*1024):.1f} MB) exceeds maximum allowed size of {max_size} MB"
            
            if file.size == 0:
                return False, "File is empty"
                
        except Exception as e:
            return False, f"Error checking file size: {str(e)}"
        
        return True, None
    
    def validate_policy_file(self, file) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation for policy document files.
        
        Args:
            file: Streamlit uploaded file object
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []
        
        if file is None:
            errors.append("Please upload a policy document")
            return False, errors
        
        # Validate file format
        format_valid, format_error = self.validate_file_format(file, ['pdf'], 'policy')
        if not format_valid:
            errors.append(format_error)
        
        # Validate file size
        size_valid, size_error = self.validate_file_size(file)
        if not size_valid:
            errors.append(size_error)
        
        # Additional policy-specific validations could go here
        # For example: checking for minimum content length, specific keywords, etc.
        
        return len(errors) == 0, errors
    
    def validate_bill_file(self, file) -> Tuple[bool, List[str]]:
        """
        Comprehensive validation for medical bill files.
        
        Args:
            file: Streamlit uploaded file object
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []
        
        if file is None:
            errors.append("Please upload a medical bill document")
            return False, errors
        
        # Validate file format
        format_valid, format_error = self.validate_file_format(file, ['pdf', 'jpg', 'jpeg', 'png'], 'bill')
        if not format_valid:
            errors.append(format_error)
        
        # Validate file size
        size_valid, size_error = self.validate_file_size(file)
        if not size_valid:
            errors.append(size_error)
        
        # Additional bill-specific validations could go here
        # For example: image quality checks, minimum resolution, etc.
        
        return len(errors) == 0, errors
    
    def validate_both_files(self, policy_file, bill_file) -> Tuple[bool, List[str]]:
        """
        Validate both policy and bill files together.
        
        Args:
            policy_file: Streamlit uploaded policy file object
            bill_file: Streamlit uploaded bill file object
            
        Returns:
            Tuple of (both_valid, list_of_all_error_messages)
        """
        all_errors = []
        
        # Validate policy file
        policy_valid, policy_errors = self.validate_policy_file(policy_file)
        if policy_errors:
            all_errors.extend([f"Policy: {error}" for error in policy_errors])
        
        # Validate bill file
        bill_valid, bill_errors = self.validate_bill_file(bill_file)
        if bill_errors:
            all_errors.extend([f"Bill: {error}" for error in bill_errors])
        
        return len(all_errors) == 0, all_errors
    
    def display_file_info(self, file, file_type: str) -> None:
        """
        Display file information in a user-friendly format.
        
        Args:
            file: Streamlit uploaded file object
            file_type: Type of file ('policy' or 'bill')
        """
        if file is None:
            return
        
        file_size_mb = file.size / (1024 * 1024)
        
        st.success(f"✅ {file_type.title()} uploaded: **{file.name}**")
        st.caption(f"Size: {file_size_mb:.1f} MB | Type: {file.type}")
    
    def display_validation_errors(self, errors: List[str]) -> None:
        """
        Display validation errors in a user-friendly format.
        
        Args:
            errors: List of error messages to display
        """
        if not errors:
            return
        
        # Group errors by severity
        critical_errors = []
        warning_errors = []
        
        for error in errors:
            if any(keyword in error.lower() for keyword in ['corrupted', 'invalid', 'empty', 'could not read']):
                critical_errors.append(error)
            else:
                warning_errors.append(error)
        
        # Display critical errors first
        for error in critical_errors:
            st.error(f"🚫 {error}")
        
        # Display warnings
        for error in warning_errors:
            st.warning(f"⚠️ {error}")
        
        # Provide helpful suggestions
        if critical_errors:
            st.info("💡 **Suggestions:**")
            st.markdown("""
            - Ensure your file is not corrupted
            - Try re-saving or re-exporting the document
            - Check that the file opens correctly in other applications
            - Make sure the file is in the correct format (PDF for policies, PDF/JPG/PNG for bills)
            """)
        elif warning_errors:
            st.info("💡 Please address the issues above before proceeding.")