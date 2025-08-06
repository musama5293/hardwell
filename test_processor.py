#!/usr/bin/env python3
"""
Test script for the document processor.
Demonstrates how to extract tables from PDF files.
"""

from document_processor import DocumentProcessor
from underwriting_analyzer import UnderwritingAnalyzer
from underwriting_output import UnderwritingOutputGenerator
from loan_sizing_engine import LoanSizingEngine, TreasuryTerm
import os
import pandas as pd

def perform_deep_logic_analysis(processed_data, summary):
    """
    Apply deep logic for data consistency and decision-making.
    
    Key logic rules:
    - If T12 is inconsistent, prefer trailing 2-6 months if trending upward
    - If income is erratic, don't switch to T3 just because last month looked good
    - Flag missing or irregular data
    - Highlight CapEx and one-time expenses
    """
    analysis = {
        'consistency_issues': [],
        'trends': [],
        'recommendations': [],
        'flags': []
    }
    
    # Check T12 data consistency
    if 't12' in processed_data and processed_data['t12'].get('tables'):
        t12_df = processed_data['t12']['tables'][0]
        
        # Look for inconsistent monthly data (if available)
        numeric_cols = t12_df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 3:  # Multiple months of data
            # Check for erratic income patterns
            income_variance = t12_df[numeric_cols].var(axis=1).sum()
            if income_variance > 10000:  # High variance threshold
                analysis['consistency_issues'].append(
                    "High variance detected in monthly income - recommend manual review"
                )
                analysis['recommendations'].append(
                    "Consider using trailing 6-month average instead of single month"
                )
        
        # Check for potential CapEx items
        capex_keywords = ['flooring', 'appliance', 'roof', 'hvac', 'plumbing', 'renovation']
        for _, row in t12_df.iterrows():
            row_text = ' '.join(str(cell).lower() for cell in row.values if pd.notna(cell))
            for keyword in capex_keywords:
                if keyword in row_text:
                    analysis['flags'].append(
                        f"Potential CapEx item detected: {keyword} - review for one-time nature"
                    )
                    break
    
    # Check rent roll data quality
    if 'rent_roll' in processed_data and processed_data['rent_roll'].get('tables'):
        rr_df = processed_data['rent_roll']['tables'][0]
        
        # Check for missing square footage
        sqft_cols = [col for col in rr_df.columns if 'sqft' in col.lower() or 'footage' in col.lower()]
        if not sqft_cols:
            analysis['consistency_issues'].append(
                "Square footage data missing - impacts per-unit analysis accuracy"
            )
        
        # Check for missing rent data
        rent_cols = [col for col in rr_df.columns if 'rent' in col.lower()]
        if rent_cols:
            rent_data = pd.to_numeric(rr_df[rent_cols[0]], errors='coerce')
            missing_rents = rent_data.isna().sum()
            if missing_rents > 0:
                analysis['consistency_issues'].append(
                    f"Missing rent data for {missing_rents} units - affects income calculations"
                )
    
    # Analyze NOI trends if available
    noi = summary.get('noi_analysis', {}).get('net_operating_income', 0)
    expense_ratio = summary.get('noi_analysis', {}).get('expense_ratio', 0)
    
    if expense_ratio > 60:
        analysis['trends'].append(
            f"High expense ratio ({expense_ratio:.1f}%) - investigate operating efficiency"
        )
    elif expense_ratio < 25:
        analysis['trends'].append(
            f"Low expense ratio ({expense_ratio:.1f}%) - verify all expenses captured"
        )
    
    # Check for income trending
    current_income = summary.get('income_summary', {}).get('current_monthly_income', 0)
    if current_income > 0:
        # This is a placeholder - in full implementation would compare with historical data
        analysis['trends'].append(
            "Income trending analysis requires historical comparison data"
        )
    
    return analysis

def test_complete_underwriting_workflow():
    """Test the complete workflow: PDF extraction → Underwriting analysis."""
    
    print("🚀 Complete Underwriting Workflow Test")
    print("=" * 60)
    
    # Initialize components
    processor = DocumentProcessor(debug=True)
    analyzer = UnderwritingAnalyzer(debug=True)
    output_generator = UnderwritingOutputGenerator(debug=True)
    loan_engine = LoanSizingEngine(debug=True)
    
    # Set property information
    property_info = {
        'property_name': 'Bolden Heights Apartments',
        'property_address': '3350 Mount Gilead Rd, Atlanta, GA 30311',
        'unit_count': 100,  # You can adjust this based on actual count
        'property_age': 25,  # Estimate - adjust as needed
        'transaction_type': 'refinance',  # or 'acquisition'
        'city': 'Atlanta',
        'state': 'GA'
    }
    
    analyzer.set_property_info(property_info)
    
    # Sample files to process
    sample_files = {
        'rent_roll': "sample_data/RR_3350_Mount_Gilead_Rd_Atlanta_GA_30311.pdf",
        't12': "sample_data/T12_3350_Mount_Gilead_Rd_Atlanta_GA_30311.pdf"
    }
    
    processed_data = {}
    
    # Step 1: Process documents
    print(f"\n📄 STEP 1: Document Processing")
    print("-" * 40)
    
    for doc_type, file_path in sample_files.items():
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
        
        print(f"\n🔍 Processing {doc_type.upper()}: {os.path.basename(file_path)}")
        
        try:
            results = processor.process_document(file_path)
            processed_data[doc_type] = results
            
            print(f"✅ Extracted {len(results['tables'])} tables")
            
            # Save raw extraction results
            saved_files = processor.save_results(results)
            print(f"💾 Saved to: {list(saved_files.values())}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}")
            continue
    
    # Step 2: Apply underwriting analysis
    print(f"\n📊 STEP 2: Underwriting Analysis")
    print("-" * 40)
    
    # Load rent roll data
    if 'rent_roll' in processed_data and processed_data['rent_roll']['tables']:
        print(f"\n🏢 Analyzing Rent Roll...")
        rent_roll_df = processed_data['rent_roll']['tables'][0]  # Use first table
        rent_roll_analysis = analyzer.load_rent_roll(rent_roll_df)
        
        print(f"📋 Rent Roll Analysis Results:")
        if 'rent_analysis' in rent_roll_analysis:
            ra = rent_roll_analysis['rent_analysis']
            print(f"   • Total Units: {ra.get('total_units', 0)}")
            print(f"   • Occupied Units: {ra.get('occupied_units', 0)}")
            print(f"   • Vacant Units: {ra.get('vacant_units', 0)}")
            print(f"   • Monthly Income: ${ra.get('current_monthly_income', 0):,.0f}")
            print(f"   • Annual GPI: ${ra.get('annual_gpi', 0):,.0f}")
        
        # Show unit type analysis
        if 'unit_analysis' in rent_roll_analysis:
            print(f"   📊 Unit Type Analysis:")
            for unit_type, data in rent_roll_analysis['unit_analysis'].items():
                print(f"      {unit_type}: {data.get('unit_count', 0)} units, "
                      f"Avg Rent: ${data.get('avg_rent', 0):.0f}")
        
        # Show flags
        if rent_roll_analysis.get('flags'):
            print(f"   🚩 Flags:")
            for flag in rent_roll_analysis['flags'][:3]:  # Show first 3
                print(f"      • {flag.get('message', 'Unknown flag')}")
    
    # Load T12 data
    if 't12' in processed_data and processed_data['t12']['tables']:
        print(f"\n💰 Analyzing T12 Operating Statement...")
        t12_df = processed_data['t12']['tables'][0]  # Use first table
        t12_analysis = analyzer.load_t12(t12_df)
        
        print(f"💸 T12 Analysis Results:")
        if 'expense_analysis' in t12_analysis:
            exp_analysis = t12_analysis['expense_analysis']
            
            print(f"   📊 Adjusted Expenses:")
            adjusted = exp_analysis.get('adjusted_expenses', {})
            total = exp_analysis.get('total_adjusted_expenses', 0)
            
            key_expenses = ['vacancy', 'property_taxes', 'insurance', 'repairs_maintenance', 'management_fee']
            for expense in key_expenses:
                if expense in adjusted:
                    print(f"      • {expense.replace('_', ' ').title()}: ${adjusted[expense]:,.0f}")
            
            print(f"   💰 Total Adjusted Expenses: ${total:,.0f}")
            
            # Show some key adjustments
            adjustments = exp_analysis.get('adjustments', {})
            if adjustments:
                print(f"   🔧 Key Adjustments:")
                for item, adjustment in list(adjustments.items())[:3]:
                    print(f"      • {item}: {adjustment}")
    
    # Step 3: Generate comprehensive summary
    print(f"\n📈 STEP 3: Underwriting Summary")
    print("-" * 40)
    
    summary = analyzer.generate_underwriting_summary()
    
    # Income Summary
    if 'income_summary' in summary:
        income = summary['income_summary']
        print(f"🏢 Income Summary:")
        print(f"   • Gross Potential Income: ${income.get('gross_potential_income', 0):,.0f}")
        print(f"   • Current Monthly Income: ${income.get('current_monthly_income', 0):,.0f}")
        print(f"   • Occupancy Rate: {income.get('occupancy_rate', 0):.1f}%")
    
    # NOI Analysis
    if 'noi_analysis' in summary:
        noi = summary['noi_analysis']
        print(f"\n💰 NOI Analysis:")
        print(f"   • Gross Potential Income: ${noi.get('gross_potential_income', 0):,.0f}")
        print(f"   • Vacancy Loss: ${noi.get('vacancy_loss', 0):,.0f}")
        print(f"   • Effective Gross Income: ${noi.get('effective_gross_income', 0):,.0f}")
        print(f"   • Total Expenses: ${noi.get('total_expenses', 0):,.0f}")
        print(f"   • Net Operating Income: ${noi.get('net_operating_income', 0):,.0f}")
        print(f"   • Expense Ratio: {noi.get('expense_ratio', 0):.1f}%")
    
    # Flags and Recommendations
    flags = summary.get('flags_and_recommendations', [])
    if flags:
        print(f"\n🚩 Flags & Recommendations ({len(flags)} total):")
        for i, flag in enumerate(flags[:5]):  # Show first 5
            print(f"   {i+1}. {flag.get('message', 'Unknown flag')}")
        if len(flags) > 5:
            print(f"   ... and {len(flags) - 5} more")
    
    # Step 4: Generate Structured Output Package
    print(f"\n📊 STEP 4: Generating Structured Output Package")
    print("-" * 40)
    
    # Load analysis data into output generator
    output_generator.load_analysis_data(
        rent_roll_analysis=processed_data.get('rent_roll', {}),
        t12_analysis=processed_data.get('t12', {}),
        property_info=property_info,
        underwriting_summary=summary
    )
    
    # Ask if this is a bridge loan (affects tabs generated)
    print(f"\n🌉 Is this a bridge loan requiring pro forma tabs?")
    try:
        bridge_choice = input("Enter 'y' for bridge loan, 'n' for standard (default: n): ").strip().lower()
        is_bridge = bridge_choice in ['y', 'yes', '1', 'true']
    except KeyboardInterrupt:
        is_bridge = False
    
    if is_bridge:
        output_generator.set_bridge_loan_mode(True)
        print("✅ Bridge loan mode enabled - will generate pro forma tabs")
    
    # Manual Override Opportunity
    print(f"\n✏️ Manual Override Options:")
    print(f"   Current NOI: ${summary.get('noi_analysis', {}).get('net_operating_income', 0):,.0f}")
    print(f"   Current Expense Ratio: {summary.get('noi_analysis', {}).get('expense_ratio', 0):.1f}%")
    print(f"   Total Flags: {len(summary.get('flags_and_recommendations', []))}")
    
    try:
        override_choice = input("Would you like to make manual adjustments before export? (y/n, default: n): ").strip().lower()
        if override_choice in ['y', 'yes', '1', 'true']:
            print(f"\n🔧 Manual Adjustment Mode:")
            
            # Allow NOI override
            current_noi = summary.get('noi_analysis', {}).get('net_operating_income', 0)
            noi_input = input(f"Override NOI (current: ${current_noi:,.0f}, press Enter to keep): ").strip()
            if noi_input:
                try:
                    new_noi = float(noi_input.replace(',', '').replace('$', ''))
                    summary['noi_analysis']['net_operating_income'] = new_noi
                    print(f"✅ NOI updated to: ${new_noi:,.0f}")
                except ValueError:
                    print("⚠️ Invalid NOI input - keeping original")
            
            # Allow expense ratio override
            current_ratio = summary.get('noi_analysis', {}).get('expense_ratio', 0)
            ratio_input = input(f"Override Expense Ratio (current: {current_ratio:.1f}%, press Enter to keep): ").strip()
            if ratio_input:
                try:
                    new_ratio = float(ratio_input.replace('%', ''))
                    summary['noi_analysis']['expense_ratio'] = new_ratio
                    print(f"✅ Expense ratio updated to: {new_ratio:.1f}%")
                except ValueError:
                    print("⚠️ Invalid ratio input - keeping original")
            
            # Allow adding custom notes
            custom_note = input("Add custom analysis note (press Enter to skip): ").strip()
            if custom_note:
                summary.setdefault('flags_and_recommendations', []).append({
                    'type': 'manual_override',
                    'severity': 'info',
                    'message': f"Manual Override: {custom_note}"
                })
                print(f"✅ Custom note added")
            
            # Reload updated data
            output_generator.load_analysis_data(
                rent_roll_analysis=processed_data.get('rent_roll', {}),
                t12_analysis=processed_data.get('t12', {}),
                property_info=property_info,
                underwriting_summary=summary
            )
            print(f"✅ Manual adjustments applied")
        
    except KeyboardInterrupt:
        print(f"\n⏩ Skipping manual overrides - proceeding with original analysis")
    
    # Generate structured Excel package
    print(f"\n📄 Generating structured underwriting package...")
    
    try:
        excel_path = output_generator.export_to_excel()
        print(f"✅ Structured Excel package: {excel_path}")
        
        # Show package contents
        print(f"\n📋 Package Contents:")
        print(f"   1. Clean Rent Roll - Standardized unit data")
        print(f"   2. Clean T12 - Operating statement (cut at NOI)")
        print(f"   3. Underwriting Summary - Line items with % EGI and notes")
        
        if is_bridge:
            print(f"   4. Pro Forma Rent Roll - Projected rental income")
            print(f"   5. Pro Forma Income Statement - Projected operations")
            print(f"   6. Sources & Uses - Financing structure")
            print(f"   7. Construction Budget - Development costs")
        
        # Generate PDF package
        print(f"\n📄 Generating PDF package...")
        pdf_path = output_generator.generate_pdf_package(excel_path)
        if pdf_path.endswith('.pdf'):
            print(f"✅ PDF package generated: {pdf_path}")
            print(f"📧 Ready to send to lender!")
        else:
            print(f"💡 PDF Generation: Use Excel as master template for manual adjustments")
            print(f"📧 Excel package ready for final review and lender submission")
        
    except Exception as e:
        print(f"❌ Error generating structured package: {str(e)}")
        if output_generator.debug:
            import traceback
            traceback.print_exc()
    
    # Step 5: Deep Logic Analysis & Recommendations
    print(f"\n🧠 STEP 5: Deep Logic Analysis")
    print("-" * 40)
    
    # Apply deep logic for decision making
    deep_analysis = perform_deep_logic_analysis(processed_data, summary)
    
    print(f"🔍 Data Consistency Analysis:")
    for issue in deep_analysis.get('consistency_issues', [])[:3]:
        print(f"   • {issue}")
    
    print(f"\n📈 Trending Analysis:")
    for trend in deep_analysis.get('trends', [])[:3]:
        print(f"   • {trend}")
    
    print(f"\n🚩 Critical Flags:")
    critical_flags = [f for f in summary.get('flags_and_recommendations', []) 
                     if f.get('severity') == 'high'][:3]
    for flag in critical_flags:
        print(f"   • {flag.get('message', 'Unknown flag')}")
    
    # Step 6: Loan Sizing & Rate Analysis
    print(f"\n💰 STEP 6: Loan Sizing & Rate Analysis")
    print("-" * 40)
    
    # Get NOI from underwriting analysis
    noi = summary.get('noi_analysis', {}).get('net_operating_income', 0)
    
    if noi <= 0:
        print("⚠️ No positive NOI found - skipping loan analysis")
    else:
        # Get cap rate input from user
        print(f"\n🏢 Property NOI: ${noi:,.0f}")
        try:
            cap_rate_input = input("Enter cap rate for valuation (e.g., 6.5 for 6.5%) or press Enter for 6.0%: ").strip()
            cap_rate = float(cap_rate_input) / 100 if cap_rate_input else 0.06
        except (ValueError, KeyboardInterrupt):
            cap_rate = 0.06  # Default 6% cap rate
        
        # Set property data in loan engine
        loan_engine.set_property_data(noi, cap_rate)
        loan_engine.property_info = property_info
        
        # Ask for treasury term preference
        print(f"\n📈 Select Treasury Index:")
        print(f"   1. 5-Year Treasury")
        print(f"   2. 7-Year Treasury") 
        print(f"   3. 10-Year Treasury (Default)")
        print(f"   4. 15-Year Treasury (Avg of 10Y & 20Y)")
        print(f"   5. 20-Year Treasury")
        print(f"   6. 30-Year Treasury")
        
        try:
            treasury_choice = input("Enter choice (1-6) or press Enter for 10-Year: ").strip()
            treasury_map = {
                '1': TreasuryTerm.FIVE_YEAR,
                '2': TreasuryTerm.SEVEN_YEAR,
                '3': TreasuryTerm.TEN_YEAR,
                '4': TreasuryTerm.FIFTEEN_YEAR,
                '5': TreasuryTerm.TWENTY_YEAR,
                '6': TreasuryTerm.THIRTY_YEAR
            }
            treasury_term = treasury_map.get(treasury_choice, TreasuryTerm.TEN_YEAR)
        except KeyboardInterrupt:
            treasury_term = TreasuryTerm.TEN_YEAR
        
        loan_engine.set_treasury_term(treasury_term)
        
        # Ask about step-down prepayment for Fannie/Freddie
        try:
            step_down_input = input("Include step-down prepayment option for Fannie/Freddie? (y/n, default: n): ").strip().lower()
            step_down_prepay = step_down_input in ['y', 'yes', '1', 'true']
        except KeyboardInterrupt:
            step_down_prepay = False
        
        # Calculate loan scenarios
        print(f"\n🔄 Calculating loan scenarios...")
        try:
            scenarios = loan_engine.calculate_loan_scenarios(step_down_prepay)
            
            # Display results
            loan_engine.print_loan_scenarios(scenarios)
            
            # Export loan analysis
            if scenarios:
                print(f"\n💾 Exporting loan analysis...")
                loan_analysis_path = loan_engine.export_loan_analysis(scenarios)
                print(f"✅ Loan analysis exported: {loan_analysis_path}")
            
        except Exception as e:
            print(f"❌ Error in loan analysis: {str(e)}")
            if loan_engine.debug:
                import traceback
                traceback.print_exc()
    
    # Step 7: Save Results
    print(f"\n💾 STEP 7: Saving Results")
    print("-" * 40)
    
    saved_files = analyzer.save_analysis()
    for file_type, file_path in saved_files.items():
        print(f"✅ {file_type.title()}: {file_path}")
    
    print(f"\n🎉 Underwriting Analysis Complete!")
    print(f"📁 Check the 'outputs' directory for all generated files")
    
    return summary

def show_underwriting_rules():
    """Display the underwriting rules being applied."""
    print("📊 INCOME RULES")
    print("-" * 30)
    print("• Rental Income: Use current rents from rent roll")
    print("• Vacant Units: Calculate using average rent by unit type")
    print("• Other Income: Use actual T12 totals")
    print("• Flag units 30%+ under average rent")
    print("")
    
    print("💸 EXPENSE RULES")
    print("-" * 30)
    print("• Vacancy: 5% of GPI or actuals (whichever higher)")
    print("• Property Taxes: +7.5% for refinance")
    print("• Insurance: +5%")
    print("• Utilities: +2% (after removing spikes)")
    print("• R&M: Age-based minimums ($500-$1,000/unit)")
    print("• Management: Tiered rates (2.5%-5% based on income)")
    print("• Reserves: $250/unit")
    print("• Minimum expense ratio: 28% of EGI")
    print("")
    
    print("💰 LOAN SIZING RULES")
    print("-" * 30)
    print("• Property Value: NOI ÷ Cap Rate")
    print("• Loan Size: Lesser of Max LTV, Min DSCR, Min Debt Yield")
    print("")
    print("🏦 LOAN TYPES & CONSTRAINTS")
    print("-" * 30)
    print("• Fannie/Freddie: 75% LTV, 1.25x DSCR, 8% DY, 30Y amort")
    print("  - ≥$6M: UST+150bps | <$6M: UST+200bps")
    print("  - Tier pricing: T3 (-25bps), T4 (-50bps)")
    print("• CMBS: 75% LTV, 1.25x DSCR, 9% DY, Interest-Only")
    print("  - UST+300bps, $5M minimum")
    print("• Debt Fund: 80% LTV, 0.95x DSCR, 25Y amort")
    print("  - UST+150bps, $20M minimum")
    print("")
    print("📈 TREASURY OPTIONS")
    print("-" * 30)
    print("• 5Y, 7Y, 10Y (default), 15Y, 20Y, 30Y available")

def test_document_processor():
    """Test the document processor with sample files."""
    
    # Initialize the processor with debug mode
    processor = DocumentProcessor(debug=True)
    
    # Sample files to test
    sample_files = [
        "sample_data/RR_3350_Mount_Gilead_Rd_Atlanta_GA_30311.pdf",
        "sample_data/T12_3350_Mount_Gilead_Rd_Atlanta_GA_30311.pdf"
    ]
    
    for file_path in sample_files:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"\n{'='*60}")
        print(f"📄 Processing: {file_path}")
        print(f"{'='*60}")
        
        try:
            # Process the document
            results = processor.process_document(file_path)
            
            # Display results
            print(f"🔍 Document Type: {results['document_type']}")
            print(f"📊 Tables Found: {len(results['tables'])}")
            
            # Show extraction summary
            summary = results['extraction_summary']
            print(f"🛠️  Methods Used: {', '.join(summary['methods_used'])}")
            
            for method, count in summary['tables_per_method'].items():
                print(f"   - {method}: {count} tables")
            
            # Display table details
            for idx, table in enumerate(results['tables']):
                print(f"\n📋 Table {idx+1}:")
                print(f"   - Shape: {table.shape[0]} rows × {table.shape[1]} columns")
                print(f"   - Method: {table.attrs.get('method', 'unknown')}")
                print(f"   - Quality Score: {table.attrs.get('quality_score', 0):.2f}")
                print(f"   - Page: {table.attrs.get('page', 'unknown')}")
                
                # Show column names
                print(f"   - Columns: {', '.join(table.columns[:5])}" + 
                      ("..." if len(table.columns) > 5 else ""))
                
                # Show first few rows
                print(f"   - Sample Data:")
                if not table.empty:
                    for i, row in table.head(3).iterrows():
                        row_data = [str(val)[:20] + ("..." if len(str(val)) > 20 else "") 
                                  for val in row.values[:3]]
                        print(f"     Row {i}: {' | '.join(row_data)}")
                else:
                    print("     (Empty table)")
            
            # Save results
            print(f"\n💾 Saving results...")
            saved_files = processor.save_results(results)
            
            for file_type, file_path in saved_files.items():
                print(f"   - {file_type}: {file_path}")
            
            # Show specific analysis if available
            if 'rent_roll_analysis' in results:
                analysis = results['rent_roll_analysis']
                if 'main_table' in analysis:
                    print(f"\n🏢 Rent Roll Analysis:")
                    print(f"   - Units detected: {analysis.get('unit_count', 0)}")
                    print(f"   - Columns: {', '.join(analysis.get('columns_detected', []))}")
            
            if 't12_analysis' in results:
                analysis = results['t12_analysis']
                if 'main_table' in analysis:
                    print(f"\n💰 T12 Analysis:")
                    print(f"   - Line items: {analysis.get('rows_count', 0)}")
                    print(f"   - Columns: {', '.join(analysis.get('columns_detected', []))}")
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {str(e)}")
            import traceback
            traceback.print_exc()

def show_file_info():
    """Show information about available sample files."""
    print("📁 Available Sample Files:")
    print("-" * 30)
    
    sample_dir = "sample_data"
    if os.path.exists(sample_dir):
        for file in os.listdir(sample_dir):
            if file.endswith('.pdf'):
                file_path = os.path.join(sample_dir, file)
                size = os.path.getsize(file_path)
                print(f"   {file} ({size:,} bytes)")
    else:
        print("   No sample_data directory found")

if __name__ == "__main__":
    print("🚀 Document Processor & Underwriting Test")
    print("=" * 50)
    
    # Show available files
    show_file_info()
    
    # Show the rules being applied
    print("\n" + "="*60)
    show_underwriting_rules()
    print("\n" + "="*60)
    
    # Ask user which test to run
    print("\nChoose test to run:")
    print("1. Document Processing Only")
    print("2. Complete Underwriting Workflow (Recommended)")
    
    try:
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\n🔍 Running Document Processing Test...")
            test_document_processor()
        elif choice == "2":
            print("\n🚀 Running Complete Underwriting Workflow...")
            test_complete_underwriting_workflow()
        else:
            print("\n🚀 Running Complete Underwriting Workflow (Default)...")
            test_complete_underwriting_workflow()
    except KeyboardInterrupt:
        print("\n\n🚀 Running Complete Underwriting Workflow (Default)...")
        test_complete_underwriting_workflow()
    
    print(f"\n✅ Test completed!")
    print("Check the 'outputs' directory for extracted data files.")