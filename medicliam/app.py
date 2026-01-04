"""
Medical Claims Processor - Streamlit Application
Automates medical reimbursement claim verification using AI-powered document analysis.
"""

import streamlit as st
import pandas as pd
import datetime
import time
import io
from typing import Optional, List, Dict, Any
from src.validation import InputValidator
from src.gemini_processor import GeminiProcessor
from src.enhanced_gemini_processor import EnhancedGeminiProcessor
from src.coverage_engine import enhance_claim_with_coverage_analysis
from src.calculator import ClaimCalculator
from src.models import ClaimData, CalculationResult
from src.pdf_generator import PDFReportGenerator
from config import GOOGLE_API_KEY, ADMIN_PASSWORD

def display_results(calculation_result: CalculationResult, claim_data: ClaimData):
    """
    Display comprehensive claim processing results with summary metrics,
    detailed table, and visual distinctions for approved/rejected items.
    
    Args:
        calculation_result: CalculationResult containing all calculated values
        claim_data: ClaimData containing processed claim information
    """
    st.markdown("---")
    st.subheader("📊 Claim Processing Results")
    
    # Summary Metrics Display
    st.subheader("💰 Financial Summary")
    
    # Create three columns for main financial metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Billed",
            value=f"₹{calculation_result.total_billed:,.2f}",
            help="Total amount across all bill items"
        )
        
    with col2:
        st.metric(
            label="Approved Amount",
            value=f"₹{calculation_result.approved_amount:,.2f}",
            delta=f"₹{calculation_result.approved_amount - calculation_result.total_billed:,.2f}",
            delta_color="normal",
            help="Amount approved for reimbursement after copay"
        )
        
    with col3:
        st.metric(
            label="Rejected Amount",
            value=f"₹{calculation_result.total_rejected:,.2f}",
            delta=f"-₹{calculation_result.total_rejected:,.2f}" if calculation_result.total_rejected > 0 else None,
            delta_color="inverse",
            help="Total amount for items not covered by policy"
        )
    
    # Additional metrics in a second row
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric(
            label="Total Covered",
            value=f"₹{calculation_result.total_covered:,.2f}",
            help="Total amount for covered items before copay"
        )
        
    with col5:
        st.metric(
            label="Patient Responsibility",
            value=f"₹{calculation_result.patient_responsibility:,.2f}",
            help=f"Your copay portion ({calculation_result.copay_percentage}%)"
        )
        
    with col6:
        coverage_percentage = (calculation_result.total_covered / calculation_result.total_billed * 100) if calculation_result.total_billed > 0 else 0
        st.metric(
            label="Coverage Rate",
            value=f"{coverage_percentage:.1f}%",
            help="Percentage of total bill that is covered"
        )
    
    # Policy Information
    st.subheader("📋 Policy Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Policy:** {claim_data.policy_name}")
        
    with col2:
        st.info(f"**Copay Rate:** {claim_data.copay_percentage}%")
    
    # Detailed Results Table
    st.subheader("📄 Detailed Bill Items")
    
    # Create enhanced DataFrame for display
    display_data = []
    for item in claim_data.bill_items:
        # Calculate individual item impact
        item_status = "✅ Covered" if item.is_covered else "❌ Rejected"
        
        display_data.append({
            'Description': item.description,
            'Amount': item.cost,
            'Status': item_status,
            'Rejection Reason': item.rejection_reason if not item.is_covered else "N/A",
            'Patient Pays': item.cost * (claim_data.copay_percentage / 100) if item.is_covered else 0.0,
            'Insurance Pays': item.cost * (1 - claim_data.copay_percentage / 100) if item.is_covered else 0.0
        })
    
    results_df = pd.DataFrame(display_data)
    
    # Format currency columns
    results_df['Amount_Formatted'] = results_df['Amount'].apply(lambda x: f"₹{x:,.2f}")
    results_df['Patient_Pays_Formatted'] = results_df['Patient Pays'].apply(lambda x: f"₹{x:,.2f}" if x > 0 else "-")
    results_df['Insurance_Pays_Formatted'] = results_df['Insurance Pays'].apply(lambda x: f"₹{x:,.2f}" if x > 0 else "-")
    
    # Create display DataFrame with formatted columns
    display_df = pd.DataFrame({
        'Description': results_df['Description'],
        'Amount': results_df['Amount_Formatted'],
        'Status': results_df['Status'],
        'Patient Pays': results_df['Patient_Pays_Formatted'],
        'Insurance Pays': results_df['Insurance_Pays_Formatted'],
        'Rejection Reason': results_df['Rejection Reason']
    })
    
    # Apply color coding with enhanced styling
    def style_results_table(row):
        """Apply color coding and styling to results table rows."""
        if "❌ Rejected" in str(row['Status']):
            # Red background for rejected items
            return [
                'background-color: #ffebee; color: #c62828; font-weight: bold',  # Description
                'background-color: #ffebee; color: #c62828; font-weight: bold',  # Amount
                'background-color: #ffebee; color: #c62828; font-weight: bold',  # Status
                'background-color: #ffebee; color: #666666',                     # Patient Pays
                'background-color: #ffebee; color: #666666',                     # Insurance Pays
                'background-color: #ffebee; color: #c62828; font-style: italic' # Rejection Reason
            ]
        else:
            # Green background for approved items
            return [
                'background-color: #e8f5e8; color: #2e7d32; font-weight: bold',  # Description
                'background-color: #e8f5e8; color: #2e7d32; font-weight: bold',  # Amount
                'background-color: #e8f5e8; color: #2e7d32; font-weight: bold',  # Status
                'background-color: #e8f5e8; color: #1976d2; font-weight: bold',  # Patient Pays
                'background-color: #e8f5e8; color: #1976d2; font-weight: bold',  # Insurance Pays
                'background-color: #e8f5e8; color: #666666'                      # Rejection Reason
            ]
    
    # Apply styling and display
    styled_df = display_df.style.apply(style_results_table, axis=1)
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Description': st.column_config.TextColumn(
                'Item Description',
                help='Description of the medical service or item',
                width='large'
            ),
            'Amount': st.column_config.TextColumn(
                'Billed Amount',
                help='Amount billed for this item in Indian Rupees (₹)'
            ),
            'Status': st.column_config.TextColumn(
                'Coverage Status',
                help='Whether this item is covered by your policy'
            ),
            'Patient Pays': st.column_config.TextColumn(
                'Your Cost',
                help='Amount you pay for this item in Rupees (copay portion)'
            ),
            'Insurance Pays': st.column_config.TextColumn(
                'Insurance Pays',
                help='Amount insurance covers for this item in Rupees'
            ),
            'Rejection Reason': st.column_config.TextColumn(
                'Rejection Reason',
                help='Reason why item was not covered (if applicable)',
                width='medium'
            )
        }
    )
    
    # Summary Statistics
    st.subheader("📈 Coverage Analysis")
    
    covered_items = len([item for item in claim_data.bill_items if item.is_covered])
    rejected_items = len([item for item in claim_data.bill_items if not item.is_covered])
    total_items = len(claim_data.bill_items)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Total Items",
            value=str(total_items),
            help="Total number of items on the bill"
        )
        
    with col2:
        st.metric(
            label="Covered Items",
            value=str(covered_items),
            delta=f"{(covered_items/total_items*100):.1f}%" if total_items > 0 else "0%",
            delta_color="normal",
            help="Number of items covered by your policy"
        )
        
    with col3:
        st.metric(
            label="Rejected Items",
            value=str(rejected_items),
            delta=f"{(rejected_items/total_items*100):.1f}%" if total_items > 0 else "0%",
            delta_color="inverse",
            help="Number of items not covered by your policy"
        )
    
    # Visual distinction for rejected items summary
    if rejected_items > 0:
        st.subheader("⚠️ Rejected Items Summary")
        
        rejected_item_list = [item for item in claim_data.bill_items if not item.is_covered]
        
        for item in rejected_item_list:
            with st.expander(f"❌ {item.description} - ₹{item.cost:,.2f}", expanded=False):
                st.error(f"**Rejection Reason:** {item.rejection_reason}")
                st.info(f"**Amount:** ₹{item.cost:,.2f}")
    
    # Action items and next steps
    st.subheader("🎯 Next Steps")
    
    if calculation_result.approved_amount > 0:
        st.success(f"✅ **Approved for Reimbursement:** ₹{calculation_result.approved_amount:,.2f}")
        
    if calculation_result.patient_responsibility > 0:
        st.info(f"💳 **Your Responsibility:** ₹{calculation_result.patient_responsibility:,.2f} (copay)")
        
    if rejected_items > 0:
        st.warning(f"⚠️ **Review Required:** {rejected_items} item(s) were rejected. Check rejection reasons above.")
    
    st.info("📋 **Next:** Admin review and approval required before downloading final reports")

def display_enhanced_analysis(enhanced_result):
    """
    Display comprehensive enhanced analysis results.
    
    Args:
        enhanced_result: EnhancedCalculationResult with detailed analysis
    """
    st.markdown("---")
    st.subheader("📊 Comprehensive Analysis")
    
    # Category Breakdown
    if enhanced_result.category_breakdown:
        st.subheader("🏥 Service Category Breakdown")
        
        # Create category summary table
        category_data = []
        for category, data in enhanced_result.category_breakdown.items():
            category_data.append({
                'Category': category.title().replace('_', ' '),
                'Items': data['count'],
                'Total Billed': f"₹{data['billed']:,.2f}",
                'Covered': f"₹{data['covered']:,.2f}",
                'Rejected': f"₹{data['rejected']:,.2f}",
                'Avg Cost': f"₹{data['average_cost']:,.2f}",
                'Coverage Rate': f"{data['coverage_rate']:.1f}%"
            })
        
        category_df = pd.DataFrame(category_data)
        
        # Display with color coding
        def style_category_table(row):
            coverage_rate = float(row['Coverage Rate'].replace('%', ''))
            if coverage_rate >= 80:
                return ['background-color: #e8f5e8'] * len(row)  # Green for high coverage
            elif coverage_rate >= 50:
                return ['background-color: #fff3cd'] * len(row)  # Yellow for medium coverage
            else:
                return ['background-color: #f8d7da'] * len(row)  # Red for low coverage
        
        styled_category_df = category_df.style.apply(style_category_table, axis=1)
        
        st.dataframe(
            styled_category_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Category insights
        with st.expander("📈 Category Insights", expanded=False):
            highest_cost_category = max(enhanced_result.category_breakdown.items(), 
                                      key=lambda x: x[1]['billed'])
            lowest_coverage_category = min(enhanced_result.category_breakdown.items(), 
                                         key=lambda x: x[1]['coverage_rate'])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    "Highest Cost Category",
                    highest_cost_category[0].title(),
                    f"₹{highest_cost_category[1]['billed']:,.2f}"
                )
            
            with col2:
                st.metric(
                    "Lowest Coverage Category",
                    lowest_coverage_category[0].title(),
                    f"{lowest_coverage_category[1]['coverage_rate']:.1f}%"
                )
    
    # Detailed Analysis
    if enhanced_result.detailed_analysis:
        st.subheader("🔍 Detailed Analysis")
        
        analysis = enhanced_result.detailed_analysis
        
        # Cost Statistics
        if 'cost_statistics' in analysis:
            st.markdown("**💰 Cost Analysis**")
            cost_stats = analysis['cost_statistics']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Average Item Cost", f"₹{cost_stats.get('average_item_cost', 0):,.2f}")
            
            with col2:
                st.metric("Median Item Cost", f"₹{cost_stats.get('median_item_cost', 0):,.2f}")
            
            with col3:
                st.metric("Highest Item Cost", f"₹{cost_stats.get('highest_cost_item', 0):,.2f}")
            
            with col4:
                st.metric("Lowest Item Cost", f"₹{cost_stats.get('lowest_cost_item', 0):,.2f}")
        
        # Coverage Analysis
        if 'coverage_analysis' in analysis:
            st.markdown("**📋 Coverage Analysis**")
            coverage_stats = analysis['coverage_analysis']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Coverage Rate", f"{coverage_stats.get('coverage_rate', 0):.1f}%")
            
            with col2:
                st.metric("Rejection Rate", f"{coverage_stats.get('rejection_rate', 0):.1f}%")
            
            with col3:
                st.metric("Avg Covered Cost", f"₹{coverage_stats.get('average_covered_cost', 0):,.2f}")
            
            with col4:
                st.metric("Avg Rejected Cost", f"₹{coverage_stats.get('average_rejected_cost', 0):,.2f}")
        
        # Policy Utilization
        if 'policy_utilization' in analysis:
            st.markdown("**📊 Policy Utilization**")
            policy_stats = analysis['policy_utilization']
            
            col1, col2 = st.columns(2)
            
            with col1:
                annual_usage = policy_stats.get('annual_limit_usage', 0)
                st.metric(
                    "Annual Limit Usage",
                    f"{annual_usage:.1f}%",
                    delta=f"{'High' if annual_usage > 80 else 'Normal'} utilization"
                )
            
            with col2:
                room_compliance = policy_stats.get('room_charges_within_limit', True)
                st.metric(
                    "Room Limit Compliance",
                    "✅ Compliant" if room_compliance else "❌ Exceeded",
                    delta="Within limits" if room_compliance else "Review required"
                )
        
        # Risk Factors
        if 'risk_factors' in analysis and analysis['risk_factors']:
            st.markdown("**⚠️ Risk Factors Identified**")
            for risk in analysis['risk_factors']:
                st.warning(f"🚨 {risk}")
        
        # Recommendations
        if 'recommendations' in analysis and analysis['recommendations']:
            st.markdown("**💡 Recommendations**")
            for recommendation in analysis['recommendations']:
                st.info(f"💡 {recommendation}")
        
        # Processing Metadata
        if 'processing_metadata' in analysis:
            with st.expander("📋 Processing Details", expanded=False):
                metadata = analysis['processing_metadata']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Total Categories:** {metadata.get('total_categories', 0)}")
                    st.write(f"**Service Duration:** {metadata.get('date_range', {}).get('duration_days', 0)} days")
                
                with col2:
                    hospital_info = metadata.get('hospital_info', {})
                    if hospital_info.get('name'):
                        st.write(f"**Hospital:** {hospital_info['name']}")
                    if hospital_info.get('bill_number'):
                        st.write(f"**Bill Number:** {hospital_info['bill_number']}")
    
    # Advanced Insights
    st.subheader("🎯 Key Insights")
    
    insights = []
    
    # Coverage insights
    total_items = enhanced_result.coverage_summary.get('Total Items', 0)
    covered_items = enhanced_result.coverage_summary.get('Covered Items', 0)
    coverage_rate = (covered_items / total_items * 100) if total_items > 0 else 0
    
    if coverage_rate >= 90:
        insights.append("✅ Excellent coverage rate - most items are covered by your policy")
    elif coverage_rate >= 70:
        insights.append("⚠️ Good coverage rate - some items may need review")
    else:
        insights.append("🚨 Low coverage rate - consider reviewing policy terms or claim details")
    
    # Cost insights
    if enhanced_result.total_billed > 100000:  # ₹1 lakh
        insights.append("💰 High-value claim - ensure all documentation is complete")
    
    # Category insights
    if enhanced_result.category_breakdown:
        admin_charges = enhanced_result.category_breakdown.get('administrative', {}).get('billed', 0)
        if admin_charges > enhanced_result.total_billed * 0.1:  # More than 10%
            insights.append("📋 High administrative charges detected - review for optimization")
    
    for insight in insights:
        st.info(insight)

def admin_review_interface(claim_data: ClaimData, calculation_result: CalculationResult):
    """
    Admin interface for reviewing and editing extracted claim data.
    
    Args:
        claim_data: ClaimData containing processed claim information
        calculation_result: CalculationResult containing calculated values
    """
    st.markdown("---")
    st.subheader("🔧 Admin Review & Edit")
    
    # Admin authentication
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.info("🔐 **Admin Access Required** - Enter password to review and edit claim data")
        
        with st.form("admin_login"):
            password = st.text_input("Admin Password", type="password")
            login_button = st.form_submit_button("🔓 Access Admin Panel")
            
            if login_button:
                if password == ADMIN_PASSWORD:
                    st.session_state.admin_authenticated = True
                    st.success("✅ Admin access granted!")
                    st.rerun()
                else:
                    st.error("❌ Invalid password")
        return
    
    # Admin panel header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.success("🔓 **Admin Panel Active** - You can now review and edit the extracted data")
    with col2:
        if st.button("🔒 Logout", type="secondary"):
            st.session_state.admin_authenticated = False
            st.rerun()
    
    st.markdown("---")
    
    # Policy Information Editing
    st.subheader("📋 Policy Information")
    
    with st.form("policy_edit"):
        col1, col2 = st.columns(2)
        
        with col1:
            edited_policy_name = st.text_input(
                "Policy Name",
                value=claim_data.policy_name,
                help="Edit the insurance policy name if incorrectly extracted"
            )
            
            edited_copay = st.number_input(
                "Copay Percentage (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(claim_data.copay_percentage),
                step=0.1,
                help="Edit the copay percentage if incorrectly extracted"
            )
        
        with col2:
            edited_client_name = st.text_input(
                "Client Name",
                value=claim_data.client_name or "",
                help="Edit client name if incorrectly extracted"
            )
            
            edited_policy_number = st.text_input(
                "Policy Number",
                value=claim_data.policy_number or "",
                help="Edit policy number if incorrectly extracted"
            )
        
        edited_client_address = st.text_area(
            "Client Address",
            value=claim_data.client_address or "",
            height=100,
            help="Edit client address if incorrectly extracted"
        )
        
        policy_update_button = st.form_submit_button("💾 Update Policy Information", type="primary")
        
        if policy_update_button:
            # Update claim data
            claim_data.policy_name = edited_policy_name
            claim_data.copay_percentage = edited_copay
            claim_data.client_name = edited_client_name if edited_client_name else None
            claim_data.policy_number = edited_policy_number if edited_policy_number else None
            claim_data.client_address = edited_client_address if edited_client_address else None
            
            # Recalculate with new copay percentage
            calculator = ClaimCalculator()
            updated_calculation = calculator.calculate_reimbursement(claim_data)
            
            # Update session state
            st.session_state.claim_data = claim_data
            st.session_state.calculation_result = updated_calculation
            
            st.success("✅ Policy information updated successfully!")
            st.rerun()
    
    # Bill Items Editing
    st.subheader("🧾 Bill Items Review & Edit")
    st.info("💡 **Tip:** Review each item carefully. You can edit descriptions, costs, and coverage decisions.")
    
    # Create editable bill items
    edited_items = []
    items_to_remove = []
    
    for i, item in enumerate(claim_data.bill_items):
        with st.expander(f"📄 Item {i+1}: {item.description[:50]}{'...' if len(item.description) > 50 else ''}", expanded=False):
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                edited_description = st.text_input(
                    "Description",
                    value=item.description,
                    key=f"desc_{i}",
                    help="Edit the service/item description"
                )
            
            with col2:
                edited_cost = st.number_input(
                    "Cost (₹)",
                    min_value=0.0,
                    value=float(item.cost),
                    step=0.01,
                    key=f"cost_{i}",
                    help="Edit the cost amount"
                )
            
            with col3:
                edited_is_covered = st.selectbox(
                    "Coverage Status",
                    options=[True, False],
                    index=0 if item.is_covered else 1,
                    format_func=lambda x: "✅ Covered" if x else "❌ Not Covered",
                    key=f"covered_{i}",
                    help="Change coverage decision"
                )
            
            # Rejection reason (only show if not covered)
            if not edited_is_covered:
                edited_rejection_reason = st.text_area(
                    "Rejection Reason",
                    value=item.rejection_reason or "",
                    key=f"rejection_{i}",
                    height=80,
                    help="Provide reason for rejection"
                )
            else:
                edited_rejection_reason = None
            
            # Action buttons
            col_update, col_remove = st.columns(2)
            
            with col_update:
                if st.button(f"💾 Update Item {i+1}", key=f"update_{i}", type="secondary"):
                    # Validate edited data
                    if not edited_description.strip():
                        st.error("Description cannot be empty")
                        continue
                    
                    if edited_cost <= 0:
                        st.error("Cost must be greater than 0")
                        continue
                    
                    if not edited_is_covered and (not edited_rejection_reason or not edited_rejection_reason.strip()):
                        st.error("Rejection reason is required for non-covered items")
                        continue
                    
                    # Update the item
                    item.description = edited_description
                    item.cost = edited_cost
                    item.is_covered = edited_is_covered
                    item.rejection_reason = edited_rejection_reason
                    
                    st.success(f"✅ Item {i+1} updated!")
                    
                    # Recalculate and update session state
                    calculator = ClaimCalculator()
                    updated_calculation = calculator.calculate_reimbursement(claim_data)
                    st.session_state.calculation_result = updated_calculation
                    
                    st.rerun()
            
            with col_remove:
                if st.button(f"🗑️ Remove Item {i+1}", key=f"remove_{i}", type="secondary"):
                    items_to_remove.append(i)
    
    # Remove items if requested
    if items_to_remove:
        for index in sorted(items_to_remove, reverse=True):
            claim_data.bill_items.pop(index)
        
        # Recalculate after removal
        calculator = ClaimCalculator()
        updated_calculation = calculator.calculate_reimbursement(claim_data)
        st.session_state.claim_data = claim_data
        st.session_state.calculation_result = updated_calculation
        
        st.success(f"✅ Removed {len(items_to_remove)} item(s)")
        st.rerun()
    
    # Add new item
    st.subheader("➕ Add New Bill Item")
    
    with st.form("add_new_item"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_description = st.text_input("Description", help="Enter description for new item")
            new_cost = st.number_input("Cost (₹)", min_value=0.01, step=0.01, help="Enter cost for new item")
        
        with col2:
            new_is_covered = st.selectbox(
                "Coverage Status",
                options=[True, False],
                format_func=lambda x: "✅ Covered" if x else "❌ Not Covered",
                help="Select coverage status"
            )
        
        new_rejection_reason = st.text_area(
            "Rejection Reason (if not covered)",
            help="Required if item is not covered",
            disabled=new_is_covered
        )
        
        add_item_button = st.form_submit_button("➕ Add Item", type="primary")
        
        if add_item_button:
            # Validate new item
            if not new_description.strip():
                st.error("Description is required")
            elif new_cost <= 0:
                st.error("Cost must be greater than 0")
            elif not new_is_covered and (not new_rejection_reason or not new_rejection_reason.strip()):
                st.error("Rejection reason is required for non-covered items")
            else:
                # Add new item
                from src.models import BillItem
                new_item = BillItem(
                    description=new_description,
                    cost=new_cost,
                    is_covered=new_is_covered,
                    rejection_reason=new_rejection_reason if not new_is_covered else None
                )
                
                claim_data.bill_items.append(new_item)
                
                # Recalculate
                calculator = ClaimCalculator()
                updated_calculation = calculator.calculate_reimbursement(claim_data)
                st.session_state.claim_data = claim_data
                st.session_state.calculation_result = updated_calculation
                
                st.success("✅ New item added successfully!")
                st.rerun()
    
    # Bulk operations
    st.subheader("🔄 Bulk Operations")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✅ Mark All as Covered", type="secondary"):
            for item in claim_data.bill_items:
                item.is_covered = True
                item.rejection_reason = None
            
            calculator = ClaimCalculator()
            updated_calculation = calculator.calculate_reimbursement(claim_data)
            st.session_state.calculation_result = updated_calculation
            
            st.success("✅ All items marked as covered!")
            st.rerun()
    
    with col2:
        if st.button("❌ Mark All as Not Covered", type="secondary"):
            default_reason = "Requires manual review"
            for item in claim_data.bill_items:
                item.is_covered = False
                item.rejection_reason = default_reason
            
            calculator = ClaimCalculator()
            updated_calculation = calculator.calculate_reimbursement(claim_data)
            st.session_state.calculation_result = updated_calculation
            
            st.success("✅ All items marked as not covered!")
            st.rerun()
    
    with col3:
        if st.button("🔄 Recalculate All", type="primary"):
            calculator = ClaimCalculator()
            updated_calculation = calculator.calculate_reimbursement(claim_data)
            st.session_state.calculation_result = updated_calculation
            
            st.success("✅ Calculations updated!")
            st.rerun()
    
    # Summary of changes
    st.subheader("📊 Current Summary")
    current_calculation = st.session_state.calculation_result
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items", len(claim_data.bill_items))
    
    with col2:
        covered_count = sum(1 for item in claim_data.bill_items if item.is_covered)
        st.metric("Covered Items", covered_count)
    
    with col3:
        st.metric("Total Billed", f"₹{current_calculation.total_billed:,.2f}")
    
    with col4:
        st.metric("Approved Amount", f"₹{current_calculation.approved_amount:,.2f}")
    
    # Final approval
    st.markdown("---")
    st.subheader("✅ Final Approval")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Approve & Finalize", type="primary", use_container_width=True):
            st.session_state.admin_approved = True
            st.success("✅ **Claim data approved!** You can now download the final reports.")
            st.balloons()
    
    with col2:
        if st.button("🔄 Reset to Original", type="secondary", use_container_width=True):
            if 'original_claim_data' in st.session_state:
                st.session_state.claim_data = st.session_state.original_claim_data
                calculator = ClaimCalculator()
                original_calculation = calculator.calculate_reimbursement(st.session_state.original_claim_data)
                st.session_state.calculation_result = original_calculation
                st.session_state.admin_approved = False
                st.info("🔄 Data reset to original AI extraction")
                st.rerun()
            else:
                st.warning("⚠️ Original data not available")

def main():
    """Main Streamlit application entry point."""
    st.set_page_config(
        page_title="Medical Claims Processor",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize validator
    validator = InputValidator()
    
    # Application header
    st.title("🏥 Medical Claims Processor (India)")
    st.markdown("Automate your medical reimbursement claims with AI-powered document analysis - amounts in Indian Rupees (₹)")
    
    # Free-tier optimization info
    with st.expander("💡 Free-Tier Optimization & Document Quality Tips", expanded=False):
        st.markdown("""
        **To get the best performance with free-tier limits:**
        
        📄 **File Optimization:**
        - Keep files under 20MB for faster processing
        - Use clear, high-contrast images for better AI accuracy
        - Compress large PDFs before uploading
        
        ⚡ **Processing Tips:**
        - Process one claim at a time
        - Wait for completion before starting another
        - Daily limit: 1,500 API requests (resets every 24 hours)
        
        🎯 **Best Results:**
        - Ensure text is clearly readable in documents
        - Use standard medical bill formats when possible
        - Include complete policy information
        
        **📋 Document Quality Guidelines:**
        
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
        - If you get JSON parsing errors, try with clearer document scans
        """)
    
    st.markdown("---")
    
    # Create main layout
    col1, col2 = st.columns(2)
    
    # Initialize session state for file validation
    if 'policy_valid' not in st.session_state:
        st.session_state.policy_valid = False
    if 'bill_valid' not in st.session_state:
        st.session_state.bill_valid = False
    
    with col1:
        st.subheader("📄 Insurance Policy")
        st.caption("💡 **Free-tier tip:** Keep files under 20MB for faster processing")
        policy_file = st.file_uploader(
            "Upload your insurance policy document",
            type=['pdf'],
            key="policy_uploader",
            help="Upload a PDF file containing your insurance policy details (max 20MB for optimal performance)"
        )
        
        # Validate policy file with enhanced error handling
        if policy_file:
            try:
                policy_valid, policy_errors = validator.validate_policy_file(policy_file)
                st.session_state.policy_valid = policy_valid
                
                if policy_valid:
                    validator.display_file_info(policy_file, "policy")
                else:
                    validator.display_validation_errors(policy_errors)
                    
            except Exception as e:
                st.session_state.policy_valid = False
                st.error(f"🚫 Error validating policy file: {str(e)}")
                st.info("💡 Please try re-uploading your file")
        else:
            st.session_state.policy_valid = False
    
    with col2:
        st.subheader("🧾 Medical Bill")
        st.caption("💡 **Free-tier tip:** Use clear, high-contrast images for better AI processing")
        bill_file = st.file_uploader(
            "Upload your medical bill",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            key="bill_uploader",
            help="Upload a PDF or image file of your medical bill (max 20MB for optimal performance)"
        )
        
        # Validate bill file with enhanced error handling
        if bill_file:
            try:
                bill_valid, bill_errors = validator.validate_bill_file(bill_file)
                st.session_state.bill_valid = bill_valid
                
                if bill_valid:
                    validator.display_file_info(bill_file, "bill")
                else:
                    validator.display_validation_errors(bill_errors)
                    
            except Exception as e:
                st.session_state.bill_valid = False
                st.error(f"🚫 Error validating bill file: {str(e)}")
                st.info("💡 Please try re-uploading your file")
        else:
            st.session_state.bill_valid = False
    
    # Process button
    st.markdown("---")
    
    # Show file validation summary
    if policy_file or bill_file:
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.session_state.policy_valid:
                st.success("✅ Policy Valid")
            elif policy_file:
                st.error("❌ Policy Invalid")
            else:
                st.warning("⏳ Policy Missing")
        
        with col2:
            if st.session_state.bill_valid:
                st.success("✅ Bill Valid")
            elif bill_file:
                st.error("❌ Bill Invalid")
            else:
                st.warning("⏳ Bill Missing")
        
        with col3:
            files_ready = st.session_state.policy_valid and st.session_state.bill_valid
            if files_ready:
                st.success("🎉 Ready to process!")
            else:
                st.info("📋 Upload and validate both files to continue")
    
    # Process button with enhanced validation
    process_button_disabled = not (st.session_state.policy_valid and st.session_state.bill_valid)
    
    # Processing options
    if st.session_state.policy_valid and st.session_state.bill_valid:
        st.subheader("⚙️ Processing Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_enhanced_processing = st.checkbox(
                "🧠 **Enhanced Coverage Analysis**",
                value=True,
                help="Use intelligent coverage determination to identify which items are covered vs rejected based on policy rules"
            )
        
        with col2:
            if use_enhanced_processing:
                st.success("✅ **Smart Coverage**: AI will analyze policy rules and determine coverage for each item")
            else:
                st.info("ℹ️ **Basic Processing**: Standard extraction without coverage analysis")
    
    if st.button("🔍 Process Claim", type="primary", use_container_width=True, disabled=process_button_disabled):
        if st.session_state.policy_valid and st.session_state.bill_valid:
            # Create progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Step 1: Initialize processor
                status_text.text("🔧 Initializing AI processor...")
                progress_bar.progress(10)
                
                processor = GeminiProcessor(GOOGLE_API_KEY)
                
                # Step 2: Test API connection
                status_text.text("🔗 Testing API connection...")
                progress_bar.progress(20)
                
                api_success, api_message = processor.test_api_connection()
                if not api_success:
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Enhanced error display for API issues
                    st.error(f"❌ **API Connection Failed**")
                    st.error(f"**Details:** {api_message}")
                    
                    # Provide specific guidance based on error type
                    if "Invalid API key" in api_message or "permissions" in api_message:
                        st.info("💡 **How to fix:**")
                        st.markdown("""
                        1. Check that your Google API key is correctly set in `app.py`
                        2. Ensure your API key has Gemini API access enabled
                        3. Verify your Google Cloud project has the Generative AI API enabled
                        4. Make sure your API key hasn't expired
                        """)
                    elif "quota exceeded" in api_message.lower():
                        st.info("💡 **How to fix:**")
                        st.markdown("""
                        1. Wait for your quota to reset (usually daily)
                        2. Consider upgrading to a paid Google Cloud plan
                        3. Check your API usage in the Google Cloud Console
                        """)
                    elif "unavailable" in api_message.lower():
                        st.info("💡 **How to fix:**")
                        st.markdown("""
                        1. Wait a few minutes and try again
                        2. Check Google Cloud Status page for service issues
                        3. Verify your internet connection
                        """)
                    else:
                        st.info("💡 **General troubleshooting:**")
                        st.markdown("""
                        1. Check your internet connection
                        2. Verify your API key is correct
                        3. Try again in a few minutes
                        """)
                    return
                
                # Step 3: Prepare files
                status_text.text("📄 Preparing documents for processing...")
                progress_bar.progress(40)
                
                # Additional file validation before processing
                try:
                    # Reset file pointers to ensure clean reads
                    policy_file.seek(0)
                    bill_file.seek(0)
                    
                    # Validate files can be read
                    policy_size = len(policy_file.read())
                    policy_file.seek(0)
                    bill_size = len(bill_file.read())
                    bill_file.seek(0)
                    
                    if policy_size == 0:
                        raise ValueError("Policy file appears to be empty")
                    if bill_size == 0:
                        raise ValueError("Bill file appears to be empty")
                        
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ **File Reading Error:** {str(e)}")
                    st.info("💡 Please try re-uploading your files")
                    return
                
                # Step 4: Process documents with AI
                if use_enhanced_processing:
                    status_text.text("🧠 Processing with Enhanced Coverage Analysis (this may take 60-90 seconds)...")
                    progress_bar.progress(60)
                    
                    try:
                        # Use enhanced processor
                        enhanced_processor = EnhancedGeminiProcessor(GOOGLE_API_KEY)
                        claim_data = enhanced_processor.process_documents_with_coverage_analysis(policy_file, bill_file)
                    except Exception as e:
                        st.warning(f"⚠️ **Enhanced processing failed**: {str(e)}")
                        st.info("🔄 **Falling back to basic processing**...")
                        
                        # Fallback to basic processing
                        processor = GeminiProcessor(GOOGLE_API_KEY)
                        claim_data = processor.process_documents(policy_file, bill_file)
                        
                        # Apply coverage analysis to basic extraction
                        status_text.text("⚖️ Applying coverage analysis to extracted data...")
                        claim_data, coverage_summary = enhance_claim_with_coverage_analysis(claim_data)
                        
                        # Display coverage summary
                        st.info(f"📊 **Coverage Analysis**: {coverage_summary['covered_items']}/{coverage_summary['total_items']} items covered ({coverage_summary['coverage_rate']:.1f}%)")
                else:
                    status_text.text("🤖 Extracting data with AI (this may take 30-60 seconds)...")
                    progress_bar.progress(60)
                    
                    claim_data = processor.process_documents(policy_file, bill_file)
                
                # Step 5: Validate extracted data
                status_text.text("✅ Validating extracted data...")
                progress_bar.progress(70)
                
                # Additional validation of extracted data
                if not claim_data.bill_items:
                    st.warning("⚠️ **No bill items found**")
                    st.info("The AI couldn't extract any line items from your bill. This might happen if:")
                    st.markdown("""
                    - The bill image/PDF is unclear or low quality
                    - The bill format is unusual or non-standard
                    - The document doesn't contain itemized charges
                    """)
                    st.info("💡 Try uploading a clearer image or a different format of your bill")
                    progress_bar.empty()
                    status_text.empty()
                    return
                
                # Step 6: Calculate reimbursement amounts
                status_text.text("🧮 Calculating reimbursement amounts...")
                progress_bar.progress(85)
                
                try:
                    # Try enhanced calculation first
                    try:
                        from src.enhanced_models import EnhancedClaimData
                        from src.enhanced_calculator import EnhancedClaimCalculator
                        
                        # Check if we have enhanced data
                        if hasattr(claim_data, 'policy_analysis'):
                            # We have enhanced data, use enhanced calculator
                            enhanced_calculator = EnhancedClaimCalculator()
                            enhanced_result = enhanced_calculator.calculate_comprehensive_reimbursement(claim_data)
                            
                            # Convert to legacy format for UI compatibility
                            calculation_result = CalculationResult(
                                total_billed=enhanced_result.total_billed,
                                total_covered=enhanced_result.total_covered,
                                total_rejected=enhanced_result.total_rejected,
                                copay_percentage=enhanced_result.copay_percentage,
                                approved_amount=enhanced_result.approved_amount,
                                patient_responsibility=enhanced_result.patient_responsibility,
                                bill_items_df=pd.DataFrame([{
                                    'description': item.description,
                                    'cost': item.cost,
                                    'is_covered': item.is_covered,
                                    'rejection_reason': item.rejection_reason
                                } for item in claim_data.bill_items])
                            )
                            
                            # Store enhanced result for advanced features
                            st.session_state.enhanced_result = enhanced_result
                            
                        else:
                            # Fallback to legacy calculation
                            calculator = ClaimCalculator()
                            calculation_result = calculator.calculate_reimbursement(claim_data)
                            
                    except Exception as enhanced_error:
                        st.warning("⚠️ Using standard calculation due to enhanced processing error")
                        # Fallback to legacy calculation
                        calculator = ClaimCalculator()
                        calculation_result = calculator.calculate_reimbursement(claim_data)
                    
                except ValueError as calc_error:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ **Calculation Error**")
                    st.error(f"**Details:** {str(calc_error)}")
                    st.info("💡 **How to fix:** There was an issue with the extracted data. Please try processing your documents again.")
                    return
                except Exception as calc_error:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ **Unexpected Calculation Error**")
                    st.error(f"**Details:** {str(calc_error)}")
                    st.info("💡 **How to fix:** Please try processing your documents again or contact support.")
                    return
                
                # Step 7: Complete processing
                status_text.text("🎉 Processing completed successfully!")
                progress_bar.progress(100)
                
                # Store results in session state
                st.session_state.claim_data = claim_data
                st.session_state.calculation_result = calculation_result
                st.session_state.show_results = True
                
                # Store original data for reset functionality
                import copy
                st.session_state.original_claim_data = copy.deepcopy(claim_data)
                st.session_state.admin_approved = False
                
                # Clean up progress indicators
                time.sleep(0.5)  # Brief pause to show completion
                progress_bar.empty()
                status_text.empty()
                
                st.success("✅ **Processing completed successfully!**")
                st.rerun()
                
            except ValueError as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ **Validation Error**")
                st.error(f"**Details:** {str(e)}")
                
                # Provide context-specific guidance
                if "empty" in str(e).lower():
                    st.info("💡 **How to fix:** Please ensure your files are not empty and try re-uploading them")
                elif "format" in str(e).lower() or "corrupted" in str(e).lower():
                    st.info("💡 **How to fix:** Please check your file format and ensure the files are not corrupted")
                else:
                    st.info("💡 **How to fix:** Please check your files and try again")
                    
            except RuntimeError as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ **Processing Error**")
                st.error(f"**Details:** {str(e)}")
                
                # Provide context-specific guidance for runtime errors
                if "rate limit" in str(e).lower():
                    st.info("💡 **How to fix:** Please wait a few minutes before trying again")
                elif "timeout" in str(e).lower():
                    st.info("💡 **How to fix:** Try with smaller files or check your internet connection")
                elif "json" in str(e).lower():
                    st.info("💡 **How to fix:** The AI response was malformed. Please try again")
                else:
                    st.info("💡 **How to fix:** Please try again in a few minutes")
                    
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ **Unexpected Error**")
                st.error(f"**Details:** {str(e)}")
                st.info("💡 **How to fix:**")
                st.markdown("""
                1. Check your API key configuration
                2. Ensure your files are valid and not corrupted
                3. Try again in a few minutes
                4. If the problem persists, try with different files
                """)
        else:
            # This shouldn't happen due to button being disabled, but good to have as fallback
            st.error("⚠️ Please upload and validate both policy and medical bill documents before processing")
    
    # Show helpful information when button is disabled
    if process_button_disabled and (policy_file or bill_file):
        if not st.session_state.policy_valid and not st.session_state.bill_valid:
            st.warning("📋 Please upload valid policy and medical bill documents to enable processing")
        elif not st.session_state.policy_valid:
            st.warning("📄 Please upload a valid policy document to enable processing")
        elif not st.session_state.bill_valid:
            st.warning("🧾 Please upload a valid medical bill document to enable processing")
    
    # Results display section
    if st.session_state.get('show_results', False) and st.session_state.get('claim_data') and st.session_state.get('calculation_result'):
        # Display main results
        display_results(st.session_state.calculation_result, st.session_state.claim_data)
        
        # Display enhanced analysis if available
        if st.session_state.get('enhanced_result'):
            display_enhanced_analysis(st.session_state.enhanced_result)
        
        # Admin review interface
        admin_review_interface(st.session_state.claim_data, st.session_state.calculation_result)
        
        # Show download section only if admin approved or no admin review needed
        if st.session_state.get('admin_approved', False):
            st.markdown("---")
            st.success("🎉 **Ready for Download** - Admin has approved the final data")
            
            # Enhanced download section for approved data
            st.subheader("📥 Download Final Reports")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 Final CSV Report**")
                try:
                    csv_data = st.session_state.calculation_result.to_csv()
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv_filename = f"approved_medical_claim_{timestamp}.csv"
                    
                    st.download_button(
                        label="📊 Download Approved CSV",
                        data=csv_data,
                        file_name=csv_filename,
                        mime="text/csv",
                        type="primary",
                        use_container_width=True,
                        help="Download admin-approved CSV report"
                    )
                except Exception as e:
                    st.error(f"CSV generation error: {str(e)}")
            
            with col2:
                st.markdown("**📄 Final PDF Report**")
                try:
                    pdf_generator = PDFReportGenerator()
                    pdf_content = pdf_generator.generate_report(st.session_state.claim_data, st.session_state.calculation_result)
                    pdf_filename = f"approved_{pdf_generator.get_report_filename(st.session_state.claim_data)}"
                    
                    st.download_button(
                        label="📄 Download Approved PDF",
                        data=pdf_content,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        type="primary",
                        use_container_width=True,
                        help="Download admin-approved PDF report"
                    )
                except Exception as e:
                    st.error(f"PDF generation error: {str(e)}")
        else:
            st.info("📋 **Admin Review Required** - Please review and approve the data above before downloading final reports")

if __name__ == "__main__":
    main()