from core.shared.utils.logger import logger

class AccountModule:
    def __init__(self, root):
        self.name = "Account Module"
        self.root = root
        self.current_screen = None
        logger.info("Account Module initialized", "AccountModule")
    
    def show_ledger_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.ledger_screen import LedgerScreen
        self.current_screen = LedgerScreen(self.root, self)
    
    def show_journal_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.journal_screen import JournalScreen
        self.current_screen = JournalScreen(self.root, self)
    
    def show_voucher_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.voucher_screen import VoucherScreen
        self.current_screen = VoucherScreen(self.root, self)
    
    def show_payment_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.payment_screen import PaymentScreen
        self.current_screen = PaymentScreen(self.root, self)
    
    def show_account_master_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.account_master_screen import AccountMasterScreen
        self.current_screen = AccountMasterScreen(self.root, self)
    
    def show_reports_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.reports_screen import ReportsScreen
        self.current_screen = ReportsScreen(self.root, self)
    
    def show_ar_aging_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.ar_aging_screen import ARAgingScreen
        self.current_screen = ARAgingScreen(self.root)
    
    def show_ap_aging_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.ap_aging_screen import APAgingScreen
        self.current_screen = APAgingScreen(self.root)
    
    def show_audit_trail_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.audit_trail_screen import AuditTrailScreen
        self.current_screen = AuditTrailScreen(self.root)
    
    def show_gst_calculator_screen(self):
        self.clear_current_screen()
        from modules.account_module.ui.screens.gst_calculator_screen import GSTCalculatorScreen
        self.current_screen = GSTCalculatorScreen(self.root)
    
    def clear_current_screen(self):
        if self.current_screen:
            self.current_screen.destroy()
        logger.info("Screen cleared", "AccountModule")
    
