"""
Enhanced data models for comprehensive medical claims processing.

This module provides enhanced data structures for detailed document analysis
while maintaining backward compatibility with the existing system.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
import pandas as pd
import io
from .models import ClaimData as LegacyClaimData, BillItem as LegacyBillItem


class PolicyAnalysis(BaseModel):
    """Comprehensive policy analysis data"""
    policy_name: str = Field(..., description="Insurance policy name")
    policy_number: Optional[str] = Field(None, description="Policy number")
    copay_percentage: float = Field(default=0.0, ge=0, le=100, description="Copay percentage (0 if not specified in policy)")
    covered_services: List[str] = Field(default_factory=list, description="List of covered services")
    exclusions: List[str] = Field(default_factory=list, description="List of excluded services")
    coverage_limits: Dict[str, Any] = Field(default_factory=dict, description="Coverage limits and caps")
    pre_auth_required: List[str] = Field(default_factory=list, description="Services requiring pre-authorization")


class ClientDetails(BaseModel):
    """Client information from policy document"""
    name: Optional[str] = Field(None, description="Client name")
    address: Optional[str] = Field(None, description="Client address")
    policy_holder: Optional[str] = Field(None, description="Policy holder name")


class BillAnalysis(BaseModel):
    """Medical bill header information"""
    hospital_name: Optional[str] = Field(None, description="Hospital or clinic name")
    bill_number: Optional[str] = Field(None, description="Bill number")
    admission_date: Optional[str] = Field(None, description="Admission date")
    discharge_date: Optional[str] = Field(None, description="Discharge date")
    total_bill_amount: float = Field(0.0, ge=0, description="Total bill amount")


class EnhancedBillItem(BaseModel):
    """Enhanced bill item with comprehensive details"""
    category: str = Field(..., description="Service category")
    description: str = Field(..., min_length=1, description="Service description")
    date: Optional[str] = Field(None, description="Service date")
    quantity: int = Field(1, ge=1, description="Quantity of service")
    unit_cost: float = Field(..., ge=0, description="Unit cost")
    total_cost: float = Field(..., ge=0, description="Total cost for this item")
    is_covered: bool = Field(..., description="Coverage decision")
    coverage_reason: Optional[str] = Field(None, description="Reason for coverage")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if not covered")
    policy_reference: Optional[str] = Field(None, description="Policy section reference")
    
    @validator('rejection_reason')
    def validate_rejection_reason(cls, v, values):
        """Ensure rejection reason is provided for non-covered items"""
        if not values.get('is_covered') and not v:
            raise ValueError('Rejection reason is required for non-covered items')
        return v
    
    @validator('coverage_reason')
    def validate_coverage_reason(cls, v, values):
        """Ensure coverage reason is provided for covered items"""
        if values.get('is_covered') and not v:
            # Allow empty coverage reason for backward compatibility
            return "Covered by policy"
        return v
    
    @validator('total_cost')
    def validate_total_cost(cls, v, values):
        """Validate total cost calculation"""
        if 'unit_cost' in values and 'quantity' in values:
            expected_total = values['unit_cost'] * values['quantity']
            if abs(v - expected_total) > 0.01:  # Allow for small rounding differences
                # Auto-correct minor calculation errors
                return expected_total
        return v
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy BillItem format"""
        return {
            'description': self.description,
            'cost': self.total_cost,
            'is_covered': self.is_covered,
            'rejection_reason': self.rejection_reason
        }


class EnhancedClaimData(BaseModel):
    """Enhanced comprehensive claim data structure"""
    policy_analysis: PolicyAnalysis = Field(..., description="Policy analysis results")
    client_details: ClientDetails = Field(..., description="Client information")
    bill_analysis: BillAnalysis = Field(..., description="Bill header information")
    bill_items: List[EnhancedBillItem] = Field(..., min_items=1, description="List of bill items")
    
    # Legacy properties for backward compatibility
    @property
    def policy_name(self) -> str:
        return self.policy_analysis.policy_name
    
    @property
    def copay_percentage(self) -> float:
        return self.policy_analysis.copay_percentage
    
    @property
    def client_name(self) -> Optional[str]:
        return self.client_details.name
    
    @property
    def policy_number(self) -> Optional[str]:
        return self.policy_analysis.policy_number
    
    @property
    def client_address(self) -> Optional[str]:
        return self.client_details.address
    
    def to_legacy_format(self) -> LegacyClaimData:
        """Convert to legacy ClaimData format for backward compatibility"""
        from .models import BillItem as LegacyBillItem
        
        legacy_items = []
        for item in self.bill_items:
            legacy_item = LegacyBillItem(
                description=item.description,
                cost=item.total_cost,
                is_covered=item.is_covered,
                rejection_reason=item.rejection_reason
            )
            legacy_items.append(legacy_item)
        
        return LegacyClaimData(
            policy_name=self.policy_name,
            copay_percentage=self.copay_percentage,
            bill_items=legacy_items,
            client_name=self.client_name,
            policy_number=self.policy_number,
            client_address=self.client_address
        )
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> 'EnhancedClaimData':
        """Create EnhancedClaimData from JSON response with format detection"""
        
        # Detect format type
        if 'policy_analysis' in data:
            # New comprehensive format
            return cls(**data)
        else:
            # Old format - convert to new structure
            policy_analysis = PolicyAnalysis(
                policy_name=data.get('policy_name', 'Unknown Policy'),
                policy_number=data.get('policy_number'),
                copay_percentage=data.get('copay_percentage', 0.0),  # Default to 0 if not specified
                covered_services=[],
                exclusions=[],
                coverage_limits={},
                pre_auth_required=[]
            )
            
            client_details = ClientDetails(
                name=data.get('client_name'),
                address=data.get('client_address'),
                policy_holder=data.get('client_name')
            )
            
            bill_analysis = BillAnalysis(
                total_bill_amount=sum(item.get('cost', 0) for item in data.get('bill_items', []))
            )
            
            # Convert old bill items to new format
            bill_items = []
            for item in data.get('bill_items', []):
                bill_item = EnhancedBillItem(
                    category='other',  # Default category for old format
                    description=item.get('description', 'Unknown Service'),
                    quantity=1,
                    unit_cost=item.get('cost', 0),
                    total_cost=item.get('cost', 0),
                    is_covered=item.get('is_covered', False),
                    coverage_reason='Legacy format - covered by policy' if item.get('is_covered') else None,
                    rejection_reason=item.get('rejection_reason'),
                    policy_reference=None
                )
                bill_items.append(bill_item)
            
            return cls(
                policy_analysis=policy_analysis,
                client_details=client_details,
                bill_analysis=bill_analysis,
                bill_items=bill_items
            )


class EnhancedCalculationResult(BaseModel):
    """Enhanced financial calculation results"""
    total_billed: float = Field(..., ge=0, description="Total amount billed")
    total_covered: float = Field(..., ge=0, description="Total amount covered by policy")
    total_rejected: float = Field(..., ge=0, description="Total amount rejected")
    patient_responsibility: float = Field(..., ge=0, description="Patient copay amount")
    approved_amount: float = Field(..., ge=0, description="Final approved reimbursement")
    copay_percentage: float = Field(..., ge=0, le=100, description="Copay percentage applied")
    
    # Enhanced breakdown by category
    category_breakdown: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Breakdown by service category")
    coverage_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of coverage decisions")
    detailed_analysis: Dict[str, Any] = Field(default_factory=dict, description="Detailed analysis results")
    
    def to_csv(self) -> str:
        """Generate comprehensive CSV export"""
        # Create summary data
        summary_data = {
            'Metric': [
                'Total Billed Amount',
                'Total Covered Amount', 
                'Total Rejected Amount',
                'Patient Responsibility (Copay)',
                'Approved Reimbursement',
                'Copay Percentage'
            ],
            'Amount (₹)': [
                f"{self.total_billed:,.2f}",
                f"{self.total_covered:,.2f}",
                f"{self.total_rejected:,.2f}",
                f"{self.patient_responsibility:,.2f}",
                f"{self.approved_amount:,.2f}",
                f"{self.copay_percentage:.1f}%"
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        
        # Create category breakdown if available
        category_data = []
        for category, amounts in self.category_breakdown.items():
            category_data.append({
                'Category': category.title(),
                'Total Billed': f"₹{amounts.get('billed', 0):,.2f}",
                'Covered': f"₹{amounts.get('covered', 0):,.2f}",
                'Rejected': f"₹{amounts.get('rejected', 0):,.2f}",
                'Items Count': amounts.get('count', 0)
            })
        
        category_df = pd.DataFrame(category_data) if category_data else pd.DataFrame()
        
        # Combine into CSV
        output = io.StringIO()
        
        # Write summary
        output.write("FINANCIAL SUMMARY\n")
        summary_df.to_csv(output, index=False)
        output.write("\n")
        
        # Write category breakdown if available
        if not category_df.empty:
            output.write("CATEGORY BREAKDOWN\n")
            category_df.to_csv(output, index=False)
            output.write("\n")
        
        # Write coverage summary
        if self.coverage_summary:
            output.write("COVERAGE SUMMARY\n")
            coverage_data = []
            for status, count in self.coverage_summary.items():
                coverage_data.append({'Status': status, 'Count': count})
            coverage_df = pd.DataFrame(coverage_data)
            coverage_df.to_csv(output, index=False)
        
        return output.getvalue()


def create_enhanced_processor():
    """Factory function to create enhanced processor with backward compatibility"""
    
    class EnhancedProcessor:
        """Wrapper to handle both legacy and enhanced formats"""
        
        @staticmethod
        def process_response(response_data: Dict[str, Any]) -> EnhancedClaimData:
            """Process API response and return enhanced claim data"""
            return EnhancedClaimData.from_json(response_data)
        
        @staticmethod
        def calculate_enhanced_results(claim_data: EnhancedClaimData) -> EnhancedCalculationResult:
            """Calculate enhanced results with category breakdown"""
            
            # Calculate basic totals
            total_billed = sum(item.total_cost for item in claim_data.bill_items)
            covered_items = [item for item in claim_data.bill_items if item.is_covered]
            rejected_items = [item for item in claim_data.bill_items if not item.is_covered]
            
            total_covered = sum(item.total_cost for item in covered_items)
            total_rejected = sum(item.total_cost for item in rejected_items)
            
            # Apply copay
            patient_responsibility = total_covered * (claim_data.copay_percentage / 100)
            approved_amount = total_covered - patient_responsibility
            
            # Calculate category breakdown
            category_breakdown = {}
            for item in claim_data.bill_items:
                category = item.category
                if category not in category_breakdown:
                    category_breakdown[category] = {
                        'billed': 0.0,
                        'covered': 0.0,
                        'rejected': 0.0,
                        'count': 0
                    }
                
                category_breakdown[category]['billed'] += item.total_cost
                category_breakdown[category]['count'] += 1
                
                if item.is_covered:
                    category_breakdown[category]['covered'] += item.total_cost
                else:
                    category_breakdown[category]['rejected'] += item.total_cost
            
            # Coverage summary
            coverage_summary = {
                'Total Items': len(claim_data.bill_items),
                'Covered Items': len(covered_items),
                'Rejected Items': len(rejected_items)
            }
            
            # Detailed analysis
            detailed_analysis = {
                'coverage_rate': (len(covered_items) / len(claim_data.bill_items)) * 100 if claim_data.bill_items else 0,
                'average_item_cost': total_billed / len(claim_data.bill_items) if claim_data.bill_items else 0,
                'highest_cost_item': max((item.total_cost for item in claim_data.bill_items), default=0),
                'policy_utilization': (total_covered / claim_data.policy_analysis.coverage_limits.get('annual_limit', float('inf'))) * 100 if claim_data.policy_analysis.coverage_limits.get('annual_limit') else 0
            }
            
            return EnhancedCalculationResult(
                total_billed=total_billed,
                total_covered=total_covered,
                total_rejected=total_rejected,
                patient_responsibility=patient_responsibility,
                approved_amount=approved_amount,
                copay_percentage=claim_data.copay_percentage,
                category_breakdown=category_breakdown,
                coverage_summary=coverage_summary,
                detailed_analysis=detailed_analysis
            )
    
    return EnhancedProcessor()