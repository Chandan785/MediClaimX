# Implementation Plan: Medical Claims Processor

## Overview

This implementation plan breaks down the Medical Claims Processor into discrete coding tasks that build incrementally toward a complete Streamlit application. Each task focuses on specific functionality while ensuring integration with previous components.

## Tasks

- [x] 1. Set up project structure and dependencies
  - Create project directory structure
  - Set up requirements.txt with Streamlit, google-generativeai, pandas, hypothesis, reportlab
  - Create app.py with hardcoded GOOGLE_API_KEY variable
  - Initialize basic Streamlit app structure
  - _Requirements: 6.1, 8.1, 8.2, 8.3, 8.4, 9.6_

- [-] 2. Implement core data models
  - [x] 2.1 Create data model classes (BillItem, ClaimData, CalculationResult)
    - Write Python dataclasses for all data structures
    - Implement serialization methods (to_dict, from_json)
    - Add validation methods for data integrity
    - _Requirements: 2.3, 3.2, 3.3, 3.4_

  - [ ]* 2.2 Write property test for data model serialization
    - **Property 10: Data model round trip**
    - **Validates: Requirements 2.3**

  - [ ]* 2.3 Write unit tests for data models
    - Test validation edge cases and error conditions
    - Test serialization/deserialization with known data
    - _Requirements: 2.3_

- [x] 3. Build file upload and validation system
  - [x] 3.1 Implement file upload interface
    - Create side-by-side Streamlit file uploaders
    - Add file format validation (PDF for policy, PDF/image for bills)
    - Implement file size and content validation
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 3.2 Write property test for file validation
    - **Property 1: File Format Validation**
    - **Validates: Requirements 1.2, 1.3, 1.4**

  - [ ]* 3.3 Write unit tests for file upload
    - Test specific file format acceptance/rejection
    - Test error message display for invalid files
    - _Requirements: 1.2, 1.3, 1.4_

- [x] 4. Implement Gemini AI integration
  - [x] 4.1 Create GeminiProcessor class
    - Implement document processing with google-generativeai library
    - Create structured extraction prompt for JSON response
    - Add response validation and error handling
    - Handle both PDF and image file formats
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 4.2 Write property test for API integration
    - **Property 2: API Integration Consistency**
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 4.3 Write property test for response validation
    - **Property 3: Response Structure Validation**
    - **Validates: Requirements 2.3, 2.4**

  - [ ]* 4.4 Write unit tests for Gemini integration
    - Test API call structure and prompt formatting
    - Test error handling for API failures
    - Test response parsing with mock data
    - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [x] 5. Checkpoint - Ensure file upload and AI integration work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Build calculation engine
  - [x] 6.1 Implement ClaimCalculator class
    - Create calculation methods using Pandas
    - Implement covered items summation logic
    - Add copay percentage application
    - Calculate rejected amounts separately
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [ ]* 6.2 Write property test for calculation accuracy
    - **Property 4: Calculation Accuracy**
    - **Validates: Requirements 3.2, 3.3, 3.4**

  - [ ]* 6.3 Write unit tests for calculations
    - Test specific calculation scenarios
    - Test edge cases (zero amounts, 100% copay)
    - Test error handling for invalid data
    - _Requirements: 3.2, 3.3, 3.4_

- [-] 7. Create results display interface
  - [x] 7.1 Implement results display components
    - Create summary metrics display (total billed, approved, rejected)
    - Build detailed results table with color coding
    - Add rejection reason display for uncovered items
    - Implement visual distinction between approved/rejected amounts
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 7.2 Write property test for display completeness
    - **Property 5: Results Display Completeness**
    - **Validates: Requirements 4.1, 4.2, 4.4**

  - [ ]* 7.3 Write property test for visual feedback
    - **Property 6: Visual Feedback Consistency**
    - **Validates: Requirements 4.3, 4.5**

  - [ ]* 7.4 Write unit tests for UI components
    - Test specific display formatting
    - Test color coding for rejected items
    - _Requirements: 4.3, 4.4, 4.5_

- [-] 8. Implement CSV export functionality
  - [x] 8.1 Create CSV export system
    - Implement CSV generation with all bill items
    - Add required columns (description, cost, is_covered, rejection_reason)
    - Include summary information in export
    - Add Streamlit download button functionality
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 8.2 Write property test for CSV export
    - **Property 7: CSV Export Completeness**
    - **Validates: Requirements 5.2, 5.3, 5.4**

  - [ ]* 8.3 Write unit tests for CSV export
    - Test CSV structure and content
    - Test download button functionality
    - _Requirements: 5.2, 5.3, 5.4, 5.5_

- [x] 9. Implement PDF report generation
  - [x] 9.1 Update data models for client details
    - Add client_name, policy_number, client_address fields to ClaimData
    - Update Gemini extraction prompt to include client details
    - Modify validation to handle optional client fields
    - _Requirements: 8.2_

  - [x] 9.2 Create PDF report generator
    - Implement PDFReportGenerator class using reportlab library
    - Add methods for header, summary, and details sections
    - Implement proper PDF formatting and styling
    - Add currency formatting utilities
    - _Requirements: 8.2, 8.3, 8.4, 8.6, 8.7_

  - [x] 9.3 Integrate PDF generation with UI
    - Add PDF download button to results interface
    - Connect PDF generator to claim results
    - Implement PDF file download functionality
    - Add error handling for PDF generation
    - _Requirements: 8.1, 8.5_

  - [ ]* 9.4 Write property test for PDF content completeness
    - **Property 11: PDF Content Completeness**
    - **Validates: Requirements 8.2**

  - [ ]* 9.5 Write property test for PDF claim data inclusion
    - **Property 12: PDF Claim Data Inclusion**
    - **Validates: Requirements 8.3, 8.7**

  - [ ]* 9.6 Write property test for PDF structure consistency
    - **Property 13: PDF Structure Consistency**
    - **Validates: Requirements 8.4**

  - [ ]* 9.7 Write property test for PDF summary metrics
    - **Property 14: PDF Summary Metrics Inclusion**
    - **Validates: Requirements 8.6**

  - [ ]* 9.8 Write unit tests for PDF generation
    - Test PDF creation with specific client data
    - Test PDF formatting and structure
    - Test error handling for PDF generation failures
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [-] 10. Add comprehensive error handling
  - [x] 10.1 Implement error handling system
    - Add error handling for file upload failures
    - Implement API timeout and rate limit handling
    - Create user-friendly error messages
    - Add loading indicators and progress feedback
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 7.5_

  - [ ]* 10.2 Write property test for error handling
    - **Property 8: Error Handling Robustness**
    - **Validates: Requirements 2.5, 6.2, 6.3, 6.4, 7.5**

  - [ ]* 10.3 Write property test for input validation
    - **Property 9: Input Validation Completeness**
    - **Validates: Requirements 1.5, 6.4**

  - [ ]* 10.4 Write unit tests for error scenarios
    - Test specific error conditions and messages
    - Test loading state management
    - _Requirements: 6.2, 6.3, 6.5_

- [-] 11. Integration and final wiring
  - [x] 11.1 Wire all components together
    - Connect file upload to AI processing
    - Link AI processing to calculation engine
    - Connect calculations to results display
    - Integrate CSV export with results
    - Add main processing workflow and button
    - _Requirements: All requirements integration_

  - [ ]* 11.2 Write property test for UI feedback
    - **Property 10: UI Feedback Consistency**
    - **Validates: Requirements 1.5, 6.5**

  - [ ]* 11.3 Write integration tests
    - Test complete end-to-end workflow
    - Test error recovery and state management
    - _Requirements: All requirements_

- [ ] 12. Final checkpoint and optimization
  - [x] 12.1 Optimize for free-tier usage
    - Review API call efficiency
    - Add rate limiting protection
    - Optimize file processing
    - _Requirements: 7.1, 7.4, 7.5_

  - [ ] 12.2 Final testing and validation
    - Run complete test suite
    - Verify all requirements are met
    - Test with sample documents
    - _Requirements: All requirements_

- [ ] 13. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using hypothesis library
- Unit tests validate specific examples and edge cases
- The hardcoded GOOGLE_API_KEY should be placed at the top of app.py for easy configuration