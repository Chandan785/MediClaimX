"""
Gemini AI Processor for Medical Claims Processing

This module handles document processing using Google Gemini API.
It extracts structured data from insurance policy and medical bill documents.
"""

import json
import base64
import mimetypes
import time
from typing import Optional, Dict, Any, Tuple, Union
import google.genai as genai
from google.genai.types import GenerateContentConfig, SafetySetting, HarmCategory, HarmBlockThreshold
import streamlit as st

from .models import ClaimData, BillItem


class GeminiProcessor:
    """
    Processes insurance policy and medical bill documents using Google Gemini 1.5 Flash.
    
    This class handles:
    - Document upload and format validation
    - Structured prompt creation for consistent JSON extraction
    - API communication with Gemini 1.5 Flash
    - Response validation and error handling
    - Support for both PDF and image file formats
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Gemini processor with API credentials.
        
        Args:
            api_key: Google API key for Gemini access
            
        Raises:
            ValueError: If API key is invalid or empty
        """
        if not api_key or not isinstance(api_key, str) or api_key.strip() == "":
            raise ValueError("API key must be a non-empty string")
        
        if api_key.strip() == "your-google-api-key-here":
            raise ValueError("Please replace the placeholder API key with your actual Google API key")
        
        self.api_key = api_key.strip()
        
        # Configure Gemini API client
        self.client = genai.Client(api_key=self.api_key)
        
        # Set model name - use the latest available model
        self.model_name = "models/gemini-flash-latest"
        
        # Free-tier optimization settings
        self.max_file_size_mb = 20  # Reduced from 200MB for faster processing
        self.max_retries = 2  # Reduced from 3 to save quota
        self.base_delay = 2.0  # Increased delay to be more conservative with rate limits
        self.request_timeout = 30  # Shorter timeout for faster failure detection
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 second between requests
        self.daily_request_count = 0
        self.daily_request_limit = 1500  # Conservative daily limit for free tier
        self.request_reset_time = 0
    
    def process_documents(self, policy_file, bill_file) -> ClaimData:
        """
        Process insurance policy and medical bill documents to extract claim data.
        
        Args:
            policy_file: Uploaded policy document (PDF)
            bill_file: Uploaded medical bill (PDF or image)
            
        Returns:
            ClaimData object containing extracted information
            
        Raises:
            ValueError: If files are invalid or processing fails
            RuntimeError: If API call fails or returns invalid data
        """
        # Validate input files
        if not policy_file or not bill_file:
            raise ValueError("Both policy and bill files are required")
        
        try:
            # Prepare file contents for API
            policy_content = self._prepare_file_content(policy_file)
            bill_content = self._prepare_file_content(bill_file)
            
            # Create extraction prompt
            prompt = self._create_extraction_prompt()
            
            # Prepare content for Gemini API (new format)
            content_parts = [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": policy_content["mime_type"],
                        "data": policy_content["data"]
                    }
                },
                {
                    "inline_data": {
                        "mime_type": bill_content["mime_type"], 
                        "data": bill_content["data"]
                    }
                }
            ]
            
            # Make API call with retry logic
            response = self._make_api_call_with_retry(content_parts)
            
            # Extract text from response (new API format)
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to get text from candidates
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        response_text = parts[0].text
            elif hasattr(response, 'content'):
                response_text = str(response.content)
            
            # Validate response
            if not response_text or not response_text.strip():
                raise RuntimeError("Gemini API returned empty response")
            
            # Clean and parse JSON response
            try:
                # Clean the response text - remove any markdown formatting
                cleaned_text = response_text.strip()
                
                # Remove markdown code blocks
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]  # Remove ```json
                if cleaned_text.startswith('```'):
                    cleaned_text = cleaned_text[3:]  # Remove ```
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]  # Remove ```
                
                cleaned_text = cleaned_text.strip()
                
                # Try to extract JSON from text that might have extra content
                json_start = cleaned_text.find('{')
                json_end = cleaned_text.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    json_text = cleaned_text[json_start:json_end + 1]
                else:
                    json_text = cleaned_text
                
                # Check if response looks truncated
                is_truncated = (
                    json_end == -1 or  # No closing brace found
                    json_text.count('{') != json_text.count('}') or  # Unbalanced braces
                    json_text.count('[') != json_text.count(']') or  # Unbalanced brackets
                    json_text.endswith(',') or  # Ends with comma
                    len(response_text) > 1400  # Response is suspiciously long (near token limit)
                )
                
                if is_truncated:
                    st.warning("⚠️ **Response appears truncated** - attempting recovery...")
                
                # Attempt to parse JSON
                response_data = json.loads(json_text)
                
            except json.JSONDecodeError as e:
                # Enhanced error handling with recovery attempts
                st.error(f"⚠️ **JSON Parsing Error**: The AI response wasn't properly formatted")
                
                # Show the problematic response for debugging (truncated)
                debug_text = response_text[:500] + "..." if len(response_text) > 500 else response_text
                with st.expander("🔍 Debug: View AI Response", expanded=False):
                    st.code(debug_text, language="text")
                    st.caption("This shows what the AI actually returned. It should be valid JSON.")
                
                # Try alternative parsing approaches
                recovery_successful = False
                
                # Recovery attempt 1: Fix common JSON issues including truncation
                try:
                    # Fix common issues like trailing commas, missing quotes, truncation, etc.
                    fixed_text = self._attempt_json_recovery(response_text)
                    if fixed_text:
                        response_data = json.loads(fixed_text)
                        recovery_successful = True
                        st.success("✅ **Recovery successful**: Fixed JSON formatting and truncation issues")
                        with st.expander("🔧 Debug: Fixed JSON", expanded=False):
                            st.code(fixed_text, language="json")
                except Exception as recovery_error:
                    st.warning(f"⚠️ JSON recovery attempt failed: {str(recovery_error)}")
                
                if not recovery_successful:
                    # Provide detailed error information
                    error_position = getattr(e, 'pos', 0)
                    error_context = response_text[max(0, error_position-50):error_position+50] if response_text else ""
                    
                    st.error("❌ **Processing Error**")
                    st.error(f"**Details:** Gemini API returned invalid JSON at position {error_position}: {e}. Context: '...{error_context}...'. This usually means the AI didn't follow the JSON format instructions. Common causes: (1) Documents are unclear or low quality, (2) Complex document formats, (3) AI model inconsistency. Please try again with clearer, higher-quality documents.")
                    
                    st.info("💡 **How to fix:** The AI response was malformed. Please try again")
                    st.markdown(self.get_troubleshooting_tips())
                    
                    raise RuntimeError(
                        f"Gemini API returned invalid JSON at position {error_position}: {e}. "
                        f"Context: '...{error_context}...'. "
                        f"This usually means the AI didn't follow the JSON format instructions. "
                        f"Common causes: (1) Documents are unclear or low quality, "
                        f"(2) Complex document formats, (3) AI model inconsistency. "
                        f"Please try again with clearer, higher-quality documents."
                    )
            
            # Validate response structure
            if not self._validate_response(response_data):
                # Provide detailed information about what's missing
                missing_info = self._get_validation_details(response_data)
                st.error("❌ **Response Validation Failed**")
                st.error(f"**Missing or invalid fields:** {missing_info}")
                
                # Show the actual response for debugging
                with st.expander("🔍 Debug: View Parsed Response", expanded=False):
                    st.json(response_data)
                    st.caption("This shows what fields were extracted. Check if required fields are missing or have wrong types.")
                
                # Provide suggestions for fixing the issue
                st.info("💡 **How to fix this:**")
                st.markdown("""
                1. **Try again**: Sometimes the AI model has temporary issues
                2. **Check document quality**: Ensure your documents are clear and readable
                3. **Verify document content**: Make sure your policy document contains coverage information
                4. **Check medical bill**: Ensure the bill has itemized charges that are clearly visible
                5. **Try different documents**: Test with simpler, clearer documents first
                """)
                
                raise RuntimeError(f"Gemini API response missing required fields: {missing_info}")
            
            
            # Convert to ClaimData object
            claim_data = ClaimData.from_json(response_data)
            
            return claim_data
            
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            else:
                raise RuntimeError(f"Document processing failed: {str(e)}")
    
    def _check_daily_quota(self):
        """
        Check if we're approaching daily quota limits.
        Reset counter if it's a new day.
        """
        current_time = time.time()
        
        # Reset daily counter if it's a new day (24 hours since last reset)
        if current_time - self.request_reset_time > 86400:  # 24 hours in seconds
            self.daily_request_count = 0
            self.request_reset_time = current_time
        
        # Check if approaching daily limit
        if self.daily_request_count >= self.daily_request_limit:
            raise RuntimeError(
                f"Daily API request limit reached ({self.daily_request_limit} requests). "
                f"Please wait until tomorrow or upgrade to a paid plan for higher limits."
            )
        
        # Warn when approaching limit
        if self.daily_request_count >= self.daily_request_limit * 0.8:
            remaining = self.daily_request_limit - self.daily_request_count
            st.warning(f"⚠️ Approaching daily API limit. {remaining} requests remaining today.")
    
    def _enforce_rate_limit(self):
        """
        Enforce rate limiting to stay within free-tier limits.
        Ensures minimum interval between API requests and checks daily quota.
        """
        # Check daily quota first
        self._check_daily_quota()
        
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            st.info(f"⏳ Rate limiting: waiting {sleep_time:.1f}s to stay within free-tier limits...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.daily_request_count += 1
    
    def _make_api_call_with_retry(self, content_parts, max_retries: int = None, base_delay: float = None):
        """
        Make API call with retry logic for handling rate limits and timeouts.
        Optimized for free-tier usage with conservative retry settings.
        
        Args:
            content_parts: Content to send to Gemini API
            max_retries: Maximum number of retry attempts (uses instance default if None)
            base_delay: Base delay between retries (uses instance default if None)
            
        Returns:
            API response object
            
        Raises:
            RuntimeError: If all retry attempts fail
        """
        # Use instance defaults for free-tier optimization
        max_retries = max_retries or self.max_retries
        base_delay = base_delay or self.base_delay
        
        # Enforce rate limiting before making request
        self._enforce_rate_limit()
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                # Configure safety settings
                safety_settings = [
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=HarmBlockThreshold.BLOCK_NONE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=HarmBlockThreshold.BLOCK_NONE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=HarmBlockThreshold.BLOCK_NONE
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=HarmBlockThreshold.BLOCK_NONE
                    ),
                ]
                
                # Create generation config optimized for free-tier
                config = GenerateContentConfig(
                    safety_settings=safety_settings,
                    temperature=0.1,  # Low temperature for consistent results
                    max_output_tokens=4096,  # Increased to prevent JSON truncation
                    top_p=0.8,  # Conservative sampling
                    top_k=20   # Limited vocabulary for efficiency
                )
                
                # Make the API call
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=content_parts,
                    config=config
                )
                return response
                
            except Exception as e:
                last_exception = e
                error_str = str(e).lower()
                
                # Handle rate limiting
                if "rate limit" in error_str or "quota" in error_str:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        st.warning(f"⏳ Rate limit reached. Retrying in {delay:.1f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(
                            "API rate limit exceeded. Please wait a few minutes before trying again. "
                            "Consider upgrading to a paid plan for higher rate limits."
                        )
                
                # Handle timeouts
                elif "timeout" in error_str or "deadline" in error_str:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        st.warning(f"⏳ Request timeout. Retrying in {delay:.1f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(
                            "API request timed out after multiple attempts. "
                            "This may be due to large file sizes or network issues. "
                            "Please try again with smaller files or check your internet connection."
                        )
                
                # Handle service unavailable
                elif "unavailable" in error_str or "503" in error_str:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        st.warning(f"⏳ Service temporarily unavailable. Retrying in {delay:.1f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(
                            "Gemini API service is temporarily unavailable. "
                            "Please try again in a few minutes."
                        )
                
                # Handle permission errors
                elif "permission" in error_str or "401" in error_str or "403" in error_str:
                    raise RuntimeError(
                        "API key is invalid or lacks necessary permissions. "
                        "Please check your Google API key configuration."
                    )
                
                # Handle invalid arguments
                elif "invalid" in error_str or "400" in error_str:
                    raise RuntimeError(f"Invalid request format: {str(e)}")
                
                # Other errors - retry
                else:
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        st.warning(f"⏳ Unexpected error. Retrying in {delay:.1f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(f"API call failed after {max_retries} retries: {str(e)}")
        
        # This should never be reached, but just in case
        raise RuntimeError(f"API call failed: {str(last_exception)}")
    
    def _prepare_file_content(self, uploaded_file) -> Dict[str, str]:
        """
        Prepare uploaded file content for Gemini API with free-tier optimizations.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            Dictionary with mime_type and base64-encoded data
            
        Raises:
            ValueError: If file format is not supported or file is too large
            RuntimeError: If file cannot be read or processed
        """
        try:
            # Get file content
            file_bytes = uploaded_file.read()
            
            # Reset file pointer for potential future reads
            uploaded_file.seek(0)
            
            # Validate file is not empty
            if not file_bytes:
                raise ValueError(f"File '{uploaded_file.name}' is empty or could not be read")
            
            # Check file size with free-tier optimized limit
            file_size_mb = len(file_bytes) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                raise ValueError(
                    f"File '{uploaded_file.name}' is too large ({file_size_mb:.1f} MB). "
                    f"Maximum size for free-tier usage is {self.max_file_size_mb} MB. "
                    f"Please compress your file or use a smaller image resolution."
                )
            
            # Log file size for monitoring
            st.info(f"📄 Processing file: {uploaded_file.name} ({file_size_mb:.1f} MB)")
            
            # Determine MIME type
            mime_type = self._get_mime_type(uploaded_file.name)
            
            # Encode to base64
            try:
                encoded_data = base64.b64encode(file_bytes).decode('utf-8')
            except Exception as e:
                raise RuntimeError(f"Failed to encode file '{uploaded_file.name}': {str(e)}")
            
            return {
                "mime_type": mime_type,
                "data": encoded_data
            }
            
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            else:
                raise RuntimeError(f"Failed to prepare file '{uploaded_file.name}' for processing: {str(e)}")
    
    def _get_mime_type(self, filename: str) -> str:
        """
        Determine MIME type from filename.
        
        Args:
            filename: Name of the uploaded file
            
        Returns:
            MIME type string
            
        Raises:
            ValueError: If file format is not supported
        """
        # Get MIME type from filename
        mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type:
            # Fallback based on file extension
            extension = filename.lower().split('.')[-1] if '.' in filename else ''
            
            mime_type_map = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg', 
                'png': 'image/png'
            }
            
            mime_type = mime_type_map.get(extension)
        
        if not mime_type:
            raise ValueError(f"Unsupported file format: {filename}")
        
        # Validate supported formats
        supported_types = [
            'application/pdf',
            'image/jpeg',
            'image/png'
        ]
        
        if mime_type not in supported_types:
            raise ValueError(f"Unsupported MIME type: {mime_type}")
        
        return mime_type
    
    def _create_extraction_prompt(self) -> str:
        """
        Create structured extraction prompt for consistent JSON response.
        
        Returns:
            Formatted prompt string for Gemini API
        """
        return """Analyze the insurance policy and medical bill documents. Extract information and respond with ONLY valid JSON.

CRITICAL: Respond with ONLY JSON - no explanations, no markdown, no code blocks.

Required JSON format:
{
  "policy_name": "exact policy name from document",
  "copay_percentage": 20,
  "client_name": "name or null",
  "policy_number": "number or null", 
  "client_address": "address or null",
  "bill_items": [
    {
      "description": "service description",
      "cost": 1500.0,
      "is_covered": true,
      "rejection_reason": null
    }
  ]
}

Rules:
- policy_name: required string from policy document
- copay_percentage: required number 0-100 (use 20 if not found)
- client fields: extract from policy, use null if unclear
- bill_items: required array, extract ALL items from bill
- For each item: description (string), cost (number), is_covered (boolean), rejection_reason (string or null)
- If covered: rejection_reason = null
- If rejected: provide rejection_reason string
- Use true/false for booleans, null for empty values
- Start with { and end with }

Extract all bill line items. Be conservative with coverage decisions."""
    
    def _attempt_json_recovery(self, response_text: str) -> Optional[str]:
        """
        Attempt to recover from common JSON formatting issues in Gemini responses.
        
        Args:
            response_text: The raw response text from Gemini
            
        Returns:
            Fixed JSON string if recovery is possible, None otherwise
        """
        try:
            import re
            
            # Start with the original text
            fixed_text = response_text.strip()
            
            # Remove any non-JSON content before the first {
            json_start = fixed_text.find('{')
            if json_start > 0:
                fixed_text = fixed_text[json_start:]
            
            # Handle truncated JSON - try to find the last complete structure
            json_end = fixed_text.rfind('}')
            if json_end != -1:
                # Check if this looks like a truncated response
                remaining_text = fixed_text[json_end + 1:].strip()
                if remaining_text and not remaining_text.startswith('\n'):
                    # Likely truncated, try to reconstruct
                    fixed_text = fixed_text[:json_end + 1]
                    
                    # Count braces to see if we need to close any
                    open_braces = fixed_text.count('{')
                    close_braces = fixed_text.count('}')
                    open_brackets = fixed_text.count('[')
                    close_brackets = fixed_text.count(']')
                    
                    # Add missing closing braces/brackets
                    if open_brackets > close_brackets:
                        fixed_text = fixed_text.rstrip(',') + ']' * (open_brackets - close_brackets)
                    if open_braces > close_braces:
                        fixed_text = fixed_text.rstrip(',') + '}' * (open_braces - close_braces)
            else:
                # No closing brace found - definitely truncated
                # Try to find the last complete field and close properly
                
                # Remove any incomplete trailing content
                # Look for the last complete field (ends with , or } or ])
                last_complete = max(
                    fixed_text.rfind(','),
                    fixed_text.rfind('}'),
                    fixed_text.rfind(']')
                )
                
                if last_complete > 0:
                    fixed_text = fixed_text[:last_complete + 1]
                    
                    # Remove trailing comma if present
                    if fixed_text.endswith(','):
                        fixed_text = fixed_text[:-1]
                    
                    # Count and balance braces/brackets
                    open_braces = fixed_text.count('{')
                    close_braces = fixed_text.count('}')
                    open_brackets = fixed_text.count('[')
                    close_brackets = fixed_text.count(']')
                    
                    # Add missing closing brackets first, then braces
                    if open_brackets > close_brackets:
                        fixed_text += ']' * (open_brackets - close_brackets)
                    if open_braces > close_braces:
                        fixed_text += '}' * (open_braces - close_braces)
            
            # Fix common issues
            
            # 1. Remove trailing commas before closing brackets/braces
            fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
            
            # 2. Fix unquoted keys (but be careful not to break quoted strings)
            # This is a simple approach - only fix obvious cases
            fixed_text = re.sub(r'(\n\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', fixed_text)
            
            # 3. Fix single quotes to double quotes (but be careful with apostrophes)
            # Replace single quotes that are clearly JSON delimiters
            fixed_text = re.sub(r"'([^']*)'(\s*:)", r'"\1"\2', fixed_text)  # Keys
            fixed_text = re.sub(r":\s*'([^']*)'", r': "\1"', fixed_text)    # Values
            
            # 4. Fix common boolean/null values
            fixed_text = re.sub(r'\bTrue\b', 'true', fixed_text)
            fixed_text = re.sub(r'\bFalse\b', 'false', fixed_text)
            fixed_text = re.sub(r'\bNone\b', 'null', fixed_text)
            fixed_text = re.sub(r'\bNULL\b', 'null', fixed_text)
            
            # 5. Remove any remaining markdown or extra text
            fixed_text = re.sub(r'```[a-zA-Z]*\n?', '', fixed_text)
            fixed_text = re.sub(r'\n```', '', fixed_text)
            
            # 6. Fix missing commas between array/object elements
            # This is tricky and might not always work, but try basic cases
            fixed_text = re.sub(r'}\s*{', '},{', fixed_text)  # Between objects
            fixed_text = re.sub(r']\s*\[', '],[', fixed_text)  # Between arrays
            
            # 7. Fix numbers that might be quoted
            fixed_text = re.sub(r':\s*"(\d+\.?\d*)"', r': \1', fixed_text)
            
            # 8. Clean up whitespace
            fixed_text = fixed_text.strip()
            
            # 9. Final balance check for braces
            open_braces = fixed_text.count('{')
            close_braces = fixed_text.count('}')
            if open_braces > close_braces:
                fixed_text += '}' * (open_braces - close_braces)
            
            # Test if the fixed text is valid JSON
            json.loads(fixed_text)
            return fixed_text
            
        except Exception:
            # If recovery fails, return None
            return None
    
    def get_document_quality_tips(self) -> str:
        """
        Get tips for preparing high-quality documents for processing.
        
        Returns:
            Formatted string with document preparation advice
        """
        return """
        **📄 Document Quality Guidelines:**
        
        **For Policy Documents:**
        - Use the official PDF from your insurance provider
        - Ensure all text is clearly readable
        - Include pages with policy details, coverage information, and copay rates
        
        **For Medical Bills:**
        - Use high-resolution scans or photos (300+ DPI)
        - Ensure good lighting and contrast
        - Include all pages with itemized charges
        - Make sure line items and amounts are clearly visible
        
        **General Tips:**
        - Avoid shadows, glare, or reflections
        - Keep documents flat and straight (not rotated)
        - Use PDF format when possible for best results
        - Ensure file size is under 20MB for optimal processing
        """
    
    def get_troubleshooting_tips(self) -> str:
        """
        Get troubleshooting tips for JSON parsing issues.
        
        Returns:
            Formatted string with troubleshooting advice
        """
        return """
        **🔧 JSON Parsing Troubleshooting Tips:**
        
        **Document Quality Issues:**
        - Ensure documents are high-resolution and clearly readable
        - Avoid blurry, rotated, or low-contrast images
        - Try scanning documents at 300 DPI or higher
        
        **File Format Issues:**
        - Convert images to PDF format for better processing
        - Ensure PDFs are text-based, not just scanned images
        - Try different file formats (JPG → PNG → PDF)
        
        **Content Issues:**
        - Use standard medical bill and policy formats
        - Ensure all text is in English or clearly structured
        - Avoid handwritten documents when possible
        
        **System Issues:**
        - Try processing again (AI models can be inconsistent)
        - Wait a few minutes and retry if you hit rate limits
        - Try with simpler documents first to test the system
        
        **Alternative Approaches:**
        - Break complex documents into smaller sections
        - Use clearer document scans or photos
        - Ensure good lighting when photographing documents
        """
    
    def _get_validation_details(self, response: Dict[str, Any]) -> str:
        """
        Get detailed information about validation failures.
        
        Args:
            response: Parsed JSON response from Gemini API
            
        Returns:
            String describing what validation failed
        """
        issues = []
        
        # Check required top-level fields
        required_fields = {'policy_name', 'copay_percentage', 'bill_items'}
        missing_fields = [field for field in required_fields if field not in response]
        
        if missing_fields:
            issues.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Check field types and values
        if 'policy_name' in response:
            if not isinstance(response['policy_name'], str) or not response['policy_name'].strip():
                issues.append("policy_name must be a non-empty string")
        
        if 'copay_percentage' in response:
            copay = response['copay_percentage']
            if not isinstance(copay, (int, float)):
                issues.append(f"copay_percentage must be a number, got {type(copay).__name__}")
            elif not (0 <= copay <= 100):
                issues.append(f"copay_percentage must be between 0-100, got {copay}")
        
        if 'bill_items' in response:
            bill_items = response['bill_items']
            if not isinstance(bill_items, list):
                issues.append(f"bill_items must be a list, got {type(bill_items).__name__}")
            elif len(bill_items) == 0:
                issues.append("bill_items cannot be empty")
            else:
                # Check individual bill items
                for i, item in enumerate(bill_items):
                    item_issues = self._validate_bill_item_details(item)
                    if item_issues:
                        issues.append(f"bill_items[{i}]: {item_issues}")
        
        # Check optional fields if present
        for field_name in ['client_name', 'policy_number', 'client_address']:
            if field_name in response:
                value = response[field_name]
                if value is not None and (not isinstance(value, str) or not value.strip()):
                    issues.append(f"{field_name} must be a non-empty string or null")
        
        return "; ".join(issues) if issues else "Unknown validation error"
    
    def _validate_bill_item_details(self, item: Dict[str, Any]) -> str:
        """
        Get detailed validation information for a bill item.
        
        Args:
            item: Bill item dictionary
            
        Returns:
            String describing validation issues, empty if valid
        """
        issues = []
        
        # Check required fields
        required_fields = {'description', 'cost', 'is_covered'}
        missing_fields = [field for field in required_fields if field not in item]
        
        if missing_fields:
            issues.append(f"missing fields: {', '.join(missing_fields)}")
        
        # Check field types and values
        if 'description' in item:
            if not isinstance(item['description'], str) or not item['description'].strip():
                issues.append("description must be a non-empty string")
        
        if 'cost' in item:
            if not isinstance(item['cost'], (int, float)):
                issues.append(f"cost must be a number, got {type(item['cost']).__name__}")
            elif item['cost'] < 0:
                issues.append(f"cost must be non-negative, got {item['cost']}")
        
        if 'is_covered' in item:
            if not isinstance(item['is_covered'], bool):
                issues.append(f"is_covered must be boolean, got {type(item['is_covered']).__name__}")
        
        # Check rejection_reason logic
        if 'is_covered' in item and 'rejection_reason' in item:
            if item['is_covered'] and item['rejection_reason'] is not None:
                issues.append("covered items should have null rejection_reason")
            elif not item['is_covered'] and (item['rejection_reason'] is None or not isinstance(item['rejection_reason'], str) or not item['rejection_reason'].strip()):
                issues.append("rejected items must have a non-empty rejection_reason")
        
        return "; ".join(issues)
    
    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """
        Validate Gemini API response structure.
        
        Args:
            response: Parsed JSON response from Gemini API
            
        Returns:
            True if response is valid, False otherwise
        """
        # Check required top-level fields
        required_fields = {'policy_name', 'copay_percentage', 'bill_items'}
        if not all(field in response for field in required_fields):
            return False
        
        # Validate policy_name
        if not isinstance(response['policy_name'], str) or not response['policy_name'].strip():
            return False
        
        # Validate copay_percentage
        copay = response['copay_percentage']
        if not isinstance(copay, (int, float)) or not (0 <= copay <= 100):
            return False
        
        # Validate optional client fields
        client_name = response.get('client_name')
        if client_name is not None and (not isinstance(client_name, str) or not client_name.strip()):
            return False
        
        policy_number = response.get('policy_number')
        if policy_number is not None and (not isinstance(policy_number, str) or not policy_number.strip()):
            return False
        
        client_address = response.get('client_address')
        if client_address is not None and (not isinstance(client_address, str) or not client_address.strip()):
            return False
        
        # Validate bill_items
        bill_items = response['bill_items']
        if not isinstance(bill_items, list) or len(bill_items) == 0:
            return False
        
        # Validate each bill item
        for item in bill_items:
            if not self._validate_bill_item(item):
                return False
        
        return True
    
    def _validate_bill_item(self, item: Dict[str, Any]) -> bool:
        """
        Validate individual bill item structure.
        
        Args:
            item: Bill item dictionary from API response
            
        Returns:
            True if item is valid, False otherwise
        """
        # Check required fields
        required_fields = {'description', 'cost', 'is_covered'}
        if not all(field in item for field in required_fields):
            return False
        
        # Validate description
        if not isinstance(item['description'], str) or not item['description'].strip():
            return False
        
        # Validate cost
        if not isinstance(item['cost'], (int, float)) or item['cost'] < 0:
            return False
        
        # Validate is_covered
        if not isinstance(item['is_covered'], bool):
            return False
        
        # Validate rejection_reason logic
        rejection_reason = item.get('rejection_reason')
        if item['is_covered']:
            # Covered items should have null rejection_reason
            if rejection_reason is not None:
                return False
        else:
            # Rejected items should have a rejection reason
            if rejection_reason is None or not isinstance(rejection_reason, str) or not rejection_reason.strip():
                return False
        
        return True
    
    def get_quota_status(self) -> Dict[str, Any]:
        """
        Get current quota usage status for display.
        
        Returns:
            Dictionary with quota information
        """
        current_time = time.time()
        
        # Reset daily counter if it's a new day
        if current_time - self.request_reset_time > 86400:
            self.daily_request_count = 0
            self.request_reset_time = current_time
        
        usage_percentage = (self.daily_request_count / self.daily_request_limit) * 100
        remaining_requests = self.daily_request_limit - self.daily_request_count
        
        return {
            "daily_used": self.daily_request_count,
            "daily_limit": self.daily_request_limit,
            "remaining": remaining_requests,
            "usage_percentage": usage_percentage,
            "reset_time": self.request_reset_time + 86400  # Next reset time
        }
    
    def test_api_connection(self) -> Tuple[bool, str]:
        """
        Test the API connection and configuration.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Simple test with minimal content
            test_content = [{"text": "Respond with just the word 'OK'"}]
            
            # Use the API call method
            response = self._make_api_call_with_retry(test_content)
            
            # Extract text using the same logic as process_documents
            response_text = None
            if hasattr(response, 'text'):
                response_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    parts = candidate.content.parts
                    if parts and hasattr(parts[0], 'text'):
                        response_text = parts[0].text
            elif hasattr(response, 'content'):
                response_text = str(response.content)
            
            if response_text and response_text.strip():
                return True, f"API connection successful using model: {self.model_name}"
            else:
                return False, "API returned empty response"
                
        except Exception as e:
            error_str = str(e).lower()
            if "permission" in error_str or "401" in error_str or "403" in error_str:
                return False, "Invalid API key or insufficient permissions"
            elif "quota" in error_str or "rate limit" in error_str:
                return False, "API quota exceeded - please wait or upgrade your plan"
            elif "unavailable" in error_str or "503" in error_str:
                return False, "Gemini API service is temporarily unavailable"
            elif "timeout" in error_str or "deadline" in error_str:
                return False, "API connection timeout - check your internet connection"
            else:
                return False, f"Connection test failed: {str(e)}"