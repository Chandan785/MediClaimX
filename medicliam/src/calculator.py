"""
Calculation engine for the Medical Claims Processor application.

This module provides deterministic mathematical calculations for medical claim processing,
using Python and Pandas for all financial computations. No AI is used for calculations.
"""

import pandas as pd
from typing import List

try:
    from .models import ClaimData, BillItem, CalculationResult
except ImportError:
    # For direct execution/testing
    from models import ClaimData, BillItem, CalculationResult


class ClaimCalculator:
    """
    Deterministic calculation engine for medical claim processing.
    
    This class handles all mathematical calculations for claim processing:
    - Summing covered items
    - Applying copay percentages
    - Calculating rejected amounts
    - Generating calculation results
    
    All calculations use Python and Pandas for accuracy and auditability.
    No AI is used for any mathematical computations.
    """
    
    def __init__(self):
        """Initialize the ClaimCalculator."""
        pass
    
    def calculate_reimbursement(self, claim_data: ClaimData) -> CalculationResult:
        """
        Calculate reimbursement amounts from claim data.
        
        Args:
            claim_data: ClaimData containing policy and bill information
            
        Returns:
            CalculationResult with all calculated values
            
        Raises:
            ValueError: If claim_data is invalid or calculations fail
        """
        if not isinstance(claim_data, ClaimData):
            raise ValueError("claim_data must be a ClaimData instance")
        
        try:
            # Convert bill items to DataFrame for Pandas operations
            bill_items_data = []
            for i, item in enumerate(claim_data.bill_items):
                try:
                    bill_items_data.append({
                        'description': item.description,
                        'cost': float(item.cost),  # Ensure numeric type
                        'is_covered': bool(item.is_covered),  # Ensure boolean type
                        'rejection_reason': item.rejection_reason
                    })
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid data in bill item {i}: {str(e)}")
            
            if not bill_items_data:
                raise ValueError("No valid bill items found for calculation")
            
            df = pd.DataFrame(bill_items_data)
            
            # Validate DataFrame integrity
            if df['cost'].isnull().any():
                raise ValueError("Some bill items have missing cost values")
            
            if (df['cost'] < 0).any():
                raise ValueError("Bill items cannot have negative costs")
            
            # Calculate totals using Pandas
            total_billed = self._calculate_total_billed(df)
            total_covered = self._sum_covered_items(df)
            total_rejected = self._calculate_rejected_total(df)
            
            # Validate calculation consistency
            if abs(total_billed - (total_covered + total_rejected)) > 0.01:
                raise ValueError("Calculation error: total billed does not equal covered + rejected amounts")
            
            # Apply copay percentage
            patient_responsibility = self._apply_copay(total_covered, claim_data.copay_percentage)
            approved_amount = total_covered - patient_responsibility
            
            # Ensure non-negative results
            if approved_amount < 0:
                approved_amount = 0.0
            
            # Create result object
            result = CalculationResult(
                total_billed=total_billed,
                total_covered=total_covered,
                total_rejected=total_rejected,
                copay_percentage=claim_data.copay_percentage,
                approved_amount=approved_amount,
                patient_responsibility=patient_responsibility,
                bill_items_df=df
            )
            
            # Final integrity check
            if not self.validate_calculation_integrity(result):
                raise ValueError("Calculation integrity check failed")
            
            return result
            
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            else:
                raise ValueError(f"Calculation failed: {str(e)}")
    
    def _calculate_total_billed(self, bill_items_df: pd.DataFrame) -> float:
        """
        Calculate total amount billed across all items using Pandas.
        
        Args:
            bill_items_df: DataFrame containing bill items
            
        Returns:
            Total billed amount
            
        Raises:
            ValueError: If DataFrame is invalid or contains invalid data
        """
        if bill_items_df.empty:
            return 0.0
        
        try:
            # Ensure cost column exists and is numeric
            if 'cost' not in bill_items_df.columns:
                raise ValueError("DataFrame missing 'cost' column")
            
            # Convert to numeric and handle any conversion errors
            cost_series = pd.to_numeric(bill_items_df['cost'], errors='coerce')
            
            if cost_series.isnull().any():
                raise ValueError("Some cost values could not be converted to numbers")
            
            return float(cost_series.sum())
            
        except Exception as e:
            raise ValueError(f"Error calculating total billed: {str(e)}")
    
    def _sum_covered_items(self, bill_items_df: pd.DataFrame) -> float:
        """
        Sum costs of all covered bill items using Pandas boolean indexing.
        
        Args:
            bill_items_df: DataFrame containing bill items
            
        Returns:
            Total amount for covered items
            
        Raises:
            ValueError: If DataFrame is invalid or contains invalid data
        """
        if bill_items_df.empty:
            return 0.0
        
        try:
            # Ensure required columns exist
            if 'cost' not in bill_items_df.columns or 'is_covered' not in bill_items_df.columns:
                raise ValueError("DataFrame missing required columns")
            
            # Use Pandas boolean indexing to filter covered items
            covered_items = bill_items_df[bill_items_df['is_covered'] == True]
            
            if covered_items.empty:
                return 0.0
            
            # Convert to numeric and sum
            cost_series = pd.to_numeric(covered_items['cost'], errors='coerce')
            
            if cost_series.isnull().any():
                raise ValueError("Some covered item costs could not be converted to numbers")
            
            return float(cost_series.sum())
            
        except Exception as e:
            raise ValueError(f"Error calculating covered items total: {str(e)}")
    
    def _apply_copay(self, covered_total: float, copay_percentage: float) -> float:
        """
        Apply copay percentage to covered amount to determine patient responsibility.
        
        Args:
            covered_total: Total amount for covered items
            copay_percentage: Copay percentage (0-100)
            
        Returns:
            Amount patient must pay (copay portion)
            
        Raises:
            ValueError: If copay_percentage is invalid
        """
        if not isinstance(copay_percentage, (int, float)) or not (0 <= copay_percentage <= 100):
            raise ValueError("copay_percentage must be between 0 and 100")
        
        if covered_total < 0:
            raise ValueError("covered_total must be non-negative")
        
        # Calculate patient responsibility using Pandas Series for precision
        copay_series = pd.Series([covered_total]) * (copay_percentage / 100)
        
        return float(copay_series.iloc[0])
    
    def _calculate_rejected_total(self, bill_items_df: pd.DataFrame) -> float:
        """
        Calculate total amount for rejected items using Pandas boolean indexing.
        
        Args:
            bill_items_df: DataFrame containing bill items
            
        Returns:
            Total amount for rejected items
            
        Raises:
            ValueError: If DataFrame is invalid or contains invalid data
        """
        if bill_items_df.empty:
            return 0.0
        
        try:
            # Ensure required columns exist
            if 'cost' not in bill_items_df.columns or 'is_covered' not in bill_items_df.columns:
                raise ValueError("DataFrame missing required columns")
            
            # Use Pandas boolean indexing to filter rejected items
            rejected_items = bill_items_df[bill_items_df['is_covered'] == False]
            
            if rejected_items.empty:
                return 0.0
            
            # Convert to numeric and sum
            cost_series = pd.to_numeric(rejected_items['cost'], errors='coerce')
            
            if cost_series.isnull().any():
                raise ValueError("Some rejected item costs could not be converted to numbers")
            
            return float(cost_series.sum())
            
        except Exception as e:
            raise ValueError(f"Error calculating rejected items total: {str(e)}")
    
    def get_covered_items_summary(self, claim_data: ClaimData) -> pd.DataFrame:
        """
        Get summary of covered items using Pandas operations.
        
        Args:
            claim_data: ClaimData containing bill information
            
        Returns:
            DataFrame containing only covered items
        """
        if not isinstance(claim_data, ClaimData):
            raise ValueError("claim_data must be a ClaimData instance")
        
        # Convert to DataFrame
        bill_items_data = []
        for item in claim_data.bill_items:
            bill_items_data.append({
                'description': item.description,
                'cost': item.cost,
                'is_covered': item.is_covered,
                'rejection_reason': item.rejection_reason
            })
        
        df = pd.DataFrame(bill_items_data)
        
        # Filter for covered items only
        return df[df['is_covered'] == True].copy()
    
    def get_rejected_items_summary(self, claim_data: ClaimData) -> pd.DataFrame:
        """
        Get summary of rejected items using Pandas operations.
        
        Args:
            claim_data: ClaimData containing bill information
            
        Returns:
            DataFrame containing only rejected items
        """
        if not isinstance(claim_data, ClaimData):
            raise ValueError("claim_data must be a ClaimData instance")
        
        # Convert to DataFrame
        bill_items_data = []
        for item in claim_data.bill_items:
            bill_items_data.append({
                'description': item.description,
                'cost': item.cost,
                'is_covered': item.is_covered,
                'rejection_reason': item.rejection_reason
            })
        
        df = pd.DataFrame(bill_items_data)
        
        # Filter for rejected items only
        return df[df['is_covered'] == False].copy()
    
    def validate_calculation_integrity(self, result: CalculationResult) -> bool:
        """
        Validate that calculation results maintain mathematical integrity.
        
        Args:
            result: CalculationResult to validate
            
        Returns:
            True if calculations are mathematically consistent
        """
        if not isinstance(result, CalculationResult):
            return False
        
        # Check that total_billed equals sum of covered and rejected
        total_check = abs(result.total_billed - (result.total_covered + result.total_rejected)) < 0.01
        
        # Check that approved_amount plus patient_responsibility equals total_covered
        coverage_check = abs((result.approved_amount + result.patient_responsibility) - result.total_covered) < 0.01
        
        # Check that patient_responsibility matches copay calculation
        copay_check = abs(result.patient_responsibility - (result.total_covered * result.copay_percentage / 100)) < 0.01
        
        return total_check and coverage_check and copay_check