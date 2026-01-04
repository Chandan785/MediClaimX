"""
Enhanced Gemini AI Processor with Intelligent Coverage Determination

This module provides advanced document processing with policy-based coverage analysis.
It determines which medical services are covered vs rejected based on policy rules.
"""

import json
import base64
import mimetypes
import time
from typing import Optional, Dict, Any, Tuple, Union, List
import google.genai as genai
from google.genai.types import GenerateContentConfig, SafetySetting, HarmCategory, HarmBlockThreshold
import streamlit as st

from .models import ClaimData, BillItem


class EnhancedGeminiProcessor:
    """
    Enhanced processor with intelligent coverage determination capabilities.
    
    This class provides:
    - Advanced policy analysis and rule extraction
    - Intelligent coverage determination for each bill item
    - Specific rejection reasons based on policy terms
    - Service categorization and matching
    """
    
    def __init__(self, api_key: str):
        """Initialize the enhanced processor with API credentials."""
        if not api_key or not isinstance(api_key, str) or api_key.strip() == "":
            raise ValueError("API key must be a non-empty string")
        
        if api_key.strip() == "your-google-api-key-here":
            raise ValueError("Please replace the placeholder API key with your actual Google API key")
        
        self.api_key = api_key.strip()
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "models/gemini-flash-latest"
        
        # Free-tier optimization settings
        self.max_file_size_mb = 10
        self.max_retries = 1
        self.base_delay = 3.0
        self.request_timeout = 20
        
        # Rate limiting tracking
        self.last_request_time = 0
        self.min_request_interval = 2.0
        self.daily_request_count = 0
        self.daily_request_limit = 1000
        self.request_reset_time = 0
    
    def process_documents_with_coverage_analysis(self, policy_file, bill_file) -> ClaimData:
        """
        Process documents with intelligent coverage determination.
        
        Args:
            policy_file: Insurance policy document
            bill_file: Medical bill document
            
        Returns:
            ClaimData with accurate coverage determinations
        """
        try:
            # Step 1: Analyze policy document first
            st.info("🔍 **Step 1**: Analyzing insurance policy for coverage rules...")
            policy_analysis = self._analyze_policy_document(policy_file)
            
            # Step 2: Extract bill items
            st.info("📋 **Step 2**: Extracting medical bill items...")
            bill_items = self._extract_bill_items(bill_file)
            
            # Step 3: Determine coverage for each item
            st.info("⚖️ **Step 3**: Determining coverage for each item based on policy...")
            coverage_decisions = self._determine_coverage(policy_analysis, bill_items)
            
            # Step 4: Create final claim data
            st.info("✅ **Step 4**: Finalizing claim data with coverage decisions...")
            claim_data = self._create_claim_data(policy_analysis, coverage_decisions)
            
            # Display coverage summary
            self._display_coverage_summary(claim_data)
            
            return claim_data
            
        except Exception as e:
            st.error(f"❌ **Enhanced processing failed**: {str(e)}")
            # Fallback to basic processing
            st.warning("🔄 **Falling back to basic processing**...")
            return self._fallback_basic_processing(policy_file, bill_file)
    
    def _analyze_policy_document(self, policy_file) -> Dict[str, Any]:
        """
        Analyze policy document to extract coverage rules and exclusions.
        
        Args:
            policy_file: Policy document file
            
        Returns:
            Dictionary containing policy analysis results
        """
        try:
            # Prepare policy content
            policy_content = self._prepare_file_content(policy_file)
            
            # Create policy analysis prompt
            prompt = self._create_policy_analysis_prompt()
            
            # Prepare content for API
            content_parts = [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": policy_content["mime_type"],
                        "data": policy_content["data"]
                    }
                }
            ]
            
            # Make API call
            response = self._make_api_call_with_retry(content_parts)
            response_text = self._extract_response_text(response)
            
            # Parse policy analysis
            policy_data = self._parse_json_response(response_text, "policy analysis")
            
            return policy_data
            
        except Exception as e:
            st.warning(f"⚠️ **Policy analysis failed**: {str(e)}")
            # Return default policy structure
            return {
                "policy_name": "Policy Analysis Required",
                "copay_percentage": 0.0,
                "covered_services": [
                    "medications", "medical supplies", "diagnostic tests", 
                    "procedures", "consultations", "hospitalization"
                ],
                "exclusions": [
                    "cosmetic procedures", "experimental treatments", 
                    "non-medical items", "personal care items"
                ],
                "coverage_limits": {},
                "pre_auth_required": []
            }
    
    def _extract_bill_items(self, bill_file) -> List[Dict[str, Any]]:
        """
        Extract detailed bill items from medical bill.
        
        Args:
            bill_file: Medical bill document
            
        Returns:
            List of extracted bill items
        """
        try:
            # Prepare bill content
            bill_content = self._prepare_file_content(bill_file)
            
            # Create bill extraction prompt
            prompt = self._create_bill_extraction_prompt()
            
            # Prepare content for API
            content_parts = [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": bill_content["mime_type"],
                        "data": bill_content["data"]
                    }
                }
            ]
            
            # Make API call
            response = self._make_api_call_with_retry(content_parts)
            response_text = self._extract_response_text(response)
            
            # Parse bill items
            bill_data = self._parse_json_response(response_text, "bill extraction")
            
            return bill_data.get("bill_items", [])
            
        except Exception as e:
            st.warning(f"⚠️ **Bill extraction failed**: {str(e)}")
            return []
    
    def _determine_coverage(self, policy_analysis: Dict[str, Any], bill_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Determine coverage for each bill item based on policy rules.
        
        Args:
            policy_analysis: Policy analysis results
            bill_items: Extracted bill items
            
        Returns:
            List of bill items with coverage decisions
        """
        try:
            # Create coverage determination prompt
            prompt = self._create_coverage_determination_prompt(policy_analysis, bill_items)
            
            # Prepare content for API
            content_parts = [{"text": prompt}]
            
            # Make API call
            response = self._make_api_call_with_retry(content_parts)
            response_text = self._extract_response_text(response)
            
            # Parse coverage decisions
            coverage_data = self._parse_json_response(response_text, "coverage determination")
            
            return coverage_data.get("coverage_decisions", bill_items)
            
        except Exception as e:
            st.warning(f"⚠️ **Coverage determination failed**: {str(e)}")
            # Apply basic coverage rules
            return self._apply_basic_coverage_rules(policy_analysis, bill_items)
    
    def _apply_basic_coverage_rules(self, policy_analysis: Dict[str, Any], bill_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply basic coverage rules when AI determination fails.
        
        Args:
            policy_analysis: Policy analysis results
            bill_items: Bill items to analyze
            
        Returns:
            Bill items with basic coverage decisions
        """
        covered_keywords = policy_analysis.get("covered_services", [])
        exclusion_keywords = policy_analysis.get("exclusions", [])
        
        for item in bill_items:
            description = item.get("description", "").lower()
            
            # Check for exclusions first
            is_excluded = any(exclusion.lower() in description for exclusion in exclusion_keywords)
            
            if is_excluded:
                item["is_covered"] = False
                item["rejection_reason"] = "Service excluded by policy terms"
            else:
                # Check for covered services
                is_covered = any(service.lower() in description for service in covered_keywords)
                
                if is_covered:
                    item["is_covered"] = True
                    item["rejection_reason"] = None
                else:
                    # Default to not covered for unknown items
                    item["is_covered"] = False
                    item["rejection_reason"] = "Service not explicitly covered by policy - requires manual review"
        
        return bill_items
    
    def _create_policy_analysis_prompt(self) -> str:
        """Create prompt for policy document analysis."""
        return """🔍 COMPREHENSIVE INSURANCE POLICY ANALYSIS

You are an expert insurance policy analyst. Analyze this insurance policy document and extract ALL coverage information with MAXIMUM DETAIL.

📋 REQUIRED ANALYSIS SECTIONS:

1. **POLICY IDENTIFICATION**
   - Policy name and number
   - Copay percentage (if specified, otherwise 0)
   - Coverage limits and caps

2. **COVERED SERVICES** (Extract ALL covered items)
   - Medical procedures and treatments
   - Medications and pharmaceuticals
   - Medical supplies and equipment
   - Diagnostic tests and imaging
   - Hospitalization services
   - Consultation fees
   - Emergency services
   - Preventive care

3. **EXCLUSIONS** (Extract ALL excluded items)
   - Cosmetic procedures
   - Experimental treatments
   - Non-medical items
   - Personal care products
   - Items not covered by policy
   - Age or condition restrictions

4. **SPECIAL REQUIREMENTS**
   - Pre-authorization required services
   - Coverage limits per service
   - Waiting periods
   - Network restrictions

🎯 REQUIRED JSON OUTPUT:
{
  "policy_name": "exact policy name",
  "policy_number": "policy number if found",
  "copay_percentage": 0,
  "covered_services": [
    "medications",
    "medical supplies",
    "diagnostic tests",
    "procedures",
    "consultations",
    "hospitalization",
    "emergency services"
  ],
  "exclusions": [
    "cosmetic procedures",
    "experimental treatments",
    "non-medical items",
    "personal care items"
  ],
  "coverage_limits": {
    "annual_limit": 500000,
    "room_rent_limit": 5000
  },
  "pre_auth_required": [
    "major surgeries",
    "expensive procedures"
  ]
}

⚡ EXTRACT EVERY COVERAGE RULE - BE COMPREHENSIVE!"""
    
    def _create_bill_extraction_prompt(self) -> str:
        """Create prompt for bill item extraction."""
        return """📋 COMPREHENSIVE MEDICAL BILL EXTRACTION

Extract EVERY line item from this medical bill with ABSOLUTE PRECISION.

🎯 EXTRACTION REQUIREMENTS:
- Extract 40+ individual items minimum
- Include exact descriptions with HSN codes
- Capture all dates, quantities, and costs
- Categorize each item by service type

📊 REQUIRED JSON OUTPUT:
{
  "bill_items": [
    {
      "category": "medication",
      "description": "PANTEC IV 40MG ( HSN:30049039 )",
      "date": "05/11/2025",
      "quantity": 1,
      "unit_cost": 52.96,
      "cost": 52.96
    }
  ]
}

🔥 CATEGORIES TO USE:
- medication
- medical_supply
- diagnostic_test
- procedure
- consultation
- room_charges
- equipment
- other

⚡ EXTRACT EVERY SINGLE ITEM - NO EXCEPTIONS!"""
    
    def _create_coverage_determination_prompt(self, policy_analysis: Dict[str, Any], bill_items: List[Dict[str, Any]]) -> str:
        """Create prompt for coverage determination."""
        policy_json = json.dumps(policy_analysis, indent=2)
        items_json = json.dumps(bill_items[:10], indent=2)  # Sample for context
        
        return f"""⚖️ INTELLIGENT COVERAGE DETERMINATION

You are an expert medical claims processor. Determine coverage for each bill item based on the policy rules.

📋 POLICY RULES:
{policy_json}

📄 SAMPLE BILL ITEMS (analyze ALL items in the full list):
{items_json}

🎯 COVERAGE DETERMINATION RULES:

1. **COVERED ITEMS**: Match against policy covered_services
   - Medications → covered if in policy
   - Medical supplies → covered if medically necessary
   - Procedures → covered if listed in policy
   - Diagnostics → covered if medically required

2. **REJECTED ITEMS**: Check against exclusions
   - Personal care items → rejected
   - Non-medical supplies → rejected
   - Cosmetic items → rejected
   - Items in exclusions list → rejected

3. **REJECTION REASONS** (be specific):
   - "Not covered by policy terms"
   - "Personal care item - not medical necessity"
   - "Excluded service per policy"
   - "Requires pre-authorization"
   - "Exceeds coverage limit"

📊 REQUIRED JSON OUTPUT:
{{
  "coverage_decisions": [
    {{
      "category": "medication",
      "description": "PANTEC IV 40MG ( HSN:30049039 )",
      "date": "05/11/2025",
      "quantity": 1,
      "unit_cost": 52.96,
      "cost": 52.96,
      "is_covered": true,
      "rejection_reason": null,
      "coverage_reason": "Medication covered by policy"
    }},
    {{
      "category": "other",
      "description": "PERSONAL SOAP BAR",
      "date": "05/11/2025",
      "quantity": 1,
      "unit_cost": 25.00,
      "cost": 25.00,
      "is_covered": false,
      "rejection_reason": "Personal care item - not medical necessity",
      "coverage_reason": null
    }}
  ]
}}

⚡ ANALYZE EACH ITEM CAREFULLY - PROVIDE SPECIFIC REASONS!

FULL BILL ITEMS TO ANALYZE:
{json.dumps(bill_items, indent=2)}"""
    
    def _create_claim_data(self, policy_analysis: Dict[str, Any], coverage_decisions: List[Dict[str, Any]]) -> ClaimData:
        """Create ClaimData object from analysis results."""
        
        # Convert coverage decisions to BillItem objects
        bill_items = []
        for item in coverage_decisions:
            bill_item = BillItem(
                description=item.get("description", "Unknown Service"),
                cost=float(item.get("cost", 0)),
                is_covered=bool(item.get("is_covered", False)),
                rejection_reason=item.get("rejection_reason"),
                date=item.get("date"),
                quantity=int(item.get("quantity", 1)),
                unit_cost=float(item.get("unit_cost", item.get("cost", 0)))
            )
            bill_items.append(bill_item)
        
        # Create ClaimData
        claim_data = ClaimData(
            policy_name=policy_analysis.get("policy_name", "Policy Analysis Required"),
            copay_percentage=float(policy_analysis.get("copay_percentage", 0)),
            bill_items=bill_items,
            client_name=policy_analysis.get("client_name"),
            policy_number=policy_analysis.get("policy_number"),
            client_address=policy_analysis.get("client_address")
        )
        
        return claim_data
    
    def _display_coverage_summary(self, claim_data: ClaimData):
        """Display coverage analysis summary."""
        covered_items = [item for item in claim_data.bill_items if item.is_covered]
        rejected_items = [item for item in claim_data.bill_items if not item.is_covered]
        
        total_items = len(claim_data.bill_items)
        covered_count = len(covered_items)
        rejected_count = len(rejected_items)
        
        st.success(f"✅ **Coverage Analysis Complete**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Items", total_items)
        
        with col2:
            st.metric("Covered Items", covered_count, f"{(covered_count/total_items*100):.1f}%")
        
        with col3:
            st.metric("Rejected Items", rejected_count, f"{(rejected_count/total_items*100):.1f}%")
        
        # Show sample rejections
        if rejected_items:
            with st.expander("🔍 Sample Rejected Items", expanded=False):
                for item in rejected_items[:5]:
                    st.error(f"❌ **{item.description[:50]}...** - {item.rejection_reason}")
    
    def _fallback_basic_processing(self, policy_file, bill_file) -> ClaimData:
        """Fallback to basic processing if enhanced processing fails."""
        from .gemini_processor import GeminiProcessor
        
        basic_processor = GeminiProcessor(self.api_key)
        return basic_processor.process_documents(policy_file, bill_file)
    
    # Utility methods (reuse from base processor)
    def _prepare_file_content(self, uploaded_file) -> Dict[str, str]:
        """Prepare file content for API (reuse from base class)."""
        try:
            file_bytes = uploaded_file.read()
            uploaded_file.seek(0)
            
            if not file_bytes:
                raise ValueError(f"File '{uploaded_file.name}' is empty")
            
            file_size_mb = len(file_bytes) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                raise ValueError(f"File too large: {file_size_mb:.1f} MB")
            
            mime_type = self._get_mime_type(uploaded_file.name)
            encoded_data = base64.b64encode(file_bytes).decode('utf-8')
            
            return {"mime_type": mime_type, "data": encoded_data}
            
        except Exception as e:
            raise RuntimeError(f"Failed to prepare file: {str(e)}")
    
    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        
        if not mime_type:
            extension = filename.lower().split('.')[-1] if '.' in filename else ''
            mime_type_map = {
                'pdf': 'application/pdf',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png'
            }
            mime_type = mime_type_map.get(extension)
        
        if not mime_type or mime_type not in ['application/pdf', 'image/jpeg', 'image/png']:
            raise ValueError(f"Unsupported file format: {filename}")
        
        return mime_type
    
    def _make_api_call_with_retry(self, content_parts):
        """Make API call with retry logic."""
        self._enforce_rate_limit()
        
        for attempt in range(self.max_retries + 1):
            try:
                safety_settings = [
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_NONE),
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_NONE),
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_NONE),
                    SafetySetting(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_NONE),
                ]
                
                config = GenerateContentConfig(
                    safety_settings=safety_settings,
                    temperature=0.0,
                    max_output_tokens=32768,
                    top_p=0.98,
                    top_k=50
                )
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=content_parts,
                    config=config
                )
                return response
                
            except Exception as e:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    st.warning(f"⏳ Retrying in {delay:.1f}s... (Attempt {attempt + 1}/{self.max_retries})")
                    time.sleep(delay)
                    continue
                else:
                    raise RuntimeError(f"API call failed: {str(e)}")
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.daily_request_count += 1
    
    def _extract_response_text(self, response) -> str:
        """Extract text from API response."""
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                parts = candidate.content.parts
                if parts and hasattr(parts[0], 'text'):
                    return parts[0].text
        elif hasattr(response, 'content'):
            return str(response.content)
        
        raise RuntimeError("Could not extract text from API response")
    
    def _parse_json_response(self, response_text: str, context: str) -> Dict[str, Any]:
        """Parse JSON response with error handling."""
        try:
            # Clean response text
            cleaned_text = response_text.strip()
            
            # Remove markdown formatting
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            
            cleaned_text = cleaned_text.strip()
            
            # Extract JSON
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}')
            
            if json_start != -1 and json_end != -1:
                json_text = cleaned_text[json_start:json_end + 1]
                return json.loads(json_text)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            st.warning(f"⚠️ **JSON parsing failed for {context}**: {str(e)}")
            return {}