#!/usr/bin/env python3
"""
Loan Sizing & Rate Rules Engine
Implements comprehensive loan analysis for different loan types with rate calculations.
"""

import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

class LoanType(Enum):
    """Supported loan types with their characteristics."""
    FANNIE_FREDDIE = "fannie_freddie"
    CMBS = "cmbs"
    DEBT_FUND = "debt_fund"

class TreasuryTerm(Enum):
    """Treasury index terms available."""
    FIVE_YEAR = "5Y"
    SEVEN_YEAR = "7Y"
    TEN_YEAR = "10Y"
    FIFTEEN_YEAR = "15Y"  # Average of 10Y and 20Y
    TWENTY_YEAR = "20Y"
    THIRTY_YEAR = "30Y"

@dataclass
class LoanConstraints:
    """Loan type constraints and parameters."""
    max_ltv: float
    min_dscr: float
    min_debt_yield: Optional[float]
    amortization_years: Optional[int]
    interest_only: bool
    base_spread: float  # Basis points over treasury
    min_loan_amount: Optional[float]
    max_loan_amount: Optional[float]
    has_tier_pricing: bool = False
    step_down_prepay_spread: Optional[float] = None

@dataclass
class TierPricing:
    """Tier pricing structure for Fannie/Freddie."""
    tier_name: str
    max_ltv: float
    min_dscr: float
    spread_adjustment: float  # Basis points adjustment from base

@dataclass
class LoanScenario:
    """Individual loan scenario results."""
    loan_type: LoanType
    tier_name: Optional[str]
    loan_amount: float
    ltv: float
    dscr: float
    debt_yield: float
    interest_rate: float
    payment: float
    amortization_years: Optional[int]
    treasury_rate: float
    spread: float
    step_down_prepay: bool
    constraint_binding: str  # Which constraint limits the loan size
    notes: List[str]

class LoanSizingEngine:
    """
    Comprehensive loan sizing and rate calculation engine.
    Implements all loan types with proper constraints and pricing.
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = self._setup_logger()
        
        # Property and NOI data
        self.noi = 0.0
        self.property_value = 0.0
        self.cap_rate = 0.0
        self.property_info = {}
        
        # Treasury rates (mock data - in production would fetch from API)
        self.treasury_rates = {
            TreasuryTerm.FIVE_YEAR: 4.25,
            TreasuryTerm.SEVEN_YEAR: 4.35,
            TreasuryTerm.TEN_YEAR: 4.45,
            TreasuryTerm.FIFTEEN_YEAR: 4.60,  # Calculated as average
            TreasuryTerm.TWENTY_YEAR: 4.75,
            TreasuryTerm.THIRTY_YEAR: 4.85
        }
        
        # Default treasury term
        self.treasury_term = TreasuryTerm.TEN_YEAR
        
        # Loan type definitions
        self.loan_types = self._define_loan_types()
        
        # Tier pricing for Fannie/Freddie
        self.tier_pricing = self._define_tier_pricing()
    
    def _setup_logger(self):
        """Set up logging for the loan sizing engine."""
        logger = logging.getLogger('LoanSizing')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        return logger
    
    def _define_loan_types(self) -> Dict[LoanType, LoanConstraints]:
        """Define all loan types with their constraints."""
        return {
            LoanType.FANNIE_FREDDIE: LoanConstraints(
                max_ltv=0.75,
                min_dscr=1.25,
                min_debt_yield=0.08,
                amortization_years=30,
                interest_only=False,
                base_spread=150,  # Will be adjusted based on loan size
                min_loan_amount=1_000_000,  # $1M minimum
                max_loan_amount=None,
                has_tier_pricing=True,
                step_down_prepay_spread=50  # Optional +50bps
            ),
            LoanType.CMBS: LoanConstraints(
                max_ltv=0.75,
                min_dscr=1.25,
                min_debt_yield=0.09,
                amortization_years=None,
                interest_only=True,
                base_spread=300,
                min_loan_amount=5_000_000,  # $5M minimum
                max_loan_amount=None,
                has_tier_pricing=False
            ),
            LoanType.DEBT_FUND: LoanConstraints(
                max_ltv=0.80,  # Higher LTV for bridge/value-add
                min_dscr=0.95,  # Lower DSCR requirement
                min_debt_yield=None,  # No debt yield requirement
                amortization_years=25,
                interest_only=False,
                base_spread=150,
                min_loan_amount=20_000_000,  # $20M minimum
                max_loan_amount=None,
                has_tier_pricing=False
            )
        }
    
    def _define_tier_pricing(self) -> List[TierPricing]:
        """Define Fannie/Freddie tier pricing structure."""
        return [
            TierPricing("Tier 2", 0.75, 1.25, 0),    # Base rate
            TierPricing("Tier 3", 0.65, 1.35, -25),  # -25bps
            TierPricing("Tier 4", 0.55, 1.45, -50)   # -50bps
        ]
    
    def set_property_data(self, noi: float, cap_rate: float = None, property_value: float = None):
        """Set property NOI and valuation data."""
        self.noi = noi
        
        if property_value:
            self.property_value = property_value
            self.cap_rate = noi / property_value if property_value > 0 else 0
        elif cap_rate:
            self.cap_rate = cap_rate
            self.property_value = noi / cap_rate if cap_rate > 0 else 0
        else:
            raise ValueError("Must provide either cap_rate or property_value")
        
        self.logger.info(f"💰 Property set: NOI ${noi:,.0f}, Value ${self.property_value:,.0f}, Cap Rate {self.cap_rate:.2%}")
    
    def set_treasury_term(self, term: TreasuryTerm):
        """Set the treasury index term for rate calculations."""
        self.treasury_term = term
        self.logger.info(f"📈 Treasury term set to: {term.value} ({self.treasury_rates[term]:.2f}%)")
    
    def get_treasury_rate(self, term: TreasuryTerm = None) -> float:
        """Get current treasury rate for specified term."""
        if term is None:
            term = self.treasury_term
        
        if term == TreasuryTerm.FIFTEEN_YEAR:
            # 15-Year is average of 10Y and 20Y
            ten_year = self.treasury_rates[TreasuryTerm.TEN_YEAR]
            twenty_year = self.treasury_rates[TreasuryTerm.TWENTY_YEAR]
            return (ten_year + twenty_year) / 2
        
        return self.treasury_rates[term]
    
    def calculate_loan_scenarios(self, step_down_prepay: bool = False) -> List[LoanScenario]:
        """Calculate all possible loan scenarios based on property data."""
        if self.noi <= 0 or self.property_value <= 0:
            raise ValueError("Property NOI and value must be set before calculating loans")
        
        scenarios = []
        
        # Calculate scenarios for each loan type
        for loan_type in LoanType:
            loan_scenarios = self._calculate_loan_type_scenarios(loan_type, step_down_prepay)
            scenarios.extend(loan_scenarios)
        
        # Sort by loan amount descending
        scenarios.sort(key=lambda x: x.loan_amount, reverse=True)
        
        self.logger.info(f"📊 Calculated {len(scenarios)} loan scenarios")
        return scenarios
    
    def _calculate_loan_type_scenarios(self, loan_type: LoanType, step_down_prepay: bool) -> List[LoanScenario]:
        """Calculate scenarios for a specific loan type."""
        constraints = self.loan_types[loan_type]
        scenarios = []
        
        # Check minimum loan amount
        if constraints.min_loan_amount and constraints.min_loan_amount > self.property_value * constraints.max_ltv:
            # Property too small for this loan type
            return scenarios
        
        if loan_type == LoanType.FANNIE_FREDDIE and constraints.has_tier_pricing:
            # Calculate scenarios for each tier
            for tier in self.tier_pricing:
                scenario = self._calculate_single_scenario(
                    loan_type, constraints, tier, step_down_prepay
                )
                if scenario:
                    scenarios.append(scenario)
        else:
            # Single scenario for non-tiered loan types
            scenario = self._calculate_single_scenario(
                loan_type, constraints, None, step_down_prepay
            )
            if scenario:
                scenarios.append(scenario)
        
        return scenarios
    
    def _calculate_single_scenario(self, loan_type: LoanType, constraints: LoanConstraints, 
                                  tier: TierPricing = None, step_down_prepay: bool = False) -> Optional[LoanScenario]:
        """Calculate a single loan scenario."""
        
        # Use tier constraints if available, otherwise base constraints
        max_ltv = tier.max_ltv if tier else constraints.max_ltv
        min_dscr = tier.min_dscr if tier else constraints.min_dscr
        
        # Calculate maximum loan amounts based on each constraint
        ltv_max_loan = self.property_value * max_ltv
        dscr_max_loan = self.noi / min_dscr if min_dscr > 0 else float('inf')
        
        debt_yield_max_loan = float('inf')
        if constraints.min_debt_yield:
            debt_yield_max_loan = self.noi / constraints.min_debt_yield
        
        # Binding constraint is the minimum
        binding_amounts = {
            'LTV': ltv_max_loan,
            'DSCR': dscr_max_loan,
            'Debt Yield': debt_yield_max_loan
        }
        
        loan_amount = min(binding_amounts.values())
        constraint_binding = min(binding_amounts, key=binding_amounts.get)
        
        # Check minimum loan amount
        if constraints.min_loan_amount and loan_amount < constraints.min_loan_amount:
            return None
        
        # Calculate metrics
        ltv = loan_amount / self.property_value
        debt_yield = self.noi / loan_amount if loan_amount > 0 else 0
        
        # Calculate interest rate
        treasury_rate = self.get_treasury_rate()
        spread = self._calculate_spread(loan_type, constraints, tier, loan_amount, step_down_prepay)
        interest_rate = treasury_rate + (spread / 100)  # Convert bps to percentage
        
        # Calculate payment
        if constraints.interest_only:
            payment = loan_amount * (interest_rate / 100) / 12  # Monthly interest only
            dscr = (self.noi / 12) / payment if payment > 0 else float('inf')
        else:
            # Amortizing payment
            monthly_rate = interest_rate / 100 / 12
            num_payments = constraints.amortization_years * 12
            if monthly_rate > 0:
                payment = loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
            else:
                payment = loan_amount / num_payments
            dscr = (self.noi / 12) / payment if payment > 0 else float('inf')
        
        # Generate notes
        notes = []
        notes.append(f"Treasury {self.treasury_term.value}: {treasury_rate:.2f}%")
        notes.append(f"Spread: {spread:.0f} bps")
        if tier:
            notes.append(f"Tier pricing: {tier.tier_name}")
        if step_down_prepay and constraints.step_down_prepay_spread:
            notes.append(f"Step-down prepay: +{constraints.step_down_prepay_spread} bps")
        notes.append(f"Binding constraint: {constraint_binding}")
        
        return LoanScenario(
            loan_type=loan_type,
            tier_name=tier.tier_name if tier else None,
            loan_amount=loan_amount,
            ltv=ltv,
            dscr=dscr,
            debt_yield=debt_yield,
            interest_rate=interest_rate,
            payment=payment,
            amortization_years=constraints.amortization_years,
            treasury_rate=treasury_rate,
            spread=spread,
            step_down_prepay=step_down_prepay,
            constraint_binding=constraint_binding,
            notes=notes
        )
    
    def _calculate_spread(self, loan_type: LoanType, constraints: LoanConstraints, 
                         tier: TierPricing = None, loan_amount: float = 0, 
                         step_down_prepay: bool = False) -> float:
        """Calculate spread over treasury for the loan."""
        
        base_spread = constraints.base_spread
        
        # Fannie/Freddie loan size adjustment
        if loan_type == LoanType.FANNIE_FREDDIE:
            if loan_amount >= 6_000_000:
                base_spread = 150  # ≥$6M: +150bps
            else:
                base_spread = 200  # <$6M: +200bps
        
        # Tier pricing adjustment
        if tier:
            base_spread += tier.spread_adjustment
        
        # Step-down prepay adjustment
        if step_down_prepay and constraints.step_down_prepay_spread:
            base_spread += constraints.step_down_prepay_spread
        
        return base_spread
    
    def generate_loan_summary_table(self, scenarios: List[LoanScenario]) -> pd.DataFrame:
        """Generate a comprehensive loan summary table."""
        
        data = []
        for scenario in scenarios:
            
            # Format loan type display name
            loan_type_name = {
                LoanType.FANNIE_FREDDIE: "Fannie/Freddie",
                LoanType.CMBS: "CMBS",
                LoanType.DEBT_FUND: "Debt Fund"
            }[scenario.loan_type]
            
            if scenario.tier_name:
                loan_type_name += f" ({scenario.tier_name})"
            
            # Payment structure
            if scenario.amortization_years:
                payment_structure = f"{scenario.amortization_years}Y Amort"
            else:
                payment_structure = "Interest Only"
            
            if scenario.step_down_prepay:
                payment_structure += " + Step-Down"
            
            data.append({
                'Loan Type': loan_type_name,
                'Loan Amount': f"${scenario.loan_amount:,.0f}",
                'LTV': f"{scenario.ltv:.1%}",
                'DSCR': f"{scenario.dscr:.2f}x",
                'Debt Yield': f"{scenario.debt_yield:.1%}" if scenario.debt_yield < 1 else f"{scenario.debt_yield:.1f}%",
                'Interest Rate': f"{scenario.interest_rate:.3f}%",
                'Payment Structure': payment_structure,
                'Monthly Payment': f"${scenario.payment:,.0f}",
                'Treasury Rate': f"{scenario.treasury_rate:.2f}%",
                'Spread': f"{scenario.spread:.0f} bps",
                'Binding Constraint': scenario.constraint_binding
            })
        
        return pd.DataFrame(data)
    
    def export_loan_analysis(self, scenarios: List[LoanScenario], output_path: str = None) -> str:
        """Export comprehensive loan analysis to Excel."""
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            property_name = self.property_info.get('property_name', 'Property').replace(' ', '_')
            output_path = f"outputs/{property_name}_Loan_Analysis_{timestamp}.xlsx"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        self.logger.info(f"📊 Exporting loan analysis to: {output_path}")
        
        # Create summary table
        summary_df = self.generate_loan_summary_table(scenarios)
        
        # Create detailed analysis
        detailed_data = []
        for scenario in scenarios:
            detailed_data.append({
                'Loan Type': scenario.loan_type.value,
                'Tier': scenario.tier_name or '',
                'Loan Amount': scenario.loan_amount,
                'LTV': scenario.ltv,
                'DSCR': scenario.dscr,
                'Debt Yield': scenario.debt_yield,
                'Interest Rate': scenario.interest_rate,
                'Monthly Payment': scenario.payment,
                'Annual Payment': scenario.payment * 12,
                'Treasury Rate': scenario.treasury_rate,
                'Spread (bps)': scenario.spread,
                'Amortization': scenario.amortization_years or 0,
                'Interest Only': not bool(scenario.amortization_years),
                'Step Down Prepay': scenario.step_down_prepay,
                'Binding Constraint': scenario.constraint_binding,
                'Notes': '; '.join(scenario.notes)
            })
        
        detailed_df = pd.DataFrame(detailed_data)
        
        # Property summary
        property_summary = pd.DataFrame([{
            'Property Value': self.property_value,
            'Net Operating Income': self.noi,
            'Cap Rate': self.cap_rate,
            'Treasury Term': self.treasury_term.value,
            'Treasury Rate': self.get_treasury_rate(),
            'Analysis Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        
        # Export to Excel
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Loan Summary', index=False)
            detailed_df.to_excel(writer, sheet_name='Detailed Analysis', index=False)
            property_summary.to_excel(writer, sheet_name='Property Summary', index=False)
        
        self.logger.info(f"✅ Loan analysis exported successfully")
        return output_path
    
    def print_loan_scenarios(self, scenarios: List[LoanScenario]):
        """Print formatted loan scenarios to console."""
        
        print(f"\n💰 LOAN SIZING ANALYSIS")
        print(f"=" * 80)
        print(f"Property Value: ${self.property_value:,.0f}")
        print(f"Net Operating Income: ${self.noi:,.0f}")
        print(f"Cap Rate: {self.cap_rate:.2%}")
        print(f"Treasury Index: {self.treasury_term.value} ({self.get_treasury_rate():.2f}%)")
        
        if not scenarios:
            print("\n❌ No qualifying loan scenarios found")
            return
        
        print(f"\n📊 QUALIFYING LOAN SCENARIOS ({len(scenarios)} found)")
        print(f"-" * 80)
        
        for i, scenario in enumerate(scenarios, 1):
            loan_type_name = {
                LoanType.FANNIE_FREDDIE: "Fannie/Freddie",
                LoanType.CMBS: "CMBS", 
                LoanType.DEBT_FUND: "Debt Fund"
            }[scenario.loan_type]
            
            if scenario.tier_name:
                loan_type_name += f" ({scenario.tier_name})"
            
            print(f"\n{i}. {loan_type_name}")
            print(f"   💵 Loan Amount: ${scenario.loan_amount:,.0f}")
            print(f"   📊 LTV: {scenario.ltv:.1%} | DSCR: {scenario.dscr:.2f}x | Debt Yield: {scenario.debt_yield:.1%}")
            print(f"   💹 Rate: {scenario.interest_rate:.3f}% | Payment: ${scenario.payment:,.0f}/month")
            print(f"   🎯 Binding: {scenario.constraint_binding}")
            
            if scenario.amortization_years:
                print(f"   📅 {scenario.amortization_years}-year amortization")
            else:
                print(f"   📅 Interest-only")
            
            if scenario.step_down_prepay:
                print(f"   📝 Step-down prepayment option included")

# Example usage and integration
if __name__ == "__main__":
    # Example usage
    engine = LoanSizingEngine(debug=True)
    
    # Set property data
    noi = 500000  # $500K NOI
    cap_rate = 0.06  # 6% cap rate
    engine.set_property_data(noi, cap_rate)
    
    # Calculate scenarios
    scenarios = engine.calculate_loan_scenarios()
    engine.print_loan_scenarios(scenarios)
    
    # Export analysis
    engine.export_loan_analysis(scenarios)
    
    print("📊 Loan Sizing Engine initialized and tested")
