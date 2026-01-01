# Requirements Document

## Introduction

The Intelligent Automated Medical Claims Processor is a Streamlit-based web application that automates the verification of medical reimbursement claims. The system extracts data from insurance policy documents and medical bills using Google Gemini 1.5 Flash, then calculates reimbursable amounts based on policy rules using deterministic logic.

## Glossary

- **System**: The Medical Claims Processor application
- **Policy_Document**: An insurance policy PDF file uploaded by the user
- **Medical_Bill**: A medical bill image or PDF file uploaded by the user
- **Gemini_API**: Google Gemini 1.5 Flash AI model service
- **Claim_Data**: Structured JSON data extracted from documents by Gemini
- **Reimbursable_Amount**: The final amount approved for reimbursement after applying policy rules
- **Bill_Item**: Individual line item from a medical bill with description, cost, and coverage status
- **Copay_Percentage**: The percentage of covered costs that the patient must pay
- **PDF_Report**: A formatted PDF document containing client details and claim results in tabular format
- **Client_Details**: Basic information about the policyholder extracted from the policy document

## Requirements

### Requirement 1: Document Upload Interface

**User Story:** As a user, I want to upload insurance policy and medical bill documents, so that I can process my reimbursement claim.

#### Acceptance Criteria

1. THE System SHALL provide two side-by-side file upload widgets for Policy_Document and Medical_Bill
2. WHEN a user uploads a Policy_Document, THE System SHALL accept PDF format files
3. WHEN a user uploads a Medical_Bill, THE System SHALL accept both image and PDF format files
4. WHEN invalid file formats are uploaded, THE System SHALL display appropriate error messages
5. THE System SHALL display the uploaded file names to confirm successful upload

### Requirement 2: AI-Powered Data Extraction

**User Story:** As a user, I want the system to automatically extract relevant information from my documents, so that I don't have to manually enter claim details.

#### Acceptance Criteria

1. WHEN both documents are uploaded and the process button is clicked, THE System SHALL send both files to Gemini_API
2. THE System SHALL use a structured prompt to request JSON-formatted extraction from Gemini_API
3. THE Gemini_API SHALL return Claim_Data containing policy_name, copay_percentage, and bill_items array
4. WHEN Gemini_API returns data, THE System SHALL validate the JSON structure before processing
5. IF Gemini_API fails or returns invalid data, THEN THE System SHALL display appropriate error messages

### Requirement 3: Deterministic Calculation Engine

**User Story:** As a user, I want accurate mathematical calculations of my reimbursement, so that I can trust the system's financial computations.

#### Acceptance Criteria

1. THE System SHALL use Python and Pandas for all mathematical calculations
2. WHEN calculating reimbursable amounts, THE System SHALL sum costs of all Bill_Items where is_covered is true
3. THE System SHALL apply the Copay_Percentage to the total covered amount to determine final reimbursement
4. THE System SHALL calculate rejected amounts by summing costs of Bill_Items where is_covered is false
5. THE System SHALL NOT use AI for any mathematical computations

### Requirement 4: Results Display and Visualization

**User Story:** As a user, I want to see a clear breakdown of my claim results, so that I can understand what was approved and rejected.

#### Acceptance Criteria

1. WHEN processing is complete, THE System SHALL display summary metrics including Total Billed, Policy Limit, and Approved Amount
2. THE System SHALL display a detailed table showing all Bill_Items with their coverage status
3. WHEN displaying the results table, THE System SHALL color-code rejected items in red
4. THE System SHALL show rejection reasons for items that are not covered
5. THE System SHALL clearly distinguish between approved and rejected amounts in the display

### Requirement 5: Data Export Functionality

**User Story:** As a user, I want to download my claim results as a CSV file, so that I can keep records or share them with others.

#### Acceptance Criteria

1. WHEN claim processing is complete, THE System SHALL provide a download button for CSV export
2. THE System SHALL generate a CSV file containing all Bill_Items with their details and coverage status
3. THE CSV file SHALL include columns for description, cost, is_covered, and rejection_reason
4. THE System SHALL include summary information in the CSV export
5. WHEN the download button is clicked, THE System SHALL initiate file download immediately

### Requirement 6: Error Handling and User Feedback

**User Story:** As a system administrator, I want robust error handling, so that users receive helpful feedback when issues occur.

#### Acceptance Criteria

1. THE System SHALL hardcode the GOOGLE_API_KEY variable directly in app.py for easy configuration
2. WHEN file upload fails, THE System SHALL provide specific error information
3. WHEN Gemini_API is unavailable, THE System SHALL handle the timeout gracefully
4. THE System SHALL validate all user inputs before processing
5. WHEN processing is in progress, THE System SHALL display loading indicators to users

### Requirement 7: Cost-Effective Operation

**User Story:** As a system operator, I want to minimize operational costs, so that the system remains economically viable.

#### Acceptance Criteria

1. THE System SHALL use only Google Gemini 1.5 Flash free tier for AI processing
2. THE System SHALL NOT use additional OCR libraries like Tesseract
3. THE System SHALL rely entirely on Gemini's multimodal capabilities for document processing
4. THE System SHALL optimize API calls to minimize usage within free tier limits
5. THE System SHALL handle rate limiting gracefully if free tier limits are approached

### Requirement 8: PDF Report Generation

**User Story:** As a user, I want to download a comprehensive PDF report of my claim results, so that I can have a professional document for my records and sharing with healthcare providers.

#### Acceptance Criteria

1. WHEN claim processing is complete, THE System SHALL provide a download button for PDF report generation
2. THE System SHALL generate a PDF report containing client basic details extracted from the policy document
3. THE System SHALL include the complete claim results data in tabular format within the PDF
4. THE System SHALL format the PDF report with clear sections for client information and claim details
5. WHEN the PDF download button is clicked, THE System SHALL generate and initiate the PDF file download immediately
6. THE System SHALL include summary metrics (total billed, approved amount, rejected amount) in the PDF report
7. THE System SHALL display all bill items with their coverage status and rejection reasons in a formatted table within the PDF

### Requirement 9: Technical Architecture

**User Story:** As a developer, I want a maintainable technical architecture, so that the system can be easily extended and debugged.

#### Acceptance Criteria

1. THE System SHALL be built using Python 3.10+ as the primary language
2. THE System SHALL use Streamlit for the web interface framework
3. THE System SHALL use the google-generativeai library for AI model integration
4. THE System SHALL use Pandas for data processing and manipulation
5. THE System SHALL maintain clear separation between UI, AI processing, and calculation logic
6. THE System SHALL use a PDF generation library (such as reportlab or fpdf) for creating PDF reports