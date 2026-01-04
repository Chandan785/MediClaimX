"""
PDF Report Generator for Medical Claims Processor

This module generates professional PDF reports containing client details and claim results.
Uses reportlab library for PDF creation with proper formatting and styling.
"""

from typing import Optional, Dict, Any
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import black, white, red, green, blue, grey
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

from .models import ClaimData, CalculationResult


class PDFReportGenerator:
    """
    Generates professional PDF reports for medical claims processing results.
    
    This class creates formatted PDF documents containing:
    - Client information extracted from policy documents
    - Comprehensive claim results in tabular format
    - Summary metrics and financial breakdowns
    - Professional styling and formatting
    """
    
    def __init__(self):
        """Initialize the PDF report generator with default settings."""
        # Page settings
        self.page_size = A4
        self.margin = 0.75 * inch
        
        # Get standard styles
        self.styles = getSampleStyleSheet()
        
        # Create custom styles
        self._create_custom_styles()
        
        # Colors for styling
        self.colors = {
            'primary': blue,
            'success': green,
            'danger': red,
            'secondary': grey,
            'text': black,
            'background': white
        }
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the PDF report."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=blue
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            spaceBefore=20,
            textColor=blue
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=16,
            textColor=black
        ))
        
        # Body text with emphasis
        self.styles.add(ParagraphStyle(
            name='BodyEmphasis',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=black
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=grey
        ))
    
    def generate_report(self, claim_data: ClaimData, calculation_result: CalculationResult) -> bytes:
        """
        Generate a complete PDF report for the medical claim.
        
        Args:
            claim_data: ClaimData containing policy and client information
            calculation_result: CalculationResult containing calculated values
            
        Returns:
            PDF file content as bytes
            
        Raises:
            ValueError: If required data is missing or invalid
            RuntimeError: If PDF generation fails
        """
        try:
            # Validate input data
            self._validate_input_data(claim_data, calculation_result)
            
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=self.page_size,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin,
                title="Medical Claim Report"
            )
            
            # Build document content
            story = []
            
            # Add header section
            self._create_header_section(story, claim_data)
            
            # Add client information section
            self._create_client_section(story, claim_data)
            
            # Add summary section
            self._create_summary_section(story, calculation_result)
            
            # Add detailed results table
            self._create_details_table(story, claim_data, calculation_result)
            
            # Add footer
            self._create_footer_section(story)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            else:
                raise RuntimeError(f"PDF generation failed: {str(e)}")
    
    def _validate_input_data(self, claim_data: ClaimData, calculation_result: CalculationResult):
        """
        Validate input data for PDF generation.
        
        Args:
            claim_data: ClaimData to validate
            calculation_result: CalculationResult to validate
            
        Raises:
            ValueError: If data is invalid or missing required fields
        """
        if not isinstance(claim_data, ClaimData):
            raise ValueError("claim_data must be a ClaimData instance")
        
        if not isinstance(calculation_result, CalculationResult):
            raise ValueError("calculation_result must be a CalculationResult instance")
        
        # Validate essential data exists
        if not claim_data.policy_name:
            raise ValueError("Policy name is required for PDF generation")
        
        if not claim_data.bill_items:
            raise ValueError("Bill items are required for PDF generation")
        
        # Validate calculation result has required data
        if calculation_result.bill_items_df.empty:
            raise ValueError("Bill items DataFrame is required for PDF generation")
    
    def _create_header_section(self, story: list, claim_data: ClaimData):
        """
        Create the header section of the PDF report.
        
        Args:
            story: List to append PDF elements to
            claim_data: ClaimData containing policy information
        """
        # Main title
        title = Paragraph("Medical Claim Report", self.styles['CustomTitle'])
        story.append(title)
        
        # Report generation date
        current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        date_text = f"Generated on {current_date}"
        date_para = Paragraph(date_text, self.styles['Footer'])
        story.append(date_para)
        story.append(Spacer(1, 20))
        
        # Policy information header
        policy_header = Paragraph("Policy Information", self.styles['SectionHeader'])
        story.append(policy_header)
        
        # Policy details table
        policy_data = [
            ['Policy Name:', claim_data.policy_name],
            ['Copay Percentage:', f"{claim_data.copay_percentage}%"]
        ]
        
        policy_table = Table(policy_data, colWidths=[2*inch, 4*inch])
        policy_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(policy_table)
        story.append(Spacer(1, 20))
    
    def _create_client_section(self, story: list, claim_data: ClaimData):
        """
        Create the client information section of the PDF report.
        
        Args:
            story: List to append PDF elements to
            claim_data: ClaimData containing client information
        """
        # Only create client section if we have client data
        if not any([claim_data.client_name, claim_data.policy_number, claim_data.client_address]):
            return
        
        # Client information header
        client_header = Paragraph("Client Information", self.styles['SectionHeader'])
        story.append(client_header)
        
        # Build client data table
        client_data = []
        
        if claim_data.client_name:
            client_data.append(['Client Name:', claim_data.client_name])
        
        if claim_data.policy_number:
            client_data.append(['Policy Number:', claim_data.policy_number])
        
        if claim_data.client_address:
            client_data.append(['Address:', claim_data.client_address])
        
        if client_data:
            client_table = Table(client_data, colWidths=[2*inch, 4*inch])
            client_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(client_table)
            story.append(Spacer(1, 20))
    
    def _create_summary_section(self, story: list, calculation_result: CalculationResult):
        """
        Create the financial summary section of the PDF report.
        
        Args:
            story: List to append PDF elements to
            calculation_result: CalculationResult containing summary metrics
        """
        # Summary header
        summary_header = Paragraph("Financial Summary", self.styles['SectionHeader'])
        story.append(summary_header)
        
        # Summary metrics table
        summary_data = [
            ['Metric', 'Amount (₹)'],
            ['Total Billed', self._format_currency(calculation_result.total_billed)],
            ['Total Covered', self._format_currency(calculation_result.total_covered)],
            ['Total Rejected', self._format_currency(calculation_result.total_rejected)],
            ['Patient Responsibility (Copay)', self._format_currency(calculation_result.patient_responsibility)],
            ['Approved Amount', self._format_currency(calculation_result.approved_amount)]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            
            # Alternating row colors
            ('BACKGROUND', (0, 1), (-1, 1), white),
            ('BACKGROUND', (0, 2), (-1, 2), grey),
            ('BACKGROUND', (0, 3), (-1, 3), white),
            ('BACKGROUND', (0, 4), (-1, 4), grey),
            ('BACKGROUND', (0, 5), (-1, 5), white),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, black),
            
            # Padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            
            # Highlight approved amount
            ('BACKGROUND', (0, 5), (-1, 5), green),
            ('TEXTCOLOR', (0, 5), (-1, 5), white),
            ('FONTNAME', (0, 5), (-1, 5), 'Helvetica-Bold'),
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
    
    def _create_details_table(self, story: list, claim_data: ClaimData, calculation_result: CalculationResult):
        """
        Create the detailed bill items table section of the PDF report.
        
        Args:
            story: List to append PDF elements to
            claim_data: ClaimData containing bill items
            calculation_result: CalculationResult containing calculated values
        """
        # Details header
        details_header = Paragraph("Detailed Bill Items", self.styles['SectionHeader'])
        story.append(details_header)
        
        # Table headers
        headers = ['Description', 'Amount (₹)', 'Status', 'Patient Pays (₹)', 'Insurance Pays (₹)', 'Rejection Reason']
        
        # Build table data
        table_data = [headers]
        
        for item in claim_data.bill_items:
            # Calculate individual amounts
            if item.is_covered:
                patient_pays = item.cost * (claim_data.copay_percentage / 100)
                insurance_pays = item.cost - patient_pays
                status = "✓ Covered"
                rejection_reason = "N/A"
            else:
                patient_pays = 0.0
                insurance_pays = 0.0
                status = "✗ Rejected"
                rejection_reason = item.rejection_reason or "Not specified"
            
            row = [
                item.description,
                self._format_currency(item.cost),
                status,
                self._format_currency(patient_pays) if patient_pays > 0 else "-",
                self._format_currency(insurance_pays) if insurance_pays > 0 else "-",
                rejection_reason
            ]
            table_data.append(row)
        
        # Create table with appropriate column widths
        col_widths = [2.5*inch, 1*inch, 0.8*inch, 1*inch, 1*inch, 1.7*inch]
        details_table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Apply table styling
        table_style = [
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Description
            ('ALIGN', (1, 1), (4, -1), 'RIGHT'), # Amount columns
            ('ALIGN', (5, 1), (5, -1), 'LEFT'),  # Rejection reason
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, black),
            
            # Padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            
            # Vertical alignment
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]
        
        # Add row-specific styling for covered/rejected items
        for i, item in enumerate(claim_data.bill_items, 1):  # Start from 1 to skip header
            if item.is_covered:
                # Green background for covered items
                table_style.extend([
                    ('BACKGROUND', (0, i), (-1, i), green),
                    ('TEXTCOLOR', (0, i), (-1, i), white),
                ])
            else:
                # Red background for rejected items
                table_style.extend([
                    ('BACKGROUND', (0, i), (-1, i), red),
                    ('TEXTCOLOR', (0, i), (-1, i), white),
                ])
        
        details_table.setStyle(TableStyle(table_style))
        story.append(details_table)
        story.append(Spacer(1, 20))
    
    def _create_footer_section(self, story: list):
        """
        Create the footer section of the PDF report.
        
        Args:
            story: List to append PDF elements to
        """
        # Add some space before footer
        story.append(Spacer(1, 30))
        
        # Footer text
        footer_text = "This report was generated by the Medical Claims Processor system. " \
                     "Please verify all information and consult with your insurance provider for final confirmation."
        
        footer_para = Paragraph(footer_text, self.styles['Footer'])
        story.append(footer_para)
        
        # Generation timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_text = f"Report generated on: {timestamp}"
        timestamp_para = Paragraph(timestamp_text, self.styles['Footer'])
        story.append(timestamp_para)
    
    def _format_currency(self, amount: float) -> str:
        """
        Format currency amount for display in PDF.
        
        Args:
            amount: Amount to format
            
        Returns:
            Formatted currency string
        """
        if amount == 0:
            return "₹0.00"
        
        # Format with Indian Rupee symbol and comma separators
        return f"₹{amount:,.2f}"
    
    def get_report_filename(self, claim_data: ClaimData) -> str:
        """
        Generate a descriptive filename for the PDF report.
        
        Args:
            claim_data: ClaimData containing client information
            
        Returns:
            Suggested filename for the PDF report
        """
        # Base filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Include client name if available
        if claim_data.client_name:
            # Clean client name for filename (remove special characters)
            clean_name = "".join(c for c in claim_data.client_name if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_name = clean_name.replace(' ', '_')
            filename = f"medical_claim_report_{clean_name}_{timestamp}.pdf"
        else:
            filename = f"medical_claim_report_{timestamp}.pdf"
        
        return filename