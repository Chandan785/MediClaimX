"""
Data models for the Medical Claims Processor application.

This module contains the core data structures used throughout the application:
- BillItem: Individual line items from medical bills
- ClaimData: Complete claim information extracted from documents
- CalculationResult: Results of claim processing calculations
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
import json
import pandas as pd


@dataclass
class BillItem:
    """
    Represents an individual line item from a medical bill with enhanced details.
    
    Attributes:
        description: Exact description of the medical service/item from bill
        cost: Total cost of the item in Indian Rupees (must be non-negative)
        is_covered: Whether this item is covered by the insurance policy
        rejection_reason: Reason for rejection if not covered (None if covered)
        date: Service date if available (optional)
        quantity: Quantity of service/item (default 1)
        unit_cost: Unit cost if available (optional)
    """
    description: str
    cost: float
    is_covered: bool
    rejection_reason: Optional[str] = None
    date: Optional[str] = None
    quantity: int = 1
    unit_cost: Optional[float] = None
    
    def __post_init__(self):
        """Validate BillItem data after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate BillItem data integrity.
        
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("Description must be a non-empty string")
        
        if not isinstance(self.cost, (int, float)) or self.cost < 0:
            raise ValueError("Cost must be a non-negative number")
        
        if not isinstance(self.is_covered, bool):
            raise ValueError("is_covered must be a boolean")
        
        if self.rejection_reason is not None and not isinstance(self.rejection_reason, str):
            raise ValueError("rejection_reason must be a string or None")
        
        # Business logic validation
        if self.is_covered and self.rejection_reason is not None:
            raise ValueError("Covered items should not have rejection reasons")
        
        if not self.is_covered and self.rejection_reason is None:
            raise ValueError("Rejected items must have rejection reasons")
        
        # Validate optional fields
        if self.date is not None and not isinstance(self.date, str):
            raise ValueError("date must be a string or None")
        
        if not isinstance(self.quantity, int) or self.quantity < 1:
            raise ValueError("quantity must be a positive integer")
        
        if self.unit_cost is not None and (not isinstance(self.unit_cost, (int, float)) or self.unit_cost < 0):
            raise ValueError("unit_cost must be a non-negative number or None")
        
        # Calculate unit_cost if not provided
        if self.unit_cost is None and self.quantity > 0:
            self.unit_cost = self.cost / self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert BillItem to dictionary format.
        
        Returns:
            Dictionary representation of the BillItem
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BillItem':
        """
        Create BillItem from dictionary data.
        
        Args:
            data: Dictionary containing BillItem data
            
        Returns:
            BillItem instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = {'description', 'cost', 'is_covered'}
        if not all(field in data for field in required_fields):
            raise ValueError(f"Missing required fields. Required: {required_fields}")
        
        return cls(
            description=data['description'],
            cost=float(data['cost']),
            is_covered=bool(data['is_covered']),
            rejection_reason=data.get('rejection_reason'),
            date=data.get('date'),
            quantity=int(data.get('quantity', 1)),
            unit_cost=float(data['unit_cost']) if data.get('unit_cost') is not None else None
        )


@dataclass
class ClaimData:
    """
    Complete claim information extracted from insurance policy and medical bill documents.
    
    Attributes:
        policy_name: Name of the insurance policy
        copay_percentage: Percentage of covered costs that patient must pay (0-100)
        bill_items: List of individual bill items from the medical bill
        client_name: Name of the policyholder (optional)
        policy_number: Policy identification number (optional)
        client_address: Address of the policyholder (optional)
    """
    policy_name: str
    copay_percentage: float
    bill_items: List[BillItem]
    client_name: Optional[str] = None
    policy_number: Optional[str] = None
    client_address: Optional[str] = None
    
    def __post_init__(self):
        """Validate ClaimData after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate ClaimData integrity.
        
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(self.policy_name, str) or not self.policy_name.strip():
            raise ValueError("Policy name must be a non-empty string")
        
        if not isinstance(self.copay_percentage, (int, float)) or not (0 <= self.copay_percentage <= 100):
            raise ValueError("Copay percentage must be a number between 0 and 100")
        
        if not isinstance(self.bill_items, list):
            raise ValueError("bill_items must be a list")
        
        if not self.bill_items:
            raise ValueError("bill_items cannot be empty")
        
        # Validate optional client fields
        if self.client_name is not None and (not isinstance(self.client_name, str) or not self.client_name.strip()):
            raise ValueError("client_name must be a non-empty string or None")
        
        if self.policy_number is not None and (not isinstance(self.policy_number, str) or not self.policy_number.strip()):
            raise ValueError("policy_number must be a non-empty string or None")
        
        if self.client_address is not None and (not isinstance(self.client_address, str) or not self.client_address.strip()):
            raise ValueError("client_address must be a non-empty string or None")
        
        # Validate each bill item
        for i, item in enumerate(self.bill_items):
            if not isinstance(item, BillItem):
                raise ValueError(f"bill_items[{i}] must be a BillItem instance")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert ClaimData to dictionary format.
        
        Returns:
            Dictionary representation of the ClaimData
        """
        return {
            'policy_name': self.policy_name,
            'copay_percentage': self.copay_percentage,
            'bill_items': [item.to_dict() for item in self.bill_items],
            'client_name': self.client_name,
            'policy_number': self.policy_number,
            'client_address': self.client_address
        }
    
    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> 'ClaimData':
        """
        Create ClaimData from JSON dictionary data.
        
        Args:
            json_data: Dictionary containing ClaimData in JSON format
            
        Returns:
            ClaimData instance
            
        Raises:
            ValueError: If required fields are missing or invalid
        """
        required_fields = {'policy_name', 'copay_percentage', 'bill_items'}
        if not all(field in json_data for field in required_fields):
            raise ValueError(f"Missing required fields. Required: {required_fields}")
        
        # Convert bill_items from dict format to BillItem objects
        bill_items = []
        for i, item_data in enumerate(json_data['bill_items']):
            try:
                bill_items.append(BillItem.from_dict(item_data))
            except ValueError as e:
                raise ValueError(f"Invalid bill_items[{i}]: {e}")
        
        return cls(
            policy_name=json_data['policy_name'],
            copay_percentage=float(json_data.get('copay_percentage', 0.0)),  # Default to 0 if not specified
            bill_items=bill_items,
            client_name=json_data.get('client_name'),
            policy_number=json_data.get('policy_number'),
            client_address=json_data.get('client_address')
        )
    
    def get_total_billed(self) -> float:
        """
        Calculate total amount billed across all items.
        
        Returns:
            Total billed amount
        """
        return sum(item.cost for item in self.bill_items)
    
    def get_covered_items(self) -> List[BillItem]:
        """
        Get list of covered bill items.
        
        Returns:
            List of BillItem objects that are covered
        """
        return [item for item in self.bill_items if item.is_covered]
    
    def get_rejected_items(self) -> List[BillItem]:
        """
        Get list of rejected bill items.
        
        Returns:
            List of BillItem objects that are not covered
        """
        return [item for item in self.bill_items if not item.is_covered]


@dataclass
class CalculationResult:
    """
    Results of claim processing calculations.
    
    Attributes:
        total_billed: Total amount billed across all items
        total_covered: Total amount for covered items before copay
        total_rejected: Total amount for rejected items
        copay_percentage: Copay percentage applied
        approved_amount: Final approved amount after copay
        patient_responsibility: Amount patient must pay (copay portion)
        bill_items_df: Pandas DataFrame containing all bill items for display
    """
    total_billed: float
    total_covered: float
    total_rejected: float
    copay_percentage: float
    approved_amount: float
    patient_responsibility: float
    bill_items_df: pd.DataFrame
    
    def __post_init__(self):
        """Validate CalculationResult after initialization."""
        self._validate()
    
    def _validate(self) -> None:
        """
        Validate CalculationResult data integrity.
        
        Raises:
            ValueError: If validation fails
        """
        # Validate numeric fields are non-negative
        numeric_fields = [
            'total_billed', 'total_covered', 'total_rejected', 
            'approved_amount', 'patient_responsibility'
        ]
        
        for field in numeric_fields:
            value = getattr(self, field)
            if not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"{field} must be a non-negative number")
        
        if not isinstance(self.copay_percentage, (int, float)) or not (0 <= self.copay_percentage <= 100):
            raise ValueError("copay_percentage must be between 0 and 100")
        
        if not isinstance(self.bill_items_df, pd.DataFrame):
            raise ValueError("bill_items_df must be a pandas DataFrame")
        
        # Validate mathematical relationships
        if abs(self.total_billed - (self.total_covered + self.total_rejected)) > 0.01:
            raise ValueError("total_billed must equal total_covered + total_rejected")
        
        expected_patient_responsibility = self.total_covered * (self.copay_percentage / 100)
        if abs(self.patient_responsibility - expected_patient_responsibility) > 0.01:
            raise ValueError("patient_responsibility must equal total_covered * copay_percentage")
        
        expected_approved_amount = self.total_covered - self.patient_responsibility
        if abs(self.approved_amount - expected_approved_amount) > 0.01:
            raise ValueError("approved_amount must equal total_covered - patient_responsibility")
    
    def to_csv(self) -> str:
        """
        Convert calculation results to CSV format.
        
        Returns:
            CSV string representation of the results
        """
        # Create a copy of the DataFrame to avoid modifying the original
        df_copy = self.bill_items_df.copy()
        
        # Add summary information as additional rows
        summary_data = {
            'description': ['SUMMARY - Total Billed', 'SUMMARY - Total Covered', 
                          'SUMMARY - Total Rejected', 'SUMMARY - Approved Amount',
                          'SUMMARY - Patient Responsibility'],
            'cost': [self.total_billed, self.total_covered, self.total_rejected,
                    self.approved_amount, self.patient_responsibility],
            'is_covered': [None, None, None, None, None],
            'rejection_reason': [None, None, None, None, None]
        }
        
        summary_df = pd.DataFrame(summary_data)
        combined_df = pd.concat([df_copy, summary_df], ignore_index=True)
        
        return combined_df.to_csv(index=False)
    
    def get_summary_metrics(self) -> Dict[str, float]:
        """
        Get summary metrics as a dictionary.
        
        Returns:
            Dictionary containing key financial metrics
        """
        return {
            'total_billed': self.total_billed,
            'total_covered': self.total_covered,
            'total_rejected': self.total_rejected,
            'approved_amount': self.approved_amount,
            'patient_responsibility': self.patient_responsibility,
            'copay_percentage': self.copay_percentage
        }
    
    @classmethod
    def from_claim_data(cls, claim_data: ClaimData) -> 'CalculationResult':
        """
        Create CalculationResult by calculating from ClaimData.
        
        Args:
            claim_data: ClaimData to process
            
        Returns:
            CalculationResult with calculated values
        """
        # Calculate totals
        total_billed = claim_data.get_total_billed()
        covered_items = claim_data.get_covered_items()
        rejected_items = claim_data.get_rejected_items()
        
        total_covered = sum(item.cost for item in covered_items)
        total_rejected = sum(item.cost for item in rejected_items)
        
        # Apply copay only if specified in policy
        if claim_data.copay_percentage > 0:
            patient_responsibility = total_covered * (claim_data.copay_percentage / 100)
            approved_amount = total_covered - patient_responsibility
        else:
            # No copay - full reimbursement for covered items
            patient_responsibility = 0.0
            approved_amount = total_covered
        
        # Create DataFrame for display
        bill_items_data = []
        for item in claim_data.bill_items:
            bill_items_data.append({
                'description': item.description,
                'cost': item.cost,
                'is_covered': item.is_covered,
                'rejection_reason': item.rejection_reason
            })
        
        bill_items_df = pd.DataFrame(bill_items_data)
        
        return cls(
            total_billed=total_billed,
            total_covered=total_covered,
            total_rejected=total_rejected,
            copay_percentage=claim_data.copay_percentage,
            approved_amount=approved_amount,
            patient_responsibility=patient_responsibility,
            bill_items_df=bill_items_df
        )