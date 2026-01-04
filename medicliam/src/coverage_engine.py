"""
Intelligent Coverage Determination Engine

This module provides rule-based coverage determination for medical claims
based on policy analysis and medical service categorization.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from .models import BillItem, ClaimData


@dataclass
class CoverageRule:
    """Represents a coverage rule from insurance policy."""
    service_type: str
    keywords: List[str]
    is_covered: bool
    rejection_reason: Optional[str] = None
    requires_preauth: bool = False
    coverage_limit: Optional[float] = None


class CoverageEngine:
    """
    Intelligent coverage determination engine that analyzes medical services
    against insurance policy rules to determine coverage decisions.
    """
    
    def __init__(self):
        """Initialize the coverage engine with default rules."""
        self.coverage_rules = self._load_default_coverage_rules()
        self.service_categories = self._load_service_categories()
    
    def analyze_coverage(self, claim_data: ClaimData, policy_rules: Optional[Dict[str, Any]] = None) -> ClaimData:
        """
        Analyze coverage for all bill items based on policy rules.
        
        Args:
            claim_data: ClaimData with bill items to analyze
            policy_rules: Optional policy rules extracted from document
            
        Returns:
            ClaimData with updated coverage decisions
        """
        # Update rules if policy analysis is available
        if policy_rules:
            self._update_rules_from_policy(policy_rules)
        
        # Analyze each bill item
        updated_items = []
        for item in claim_data.bill_items:
            updated_item = self._determine_item_coverage(item)
            updated_items.append(updated_item)
        
        # Create new ClaimData with updated items
        updated_claim_data = ClaimData(
            policy_name=claim_data.policy_name,
            copay_percentage=claim_data.copay_percentage,
            bill_items=updated_items,
            client_name=claim_data.client_name,
            policy_number=claim_data.policy_number,
            client_address=claim_data.client_address
        )
        
        return updated_claim_data
    
    def _determine_item_coverage(self, item: BillItem) -> BillItem:
        """
        Determine coverage for a single bill item.
        
        Args:
            item: BillItem to analyze
            
        Returns:
            BillItem with updated coverage decision
        """
        description = item.description.lower()
        
        # Step 1: Categorize the service
        category = self._categorize_service(description)
        
        # Step 2: Apply coverage rules
        coverage_decision = self._apply_coverage_rules(description, category)
        
        # Step 3: Check for specific exclusions
        exclusion_check = self._check_exclusions(description)
        
        # Step 4: Make final decision
        if exclusion_check["is_excluded"]:
            is_covered = False
            rejection_reason = exclusion_check["reason"]
        else:
            is_covered = coverage_decision["is_covered"]
            rejection_reason = coverage_decision["rejection_reason"]
        
        # Create updated item
        updated_item = BillItem(
            description=item.description,
            cost=item.cost,
            is_covered=is_covered,
            rejection_reason=rejection_reason,
            date=getattr(item, 'date', None),
            quantity=getattr(item, 'quantity', 1),
            unit_cost=getattr(item, 'unit_cost', item.cost)
        )
        
        return updated_item
    
    def _categorize_service(self, description: str) -> str:
        """
        Categorize medical service based on description.
        
        Args:
            description: Service description
            
        Returns:
            Service category
        """
        description_lower = description.lower()
        
        for category, keywords in self.service_categories.items():
            if any(keyword in description_lower for keyword in keywords):
                return category
        
        return "other"
    
    def _apply_coverage_rules(self, description: str, category: str) -> Dict[str, Any]:
        """
        Apply coverage rules to determine if service is covered.
        
        Args:
            description: Service description
            category: Service category
            
        Returns:
            Dictionary with coverage decision
        """
        # Check category-specific rules
        for rule in self.coverage_rules:
            if rule.service_type == category:
                # Check if any keywords match
                if any(keyword in description for keyword in rule.keywords):
                    return {
                        "is_covered": rule.is_covered,
                        "rejection_reason": rule.rejection_reason,
                        "requires_preauth": rule.requires_preauth
                    }
        
        # Default decision based on category
        return self._get_default_coverage_decision(category)
    
    def _check_exclusions(self, description: str) -> Dict[str, Any]:
        """
        Check for specific exclusions that override coverage decisions.
        
        Args:
            description: Service description
            
        Returns:
            Dictionary with exclusion check results
        """
        exclusion_patterns = [
            # Personal care items
            (r'\b(soap|shampoo|toothbrush|toothpaste|comb|mirror)\b', 
             "Personal care item - not medical necessity"),
            
            # Cosmetic items
            (r'\b(cosmetic|beauty|aesthetic|plastic surgery)\b', 
             "Cosmetic procedure - excluded by policy"),
            
            # Non-medical supplies
            (r'\b(newspaper|magazine|tv|entertainment|phone|wifi)\b', 
             "Non-medical service - not covered"),
            
            # Food and beverages (unless medical nutrition)
            (r'\b(tea|coffee|juice|snacks|meals)\b(?!.*medical|therapeutic)', 
             "Food/beverage - not medical necessity"),
            
            # Experimental treatments
            (r'\b(experimental|investigational|trial|research)\b', 
             "Experimental treatment - excluded by policy"),
        ]
        
        description_lower = description.lower()
        
        for pattern, reason in exclusion_patterns:
            if re.search(pattern, description_lower):
                return {
                    "is_excluded": True,
                    "reason": reason
                }
        
        return {"is_excluded": False, "reason": None}
    
    def _get_default_coverage_decision(self, category: str) -> Dict[str, Any]:
        """
        Get default coverage decision for a service category.
        
        Args:
            category: Service category
            
        Returns:
            Default coverage decision
        """
        # Generally covered categories
        covered_categories = [
            "medication", "medical_supply", "diagnostic_test", 
            "procedure", "consultation", "emergency"
        ]
        
        # Generally not covered categories
        not_covered_categories = [
            "personal_care", "cosmetic", "non_medical", "comfort"
        ]
        
        if category in covered_categories:
            return {
                "is_covered": True,
                "rejection_reason": None,
                "requires_preauth": False
            }
        elif category in not_covered_categories:
            return {
                "is_covered": False,
                "rejection_reason": f"{category.replace('_', ' ').title()} - not covered by policy",
                "requires_preauth": False
            }
        else:
            # Unknown category - default to manual review
            return {
                "is_covered": False,
                "rejection_reason": "Service requires manual review for coverage determination",
                "requires_preauth": False
            }
    
    def _load_default_coverage_rules(self) -> List[CoverageRule]:
        """Load default coverage rules."""
        return [
            # Medications - Generally Covered
            CoverageRule(
                service_type="medication",
                keywords=["tablet", "injection", "syrup", "capsule", "mg", "ml"],
                is_covered=True
            ),
            
            # Medical Supplies - Generally Covered
            CoverageRule(
                service_type="medical_supply",
                keywords=["syringe", "needle", "gauze", "bandage", "catheter", "tube"],
                is_covered=True
            ),
            
            # Diagnostic Tests - Generally Covered
            CoverageRule(
                service_type="diagnostic_test",
                keywords=["test", "scan", "x-ray", "mri", "ct", "ultrasound", "blood", "urine"],
                is_covered=True
            ),
            
            # Procedures - Generally Covered
            CoverageRule(
                service_type="procedure",
                keywords=["surgery", "operation", "procedure", "treatment"],
                is_covered=True
            ),
            
            # Room Charges - Generally Covered
            CoverageRule(
                service_type="room_charges",
                keywords=["room", "bed", "accommodation", "stay"],
                is_covered=True
            ),
            
            # Personal Care - Generally Not Covered
            CoverageRule(
                service_type="personal_care",
                keywords=["soap", "shampoo", "toothbrush", "comb", "towel"],
                is_covered=False,
                rejection_reason="Personal care item - not medical necessity"
            ),
            
            # Comfort Items - Generally Not Covered
            CoverageRule(
                service_type="comfort",
                keywords=["tv", "phone", "newspaper", "magazine", "entertainment"],
                is_covered=False,
                rejection_reason="Comfort/entertainment item - not covered by policy"
            ),
        ]
    
    def _load_service_categories(self) -> Dict[str, List[str]]:
        """Load service category keywords."""
        return {
            "medication": [
                "tablet", "tab", "injection", "inj", "syrup", "capsule", "cap",
                "mg", "ml", "drug", "medicine", "pharmaceutical", "antibiotic",
                "painkiller", "analgesic", "antacid", "vitamin"
            ],
            
            "medical_supply": [
                "syringe", "needle", "gauze", "bandage", "cotton", "swab",
                "catheter", "tube", "bag", "container", "gloves", "mask",
                "dressing", "pad", "tape", "suture"
            ],
            
            "diagnostic_test": [
                "test", "scan", "x-ray", "mri", "ct", "ultrasound", "echo",
                "blood", "urine", "stool", "culture", "biopsy", "pathology",
                "lab", "laboratory", "analysis", "screening"
            ],
            
            "procedure": [
                "surgery", "operation", "procedure", "treatment", "therapy",
                "intervention", "repair", "removal", "insertion", "biopsy"
            ],
            
            "consultation": [
                "consultation", "visit", "checkup", "examination", "assessment",
                "doctor", "physician", "specialist", "consultant"
            ],
            
            "room_charges": [
                "room", "bed", "accommodation", "stay", "ward", "icu", "ccu",
                "private", "general", "deluxe", "suite"
            ],
            
            "equipment": [
                "monitor", "ventilator", "pump", "machine", "device", "equipment",
                "apparatus", "instrument", "tool"
            ],
            
            "emergency": [
                "emergency", "urgent", "critical", "trauma", "ambulance",
                "er", "casualty", "acute"
            ],
            
            "personal_care": [
                "soap", "shampoo", "toothbrush", "toothpaste", "comb", "brush",
                "towel", "tissue", "napkin", "wipes", "lotion", "cream"
            ],
            
            "comfort": [
                "tv", "television", "phone", "telephone", "newspaper", "magazine",
                "entertainment", "wifi", "internet", "cable", "ac", "air conditioning"
            ],
            
            "food": [
                "food", "meal", "breakfast", "lunch", "dinner", "snack",
                "tea", "coffee", "juice", "water", "beverage", "diet"
            ]
        }
    
    def _update_rules_from_policy(self, policy_rules: Dict[str, Any]):
        """
        Update coverage rules based on policy analysis.
        
        Args:
            policy_rules: Policy rules extracted from document
        """
        # Add covered services from policy
        covered_services = policy_rules.get("covered_services", [])
        for service in covered_services:
            # Check if rule already exists
            existing_rule = next((rule for rule in self.coverage_rules 
                                if rule.service_type == service), None)
            
            if not existing_rule:
                # Add new coverage rule
                self.coverage_rules.append(
                    CoverageRule(
                        service_type=service,
                        keywords=[service.lower()],
                        is_covered=True
                    )
                )
        
        # Add exclusions from policy
        exclusions = policy_rules.get("exclusions", [])
        for exclusion in exclusions:
            # Add exclusion rule
            self.coverage_rules.append(
                CoverageRule(
                    service_type="exclusion",
                    keywords=[exclusion.lower()],
                    is_covered=False,
                    rejection_reason=f"Excluded service: {exclusion}"
                )
            )
    
    def get_coverage_summary(self, claim_data: ClaimData) -> Dict[str, Any]:
        """
        Get coverage analysis summary.
        
        Args:
            claim_data: ClaimData to analyze
            
        Returns:
            Coverage summary statistics
        """
        total_items = len(claim_data.bill_items)
        covered_items = [item for item in claim_data.bill_items if item.is_covered]
        rejected_items = [item for item in claim_data.bill_items if not item.is_covered]
        
        # Calculate amounts
        total_amount = sum(item.cost for item in claim_data.bill_items)
        covered_amount = sum(item.cost for item in covered_items)
        rejected_amount = sum(item.cost for item in rejected_items)
        
        # Categorize rejections
        rejection_reasons = {}
        for item in rejected_items:
            reason = item.rejection_reason or "Unknown reason"
            rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1
        
        return {
            "total_items": total_items,
            "covered_items": len(covered_items),
            "rejected_items": len(rejected_items),
            "coverage_rate": (len(covered_items) / total_items * 100) if total_items > 0 else 0,
            "total_amount": total_amount,
            "covered_amount": covered_amount,
            "rejected_amount": rejected_amount,
            "rejection_reasons": rejection_reasons
        }


def enhance_claim_with_coverage_analysis(claim_data: ClaimData, policy_rules: Optional[Dict[str, Any]] = None) -> Tuple[ClaimData, Dict[str, Any]]:
    """
    Enhance claim data with intelligent coverage analysis.
    
    Args:
        claim_data: Original claim data
        policy_rules: Optional policy rules from document analysis
        
    Returns:
        Tuple of (enhanced_claim_data, coverage_summary)
    """
    engine = CoverageEngine()
    enhanced_claim = engine.analyze_coverage(claim_data, policy_rules)
    summary = engine.get_coverage_summary(enhanced_claim)
    
    return enhanced_claim, summary