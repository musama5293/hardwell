#!/usr/bin/env python3
"""
Enhanced Underwriting Analyzer
Applies comprehensive income and expense rules to extracted document data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import re
from datetime import datetime
import json

class UnderwritingAnalyzer:
    """Advanced underwriting analysis with comprehensive rules."""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.property_info = {}
        self.rent_roll_data = None
        self.t12_data = None
        self.analysis_results = {}
        
    def set_property_info(self, info: Dict[str, Any]):
        """Set property information for analysis."""
        self.property_info = info
        if self.debug:
            print(f"🏢 Property Info Set: {info.get('property_name', 'Unknown')}")
    
    def load_rent_roll(self, rent_roll_df: pd.DataFrame):
        """Load and analyze rent roll data."""
        self.rent_roll_data = rent_roll_df.copy()
        if self.debug:
            print(f"📋 Rent Roll Loaded: {len(rent_roll_df)} rows")
        return self._analyze_rent_roll()
    
    def load_t12(self, t12_df: pd.DataFrame):
        """Load and analyze T12 data."""
        self.t12_data = t12_df.copy()
        if self.debug:
            print(f"💰 T12 Loaded: {len(t12_df)} rows")
        return self._analyze_t12()
    
    def _analyze_rent_roll(self) -> Dict[str, Any]:
        """📊 INCOME RULES - Analyze rent roll data."""
        if self.rent_roll_data is None:
            return {}
        
        df = self.rent_roll_data
        analysis = {
            'unit_analysis': {},
            'rent_analysis': {},
            'occupancy_analysis': {},
            'flags': []
        }
        
        # Detect key columns
        unit_col = self._find_column(df, ['unit', 'apt', 'apartment', 'number'])
        rent_col = self._find_column(df, ['rent', 'current rent', 'monthly rent'])
        unit_type_col = self._find_column(df, ['type', 'unit type', 'bed', 'bedroom'])
        sqft_col = self._find_column(df, ['sqft', 'sq ft', 'square feet', 'sf'])
        status_col = self._find_column(df, ['status', 'occupied', 'vacant'])
        
        if self.debug:
            print(f"🔍 Detected Columns:")
            print(f"   Unit: {unit_col}")
            print(f"   Rent: {rent_col}")
            print(f"   Type: {unit_type_col}")
            print(f"   SqFt: {sqft_col}")
            print(f"   Status: {status_col}")
        
        # Clean and process rent data
        if rent_col:
            df['clean_rent'] = df[rent_col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df['clean_rent'] = pd.to_numeric(df['clean_rent'], errors='coerce')
            df = df[df['clean_rent'] > 0]  # Remove invalid rents
        
        # Analyze by unit type
        if unit_type_col and rent_col:
            unit_type_analysis = self._analyze_by_unit_type(df, unit_type_col, rent_col, sqft_col, status_col)
            analysis['unit_analysis'] = unit_type_analysis
        
        # Calculate gross potential income
        if rent_col:
            total_units = len(df)
            occupied_units = self._count_occupied_units(df, status_col)
            vacant_units = total_units - occupied_units
            
            # Current rental income (occupied units)
            current_income = df[df['clean_rent'] > 0]['clean_rent'].sum()
            
            # Vacant unit income using average rent by type
            vacant_income = self._calculate_vacant_income(df, unit_type_col, rent_col, status_col)
            
            gross_potential_income = current_income + vacant_income
            
            analysis['rent_analysis'] = {
                'total_units': total_units,
                'occupied_units': occupied_units,
                'vacant_units': vacant_units,
                'current_monthly_income': current_income,
                'vacant_unit_income': vacant_income,
                'gross_potential_income': gross_potential_income,
                'annual_gpi': gross_potential_income * 12
            }
        
        # Flag underpriced units (30%+ under average)
        if unit_type_col and rent_col:
            underpriced_flags = self._flag_underpriced_units(df, unit_type_col, rent_col)
            analysis['flags'].extend(underpriced_flags)
        
        # Check for missing square footage
        if not sqft_col or df[sqft_col].isna().sum() > 0:
            analysis['flags'].append({
                'type': 'missing_sqft',
                'message': 'Square footage data is missing or incomplete',
                'action': 'Request square footage by unit type from user'
            })
        
        self.analysis_results['rent_roll'] = analysis
        return analysis
    
    def _analyze_t12(self) -> Dict[str, Any]:
        """💸 EXPENSE RULES - Analyze T12 data."""
        if self.t12_data is None:
            return {}
        
        df = self.t12_data
        analysis = {
            'income_analysis': {},
            'expense_analysis': {},
            'adjusted_expenses': {},
            'flags': []
        }
        
        # Find income and expense line items
        income_items = self._extract_income_items(df)
        expense_items = self._extract_expense_items(df)
        
        # Apply income rules
        income_analysis = self._apply_income_rules(income_items)
        analysis['income_analysis'] = income_analysis
        
        # Apply expense rules
        expense_analysis = self._apply_expense_rules(expense_items)
        analysis['expense_analysis'] = expense_analysis
        
        self.analysis_results['t12'] = analysis
        return analysis
    
    def _apply_expense_rules(self, expense_items: Dict[str, float]) -> Dict[str, Any]:
        """Apply comprehensive expense rules."""
        property_age = self.property_info.get('property_age', 25)
        unit_count = self.property_info.get('unit_count', 1)
        is_refinance = self.property_info.get('transaction_type', 'refinance') == 'refinance'
        
        adjusted_expenses = {}
        adjustments = {}
        
        # 1. Vacancy - 5% of GPI or actuals (whichever higher)
        if 'rent_roll' in self.analysis_results:
            gpi = self.analysis_results['rent_roll']['rent_analysis'].get('annual_gpi', 0)
            vacancy_5_percent = gpi * 0.05
            actual_vacancy = expense_items.get('vacancy', 0)
            adjusted_expenses['vacancy'] = max(vacancy_5_percent, actual_vacancy)
            adjustments['vacancy'] = f"Used {max(vacancy_5_percent, actual_vacancy):,.0f} (5% of GPI: {vacancy_5_percent:,.0f}, Actual: {actual_vacancy:,.0f})"
        
        # 2. Property Taxes
        actual_taxes = expense_items.get('property_taxes', 0)
        if is_refinance:
            adjusted_expenses['property_taxes'] = actual_taxes * 1.075  # Increase by 7.5%
            adjustments['property_taxes'] = f"Refinance: Increased actual {actual_taxes:,.0f} by 7.5%"
        else:
            # For acquisition, would need millage rate calculation
            adjusted_expenses['property_taxes'] = actual_taxes
            adjustments['property_taxes'] = "Acquisition: Using actuals (millage rate calculation needed)"
        
        # 3. Insurance - Increase by 5%
        actual_insurance = expense_items.get('insurance', 0)
        adjusted_expenses['insurance'] = actual_insurance * 1.05
        adjustments['insurance'] = f"Increased actual {actual_insurance:,.0f} by 5%"
        
        # 4. Utilities - Increase by 2% (after removing spikes)
        utility_items = ['electricity', 'water', 'sewer', 'trash']
        for utility in utility_items:
            actual_utility = expense_items.get(utility, 0)
            # TODO: Implement spike detection and removal
            adjusted_expenses[utility] = actual_utility * 1.02
            adjustments[utility] = f"Increased actual {actual_utility:,.0f} by 2%"
        
        # 5. Repairs & Maintenance - Age-based minimums
        rm_minimums = {
            (0, 10): 500,
            (10, 20): 600,
            (20, 30): 700,
            (30, 40): 800,
            (40, 50): 900,
            (50, 100): 1000
        }
        
        rm_minimum = 500  # Default
        for age_range, minimum in rm_minimums.items():
            if age_range[0] <= property_age < age_range[1]:
                rm_minimum = minimum
                break
        
        rm_minimum_total = rm_minimum * unit_count
        rm_cap = 1500 * unit_count
        actual_rm = expense_items.get('repairs_maintenance', 0)
        
        if actual_rm < rm_minimum_total:
            adjusted_expenses['repairs_maintenance'] = rm_minimum_total
            adjustments['repairs_maintenance'] = f"Increased to minimum ${rm_minimum}/unit for {property_age}yr property"
        elif actual_rm > rm_cap:
            adjusted_expenses['repairs_maintenance'] = rm_cap
            adjustments['repairs_maintenance'] = f"Capped at ${1500}/unit (excess: ${(actual_rm - rm_cap):,.0f})"
        else:
            adjusted_expenses['repairs_maintenance'] = actual_rm
            adjustments['repairs_maintenance'] = f"Used actual (within range)"
        
        # 6. Payroll - Same rules as R&M
        actual_payroll = expense_items.get('payroll', 0)
        payroll_minimum_total = rm_minimum * unit_count
        payroll_cap = 1500 * unit_count
        
        if actual_payroll < payroll_minimum_total:
            adjusted_expenses['payroll'] = payroll_minimum_total
            adjustments['payroll'] = f"Increased to minimum ${rm_minimum}/unit"
        elif actual_payroll > payroll_cap:
            adjusted_expenses['payroll'] = payroll_cap
            adjustments['payroll'] = f"Capped at ${1500}/unit"
        else:
            adjusted_expenses['payroll'] = actual_payroll
            adjustments['payroll'] = f"Used actual (within range)"
        
        # 7. Professional Fees / General Administrative
        actual_admin = expense_items.get('admin_fees', 0)
        admin_minimum = 1000
        admin_maximum = 400 * unit_count
        
        if actual_admin < admin_minimum:
            adjusted_expenses['admin_fees'] = admin_minimum
            adjustments['admin_fees'] = f"Increased to minimum $1,000"
        elif actual_admin > admin_maximum:
            adjusted_expenses['admin_fees'] = admin_maximum
            adjustments['admin_fees'] = f"Capped at $400/unit"
        else:
            adjusted_expenses['admin_fees'] = actual_admin
            adjustments['admin_fees'] = f"Used actual (within range)"
        
        # 8. Management Fee - Based on gross income
        if 'rent_roll' in self.analysis_results:
            gross_income = self.analysis_results['rent_roll']['rent_analysis'].get('annual_gpi', 0)
            
            if gross_income <= 500000:
                mgmt_rate = 0.05
            elif gross_income <= 750000:
                mgmt_rate = 0.045
            elif gross_income <= 1000000:
                mgmt_rate = 0.04
            elif gross_income <= 1500000:
                mgmt_rate = 0.035
            elif gross_income <= 2000000:
                mgmt_rate = 0.03
            else:
                mgmt_rate = 0.025
            
            adjusted_expenses['management_fee'] = gross_income * mgmt_rate
            adjustments['management_fee'] = f"Applied {mgmt_rate*100}% rate to gross income of ${gross_income:,.0f}"
        
        # 9. Replacement Reserves - Always $250/unit
        adjusted_expenses['replacement_reserves'] = 250 * unit_count
        adjustments['replacement_reserves'] = f"Applied $250/unit for {unit_count} units"
        
        # 10. Check minimum expense ratio (28% of EGI)
        total_expenses = sum(adjusted_expenses.values())
        if 'rent_roll' in self.analysis_results:
            gpi = self.analysis_results['rent_roll']['rent_analysis'].get('annual_gpi', 0)
            vacancy = adjusted_expenses.get('vacancy', 0)
            egi = gpi - vacancy
            expense_ratio = total_expenses / egi if egi > 0 else 0
            
            if expense_ratio < 0.28:
                shortfall = (egi * 0.28) - total_expenses
                adjustments['minimum_ratio'] = f"Expense ratio {expense_ratio:.1%} below 28% minimum. Shortfall: ${shortfall:,.0f}"
            else:
                adjustments['minimum_ratio'] = f"Expense ratio {expense_ratio:.1%} meets 28% minimum"
        
        return {
            'adjusted_expenses': adjusted_expenses,
            'adjustments': adjustments,
            'total_adjusted_expenses': total_expenses
        }
    
    def _apply_income_rules(self, income_items: Dict[str, float]) -> Dict[str, Any]:
        """Apply income analysis rules."""
        analysis = {}
        
        # Other Income - Use actual T12 total
        other_income = income_items.get('other_income', 0)
        if other_income == 0:
            analysis['other_income_flag'] = "Other income missing - requires clarification"
        else:
            analysis['other_income'] = other_income
        
        # TODO: Implement occupancy trending analysis (T3, T2, T4 vs T12)
        # This would require additional period data
        
        return analysis
    
    def _find_column(self, df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
        """Find column that matches keywords."""
        for col in df.columns:
            col_lower = str(col).lower()
            for keyword in keywords:
                if keyword.lower() in col_lower:
                    return col
        return None
    
    def _analyze_by_unit_type(self, df: pd.DataFrame, type_col: str, rent_col: str, 
                             sqft_col: Optional[str], status_col: Optional[str]) -> Dict[str, Any]:
        """Analyze rent and occupancy by unit type."""
        analysis = {}
        
        for unit_type in df[type_col].dropna().unique():
            type_data = df[df[type_col] == unit_type]
            
            avg_rent = type_data['clean_rent'].mean()
            occupied_count = self._count_occupied_units(type_data, status_col)
            
            type_analysis = {
                'avg_rent': avg_rent,
                'unit_count': len(type_data),
                'occupied_count': occupied_count,
                'vacancy_rate': (len(type_data) - occupied_count) / len(type_data)
            }
            
            # Add rent per square foot if available
            if sqft_col:
                avg_sqft = pd.to_numeric(type_data[sqft_col], errors='coerce').mean()
                if not pd.isna(avg_sqft) and avg_sqft > 0:
                    type_analysis['avg_sqft'] = avg_sqft
                    type_analysis['rent_per_sqft'] = avg_rent / avg_sqft
            
            analysis[unit_type] = type_analysis
        
        return analysis
    
    def _count_occupied_units(self, df: pd.DataFrame, status_col: Optional[str]) -> int:
        """Count occupied units."""
        if not status_col:
            # Assume all units with rent > 0 are occupied
            return len(df[df['clean_rent'] > 0])
        
        occupied_keywords = ['occupied', 'occ', 'rented']
        status_series = df[status_col].astype(str).str.lower()
        
        for keyword in occupied_keywords:
            occupied_mask = status_series.str.contains(keyword, na=False)
            if occupied_mask.any():
                return occupied_mask.sum()
        
        # Fallback: assume non-zero rent means occupied
        return len(df[df['clean_rent'] > 0])
    
    def _calculate_vacant_income(self, df: pd.DataFrame, type_col: str, 
                                rent_col: str, status_col: Optional[str]) -> float:
        """Calculate income from vacant units using average rent by type."""
        if not type_col or not status_col:
            return 0
        
        vacant_income = 0
        
        # Get vacant units
        vacant_keywords = ['vacant', 'vac', 'empty']
        status_series = df[status_col].astype(str).str.lower()
        
        vacant_mask = pd.Series([False] * len(df))
        for keyword in vacant_keywords:
            vacant_mask |= status_series.str.contains(keyword, na=False)
        
        vacant_units = df[vacant_mask]
        
        # Calculate income for each vacant unit using type average
        for _, vacant_unit in vacant_units.iterrows():
            unit_type = vacant_unit[type_col]
            
            # Get average rent for this unit type (from occupied units)
            type_units = df[df[type_col] == unit_type]
            occupied_type_units = type_units[~vacant_mask & (type_units.index.isin(df.index))]
            
            if len(occupied_type_units) > 0:
                avg_rent = occupied_type_units['clean_rent'].mean()
                vacant_income += avg_rent
        
        return vacant_income
    
    def _flag_underpriced_units(self, df: pd.DataFrame, type_col: str, rent_col: str) -> List[Dict]:
        """Flag units that are 30%+ under average for their type."""
        flags = []
        
        for unit_type in df[type_col].dropna().unique():
            type_data = df[df[type_col] == unit_type]
            avg_rent = type_data['clean_rent'].mean()
            threshold = avg_rent * 0.7  # 30% under average
            
            underpriced = type_data[type_data['clean_rent'] < threshold]
            
            for _, unit in underpriced.iterrows():
                flags.append({
                    'type': 'underpriced_unit',
                    'unit': unit.get('unit', 'Unknown'),
                    'unit_type': unit_type,
                    'current_rent': unit['clean_rent'],
                    'type_average': avg_rent,
                    'percent_under': ((avg_rent - unit['clean_rent']) / avg_rent * 100),
                    'message': f"Unit {unit.get('unit', 'Unknown')} ({unit_type}) is {((avg_rent - unit['clean_rent']) / avg_rent * 100):.0f}% under type average"
                })
        
        return flags
    
    def _extract_income_items(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract income line items from T12."""
        income_items = {}
        
        # Look for income-related rows
        income_keywords = {
            'rental_income': ['rental income', 'rent income', 'rental revenue'],
            'other_income': ['other income', 'misc income', 'ancillary income']
        }
        
        for item_type, keywords in income_keywords.items():
            for _, row in df.iterrows():
                row_text = str(row.iloc[0]).lower()
                for keyword in keywords:
                    if keyword in row_text:
                        # Try to extract numeric value from the row
                        for col in df.columns[1:]:  # Skip first column (description)
                            try:
                                value = float(str(row[col]).replace(',', '').replace('$', '').replace('(', '-').replace(')', ''))
                                income_items[item_type] = value
                                break
                            except:
                                continue
                        break
        
        return income_items
    
    def _extract_expense_items(self, df: pd.DataFrame) -> Dict[str, float]:
        """Extract expense line items from T12."""
        expense_items = {}
        
        # Expense keywords mapping
        expense_keywords = {
            'vacancy': ['vacancy', 'vacancy loss', 'vacant'],
            'property_taxes': ['property tax', 'real estate tax', 'taxes'],
            'insurance': ['insurance'],
            'electricity': ['electric', 'electricity'],
            'water': ['water'],
            'sewer': ['sewer'],
            'trash': ['trash', 'garbage'],
            'repairs_maintenance': ['repairs', 'maintenance', 'r&m', 'repair & maintenance'],
            'payroll': ['payroll', 'wages', 'salary'],
            'admin_fees': ['admin', 'professional', 'general admin', 'office'],
            'management_fee': ['management', 'mgmt']
        }
        
        for item_type, keywords in expense_keywords.items():
            for _, row in df.iterrows():
                row_text = str(row.iloc[0]).lower()
                for keyword in keywords:
                    if keyword in row_text:
                        # Try to extract numeric value from the row
                        for col in df.columns[1:]:  # Skip first column (description)
                            try:
                                value_str = str(row[col]).replace(',', '').replace('$', '')
                                # Handle negative values in parentheses
                                if '(' in value_str and ')' in value_str:
                                    value_str = value_str.replace('(', '-').replace(')', '')
                                value = float(value_str)
                                expense_items[item_type] = abs(value)  # Ensure positive
                                break
                            except:
                                continue
                        break
        
        return expense_items
    
    def generate_underwriting_summary(self) -> Dict[str, Any]:
        """Generate comprehensive underwriting summary."""
        summary = {
            'property_info': self.property_info,
            'income_summary': {},
            'expense_summary': {},
            'noi_analysis': {},
            'flags_and_recommendations': []
        }
        
        # Compile income summary
        if 'rent_roll' in self.analysis_results:
            rent_analysis = self.analysis_results['rent_roll']['rent_analysis']
            summary['income_summary'] = {
                'gross_potential_income': rent_analysis.get('annual_gpi', 0),
                'current_monthly_income': rent_analysis.get('current_monthly_income', 0),
                'vacant_unit_potential': rent_analysis.get('vacant_unit_income', 0) * 12,
                'occupancy_rate': (rent_analysis.get('occupied_units', 0) / rent_analysis.get('total_units', 1)) * 100
            }
        
        # Compile expense summary
        if 't12' in self.analysis_results:
            expense_analysis = self.analysis_results['t12']['expense_analysis']
            summary['expense_summary'] = expense_analysis.get('adjusted_expenses', {})
            summary['total_expenses'] = expense_analysis.get('total_adjusted_expenses', 0)
        
        # Calculate NOI
        gpi = summary['income_summary'].get('gross_potential_income', 0)
        vacancy = summary['expense_summary'].get('vacancy', 0)
        total_expenses = summary.get('total_expenses', 0)
        
        egi = gpi - vacancy
        noi = egi - total_expenses
        
        summary['noi_analysis'] = {
            'gross_potential_income': gpi,
            'vacancy_loss': vacancy,
            'effective_gross_income': egi,
            'total_expenses': total_expenses,
            'net_operating_income': noi,
            'expense_ratio': (total_expenses / egi * 100) if egi > 0 else 0
        }
        
        # Compile all flags
        all_flags = []
        for analysis in self.analysis_results.values():
            all_flags.extend(analysis.get('flags', []))
        
        summary['flags_and_recommendations'] = all_flags
        
        return summary
    
    def save_analysis(self, output_dir: str = "outputs") -> Dict[str, str]:
        """Save analysis results to files."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        saved_files = {}
        
        # Save underwriting summary
        summary = self.generate_underwriting_summary()
        summary_file = os.path.join(output_dir, "underwriting_summary.json")
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        saved_files['summary'] = summary_file
        
        # Save detailed analysis
        if self.analysis_results:
            detail_file = os.path.join(output_dir, "detailed_analysis.json")
            with open(detail_file, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            saved_files['details'] = detail_file
        
        return saved_files

if __name__ == "__main__":
    # Example usage
    analyzer = UnderwritingAnalyzer(debug=True)
    
    # Set property info
    analyzer.set_property_info({
        'property_name': 'Sample Apartments',
        'property_address': '123 Main St',
        'unit_count': 100,
        'property_age': 25,
        'transaction_type': 'refinance'
    })
    
    print("✅ Underwriting Analyzer ready for document analysis!")
