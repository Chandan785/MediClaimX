"""
Enhanced Calculator for comprehensive medical claims processing.

This module provides advanced calculation capabilities with detailed analysis
while maintaining backward compatibility with the existing calculator.
"""

from typing import Dict, List, Any, Tuple
from .models import ClaimData, CalculationResult
from .enhanced_models import EnhancedClaimData, EnhancedCalculationResult, EnhancedBillItem
import pandas as pd


class EnhancedClaimCalculator:
    """
    Enhanced calculator with comprehensive analysis capabilities.
    
    Provides detailed financial calculations, category breakdowns,
    and advanced analytics while maintaining backward compatibility.
    """
    
    def __init__(self):
        """Initialize the enhanced calculator."""
        self.category_weights = {
            'consultation': 1.0,
            'diagnostic': 1.0,
            'procedure': 1.0,
            'medication': 1.0,
            'room': 1.0,
            'nursing': 1.0,
            'equipment': 1.0,
            'ambulance': 1.0,
            'doctor_fee': 1.0,
            'laboratory': 1.0,
            'pharmacy': 1.0,
            'administrative': 0.8,  # Lower priority for admin fees
            'other': 1.0
        }
    
    def calculate_comprehensive_reimbursement(self, claim_data: EnhancedClaimData) -> EnhancedCalculationResult:
        """
        Calculate comprehensive reimbursement with detailed analysis.
        
        Args:
            claim_data: Enhanced claim data with detailed information
            
        Returns:
            Enhanced calculation result with category breakdown and analytics
        """
        # Basic calculations
        total_billed = sum(item.total_cost for item in claim_data.bill_items)
        covered_items = [item for item in claim_data.bill_items if item.is_covered]
        rejected_items = [item for item in claim_data.bill_items if not item.is_covered]
        
        total_covered = sum(item.total_cost for item in covered_items)
        total_rejected = sum(item.total_cost for item in rejected_items)
        
        # Apply copay only if specified in policy
        if copay_percentage > 0:
            patient_responsibility = total_covered * (copay_percentage / 100)
            approved_amount = total_covered - patient_responsibility
        else:
            # No copay - full coverage for covered items
            patient_responsibility = 0.0
            approved_amount = total_covered
        
        # Category breakdown analysis
        category_breakdown = self._calculate_category_breakdown(claim_data.bill_items)
        
        # Coverage summary
        coverage_summary = self._calculate_coverage_summary(claim_data.bill_items)
        
        # Detailed analysis
        detailed_analysis = self._perform_detailed_analysis(claim_data)
        
        return EnhancedCalculationResult(
            total_billed=total_billed,
            total_covered=total_covered,
            total_rejected=total_rejected,
            patient_responsibility=patient_responsibility,
            approved_amount=approved_amount,
            copay_percentage=copay_percentage,
            category_breakdown=category_breakdown,
            coverage_summary=coverage_summary,
            detailed_analysis=detailed_analysis
        )
    
    def calculate_reimbursement(self, claim_data: ClaimData) -> CalculationResult:
        """
        Legacy calculation method for backward compatibility.
        
        Args:
            claim_data: Legacy claim data
            
        Returns:
            Legacy calculation result
        """
        # Use existing calculation logic
        total_billed = sum(item.cost for item in claim_data.bill_items)
        covered_items = [item for item in claim_data.bill_items if item.is_covered]
        rejected_items = [item for item in claim_data.bill_items if not item.is_covered]
        
        total_covered = sum(item.cost for item in covered_items)
        total_rejected = sum(item.cost for item in rejected_items)
        
        # Apply copay only if specified
        if claim_data.copay_percentage > 0:
            patient_responsibility = total_covered * (claim_data.copay_percentage / 100)
            approved_amount = total_covered - patient_responsibility
        else:
            # No copay specified - full coverage
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
        
        return CalculationResult(
            total_billed=total_billed,
            total_covered=total_covered,
            total_rejected=total_rejected,
            copay_percentage=claim_data.copay_percentage,
            approved_amount=approved_amount,
            patient_responsibility=patient_responsibility,
            bill_items_df=bill_items_df
        )
    
    def _calculate_category_breakdown(self, bill_items: List[EnhancedBillItem]) -> Dict[str, Dict[str, float]]:
        """Calculate breakdown by service category."""
        category_breakdown = {}
        
        for item in bill_items:
            category = item.category
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'billed': 0.0,
                    'covered': 0.0,
                    'rejected': 0.0,
                    'count': 0,
                    'average_cost': 0.0,
                    'coverage_rate': 0.0
                }
            
            category_breakdown[category]['billed'] += item.total_cost
            category_breakdown[category]['count'] += 1
            
            if item.is_covered:
                category_breakdown[category]['covered'] += item.total_cost
            else:
                category_breakdown[category]['rejected'] += item.total_cost
        
        # Calculate derived metrics
        for category, data in category_breakdown.items():
            if data['count'] > 0:
                data['average_cost'] = data['billed'] / data['count']
                covered_items = sum(1 for item in bill_items 
                                  if item.category == category and item.is_covered)
                data['coverage_rate'] = (covered_items / data['count']) * 100
        
        return category_breakdown
    
    def _calculate_coverage_summary(self, bill_items: List[EnhancedBillItem]) -> Dict[str, int]:
        """Calculate coverage summary statistics."""
        total_items = len(bill_items)
        covered_items = sum(1 for item in bill_items if item.is_covered)
        rejected_items = total_items - covered_items
        
        # Category-wise coverage
        category_coverage = {}
        for item in bill_items:
            category = item.category
            if category not in category_coverage:
                category_coverage[category] = {'total': 0, 'covered': 0}
            
            category_coverage[category]['total'] += 1
            if item.is_covered:
                category_coverage[category]['covered'] += 1
        
        summary = {
            'Total Items': total_items,
            'Covered Items': covered_items,
            'Rejected Items': rejected_items,
            'Coverage Rate (%)': round((covered_items / total_items) * 100, 1) if total_items > 0 else 0
        }
        
        # Add category-wise coverage rates
        for category, data in category_coverage.items():
            rate = (data['covered'] / data['total']) * 100 if data['total'] > 0 else 0
            summary[f'{category.title()} Coverage (%)'] = round(rate, 1)
        
        return summary
    
    def _perform_detailed_analysis(self, claim_data: EnhancedClaimData) -> Dict[str, Any]:
        """Perform detailed analysis of the claim."""
        bill_items = claim_data.bill_items
        
        if not bill_items:
            return {}
        
        # Cost analysis
        costs = [item.total_cost for item in bill_items]
        total_cost = sum(costs)
        
        # Coverage analysis
        covered_items = [item for item in bill_items if item.is_covered]
        rejected_items = [item for item in bill_items if not item.is_covered]
        
        # Policy utilization
        coverage_limits = claim_data.policy_analysis.coverage_limits
        annual_limit = coverage_limits.get('annual_limit', 0)
        room_limit = coverage_limits.get('room_rent_limit', 0)
        
        # Risk factors
        risk_factors = self._identify_risk_factors(claim_data)
        
        # Recommendations
        recommendations = self._generate_recommendations(claim_data)
        
        analysis = {
            'cost_statistics': {
                'average_item_cost': total_cost / len(bill_items),
                'median_item_cost': sorted(costs)[len(costs) // 2],
                'highest_cost_item': max(costs),
                'lowest_cost_item': min(costs),
                'cost_variance': self._calculate_variance(costs)
            },
            'coverage_analysis': {
                'coverage_rate': (len(covered_items) / len(bill_items)) * 100,
                'rejection_rate': (len(rejected_items) / len(bill_items)) * 100,
                'average_covered_cost': sum(item.total_cost for item in covered_items) / len(covered_items) if covered_items else 0,
                'average_rejected_cost': sum(item.total_cost for item in rejected_items) / len(rejected_items) if rejected_items else 0
            },
            'policy_utilization': {
                'annual_limit_usage': (sum(item.total_cost for item in covered_items) / annual_limit * 100) if annual_limit > 0 else 0,
                'room_charges_within_limit': self._check_room_limit_compliance(bill_items, room_limit),
                'pre_auth_compliance': self._check_preauth_compliance(claim_data)
            },
            'risk_factors': risk_factors,
            'recommendations': recommendations,
            'processing_metadata': {
                'total_categories': len(set(item.category for item in bill_items)),
                'date_range': self._calculate_date_range(bill_items),
                'hospital_info': {
                    'name': claim_data.bill_analysis.hospital_name,
                    'bill_number': claim_data.bill_analysis.bill_number
                }
            }
        }
        
        return analysis
    
    def _calculate_variance(self, values: List[float]) -> float:
        """Calculate variance of a list of values."""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance
    
    def _identify_risk_factors(self, claim_data: EnhancedClaimData) -> List[str]:
        """Identify potential risk factors in the claim."""
        risk_factors = []
        
        # High-cost items
        high_cost_threshold = 50000  # ₹50,000
        high_cost_items = [item for item in claim_data.bill_items if item.total_cost > high_cost_threshold]
        if high_cost_items:
            risk_factors.append(f"High-cost items detected: {len(high_cost_items)} items above ₹{high_cost_threshold:,}")
        
        # Multiple rejections
        rejected_items = [item for item in claim_data.bill_items if not item.is_covered]
        if len(rejected_items) > len(claim_data.bill_items) * 0.3:  # More than 30% rejected
            risk_factors.append(f"High rejection rate: {len(rejected_items)} out of {len(claim_data.bill_items)} items rejected")
        
        # Missing pre-authorization
        pre_auth_required = claim_data.policy_analysis.pre_auth_required
        if pre_auth_required:
            for item in claim_data.bill_items:
                if any(service in item.description.lower() for service in pre_auth_required):
                    if 'pre-auth' not in item.coverage_reason.lower() if item.coverage_reason else True:
                        risk_factors.append(f"Potential pre-authorization issue for: {item.description}")
        
        # Unusual patterns
        categories = [item.category for item in claim_data.bill_items]
        if categories.count('administrative') > 5:
            risk_factors.append("High number of administrative charges")
        
        return risk_factors
    
    def _generate_recommendations(self, claim_data: EnhancedClaimData) -> List[str]:
        """Generate recommendations based on claim analysis."""
        recommendations = []
        
        # Coverage optimization
        rejected_items = [item for item in claim_data.bill_items if not item.is_covered]
        if rejected_items:
            recommendations.append("Review rejected items for potential policy coverage gaps")
        
        # Cost optimization
        high_cost_categories = []
        category_breakdown = self._calculate_category_breakdown(claim_data.bill_items)
        for category, data in category_breakdown.items():
            if data['average_cost'] > 10000:  # ₹10,000 average
                high_cost_categories.append(category)
        
        if high_cost_categories:
            recommendations.append(f"Consider cost optimization for: {', '.join(high_cost_categories)}")
        
        # Policy recommendations
        coverage_limits = claim_data.policy_analysis.coverage_limits
        total_covered = sum(item.total_cost for item in claim_data.bill_items if item.is_covered)
        
        if coverage_limits.get('annual_limit'):
            utilization = (total_covered / coverage_limits['annual_limit']) * 100
            if utilization > 80:
                recommendations.append("High policy utilization - consider reviewing annual limits")
        
        return recommendations
    
    def _check_room_limit_compliance(self, bill_items: List[EnhancedBillItem], room_limit: float) -> bool:
        """Check if room charges comply with policy limits."""
        if room_limit <= 0:
            return True
        
        room_items = [item for item in bill_items if 'room' in item.category.lower()]
        for item in room_items:
            daily_cost = item.total_cost / max(item.quantity, 1)
            if daily_cost > room_limit:
                return False
        
        return True
    
    def _check_preauth_compliance(self, claim_data: EnhancedClaimData) -> Dict[str, bool]:
        """Check pre-authorization compliance."""
        pre_auth_required = claim_data.policy_analysis.pre_auth_required
        compliance = {}
        
        for service in pre_auth_required:
            compliance[service] = True  # Assume compliant unless proven otherwise
            
            for item in claim_data.bill_items:
                if service.lower() in item.description.lower():
                    # Check if pre-auth is mentioned in coverage reason
                    if item.coverage_reason and 'pre-auth' not in item.coverage_reason.lower():
                        compliance[service] = False
        
        return compliance
    
    def _calculate_date_range(self, bill_items: List[EnhancedBillItem]) -> Dict[str, str]:
        """Calculate date range of services."""
        dates = [item.date for item in bill_items if item.date]
        
        if not dates:
            return {'start_date': None, 'end_date': None, 'duration_days': 0}
        
        # Simple date range calculation (assuming dates are strings)
        return {
            'start_date': min(dates) if dates else None,
            'end_date': max(dates) if dates else None,
            'duration_days': len(set(dates)) if dates else 0
        }