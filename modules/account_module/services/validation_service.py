"""
Validation Service for Accounting Module
"""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from modules.admin_module.models.entities import FinancialYear
from modules.account_module.models.entities import AccountMaster, Ledger
from decimal import Decimal

class ValidationService:
    """Service for accounting validations"""
    
    @staticmethod
    def validate_financial_year(session: Session, transaction_date: datetime, tenant_id: int) -> FinancialYear:
        """
        Validate that transaction date falls within an active fiscal year
        
        Args:
            session: Database session
            transaction_date: Transaction date to validate
            tenant_id: Tenant ID
            
        Returns:
            FinancialYear: Active financial year
            
        Raises:
            ValueError: If no active fiscal year found or fiscal year is closed
        """
        financial_year = session.query(FinancialYear).filter(
            FinancialYear.tenant_id == tenant_id,
            FinancialYear.is_active == True,
            FinancialYear.start_date <= transaction_date,
            FinancialYear.end_date >= transaction_date
        ).first()
        
        if not financial_year:
            raise ValueError(
                f"No active financial year found for date {transaction_date.date()}. "
                "Please create a financial year covering this period."
            )
        
        if financial_year.is_closed:
            raise ValueError(
                f"Financial year '{financial_year.name}' is closed. "
                "Cannot post transactions to a closed period."
            )
        
        return financial_year
    
    @staticmethod
    def validate_debit_credit_balance(debit_total: float, credit_total: float, tolerance: float = 0.01) -> bool:
        """
        Validate that debit and credit totals are balanced
        
        Args:
            debit_total: Total debit amount
            credit_total: Total credit amount
            tolerance: Acceptable difference (default 0.01)
            
        Returns:
            bool: True if balanced
            
        Raises:
            ValueError: If not balanced
        """
        difference = abs(debit_total - credit_total)
        if difference > tolerance:
            raise ValueError(
                f"Debit ({debit_total:.2f}) and Credit ({credit_total:.2f}) are not balanced. "
                f"Difference: {difference:.2f}"
            )
        return True
    
    @staticmethod
    def validate_voucher_lines(lines: list) -> bool:
        """
        Validate voucher lines
        
        Args:
            lines: List of voucher lines
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If validation fails
        """
        if not lines or len(lines) < 2:
            raise ValueError("At least 2 line items are required for a voucher")
        
        valid_lines = [line for line in lines if line.get('account_id') and (line.get('debit', 0) > 0 or line.get('credit', 0) > 0)]
        
        if len(valid_lines) < 2:
            raise ValueError("At least 2 valid line items with account and amount are required")
        
        total_debit = sum(line.get('debit', 0) for line in valid_lines)
        total_credit = sum(line.get('credit', 0) for line in valid_lines)
        
        ValidationService.validate_debit_credit_balance(total_debit, total_credit)
        
        return True
    
    @staticmethod
    def calculate_ledger_balance(session: Session, account_id: int, transaction_date: datetime, tenant_id: int) -> Decimal:
        """
        Calculate correct ledger balance by querying previous entries
        
        Args:
            session: Database session
            account_id: Account ID
            transaction_date: Transaction date
            tenant_id: Tenant ID
            
        Returns:
            Decimal: Previous balance
        """
        # Get balance from last entry before this date
        previous_balance = session.query(
            func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
        ).filter(
            Ledger.account_id == account_id,
            Ledger.transaction_date < transaction_date,
            Ledger.tenant_id == tenant_id
        ).scalar() or 0
        
        # Add same-date entries up to now
        same_date_balance = session.query(
            func.coalesce(func.sum(Ledger.debit_amount), 0) - func.coalesce(func.sum(Ledger.credit_amount), 0)
        ).filter(
            Ledger.account_id == account_id,
            Ledger.transaction_date == transaction_date,
            Ledger.tenant_id == tenant_id
        ).scalar() or 0
        
        return Decimal(str(previous_balance)) + Decimal(str(same_date_balance))
    
    @staticmethod
    def validate_gst_calculation(subtotal: float, cgst_rate: float, sgst_rate: float, igst_rate: float, 
                                 cgst_amount: float, sgst_amount: float, igst_amount: float, 
                                 utgst_rate: float = 0, utgst_amount: float = 0) -> bool:
        """
        Validate GST calculation
        
        Args:
            subtotal: Taxable amount
            cgst_rate: CGST rate
            sgst_rate: SGST rate
            igst_rate: IGST rate
            cgst_amount: Calculated CGST
            sgst_amount: Calculated SGST
            igst_amount: Calculated IGST
            utgst_rate: UTGST rate (for Union Territories)
            utgst_amount: Calculated UTGST (for Union Territories)
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If calculation is incorrect
        """
        tolerance = 0.01
        
        if igst_rate > 0:
            # Interstate - only IGST
            expected_igst = round(subtotal * igst_rate / 100, 2)
            if abs(igst_amount - expected_igst) > tolerance:
                raise ValueError(f"IGST calculation incorrect. Expected: {expected_igst}, Got: {igst_amount}")
            if cgst_amount > 0 or sgst_amount > 0 or utgst_amount > 0:
                raise ValueError("CGST/SGST/UTGST should be zero for interstate transactions")
        elif utgst_rate > 0:
            # Union Territory - CGST + UTGST
            expected_cgst = round(subtotal * cgst_rate / 100, 2)
            expected_utgst = round(subtotal * utgst_rate / 100, 2)
            if abs(cgst_amount - expected_cgst) > tolerance:
                raise ValueError(f"CGST calculation incorrect. Expected: {expected_cgst}, Got: {cgst_amount}")
            if abs(utgst_amount - expected_utgst) > tolerance:
                raise ValueError(f"UTGST calculation incorrect. Expected: {expected_utgst}, Got: {utgst_amount}")
            if sgst_amount > 0 or igst_amount > 0:
                raise ValueError("SGST/IGST should be zero for Union Territory transactions")
        else:
            # Intrastate - CGST + SGST
            expected_cgst = round(subtotal * cgst_rate / 100, 2)
            expected_sgst = round(subtotal * sgst_rate / 100, 2)
            if abs(cgst_amount - expected_cgst) > tolerance:
                raise ValueError(f"CGST calculation incorrect. Expected: {expected_cgst}, Got: {cgst_amount}")
            if abs(sgst_amount - expected_sgst) > tolerance:
                raise ValueError(f"SGST calculation incorrect. Expected: {expected_sgst}, Got: {sgst_amount}")
            if igst_amount > 0 or utgst_amount > 0:
                raise ValueError("IGST/UTGST should be zero for intrastate transactions")
        
        return True
