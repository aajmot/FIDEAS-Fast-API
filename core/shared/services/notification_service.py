from typing import List, Dict, Optional
from datetime import datetime
from core.database.connection import db_manager
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class NotificationService:
    @staticmethod
    def send_email(to_email: str, subject: str, body: str, tenant_id: int) -> bool:
        try:
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER')
            smtp_pass = os.getenv('SMTP_PASS')
            
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            server.quit()
            
            NotificationService._log_notification(tenant_id, 'EMAIL', to_email, subject, 'SENT')
            return True
        except Exception as e:
            NotificationService._log_notification(tenant_id, 'EMAIL', to_email, subject, 'FAILED', str(e))
            return False

    @staticmethod
    def send_invoice_email(voucher_id: int, tenant_id: int) -> bool:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT v.voucher_no, v.voucher_date, v.total_amount, p.party_name, p.email "
                "FROM vouchers v JOIN parties p ON v.party_id = p.party_id "
                "WHERE v.voucher_id = :vid AND v.tenant_id = :tid",
                {"vid": voucher_id, "tid": tenant_id}
            )
            row = result.fetchone()
            if row and row[4]:
                subject = f"Invoice {row[0]} - Amount: Rs{row[2]}"
                body = f"<h3>Invoice Details</h3><p>Invoice No: {row[0]}</p><p>Date: {row[1]}</p><p>Amount: Rs{row[2]}</p><p>Thank you!</p>"
                return NotificationService.send_email(row[4], subject, body, tenant_id)
            return False

    @staticmethod
    def send_payment_reminder(party_id: int, tenant_id: int) -> bool:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT p.party_name, p.email, SUM(v.total_amount) as pending FROM parties p "
                "JOIN vouchers v ON p.party_id = v.party_id "
                "WHERE p.party_id = :pid AND p.tenant_id = :tid AND v.payment_status = 'PENDING' "
                "GROUP BY p.party_id, p.party_name, p.email",
                {"pid": party_id, "tid": tenant_id}
            )
            row = result.fetchone()
            if row and row[1]:
                subject = f"Payment Reminder - Pending: Rs{row[2]}"
                body = f"<h3>Payment Reminder</h3><p>Dear {row[0]},</p><p>Pending payment: Rs{row[2]}.</p>"
                return NotificationService.send_email(row[1], subject, body, tenant_id)
            return False

    @staticmethod
    def send_low_stock_alert(product_id: int, tenant_id: int) -> bool:
        with db_manager.get_session() as session:
            result = session.execute(
                "SELECT p.product_name, p.current_stock, p.reorder_level, t.email FROM products p "
                "JOIN tenants t ON p.tenant_id = t.tenant_id WHERE p.product_id = :pid AND p.tenant_id = :tid",
                {"pid": product_id, "tid": tenant_id}
            )
            row = result.fetchone()
            if row and row[3] and row[1] <= row[2]:
                subject = f"Low Stock Alert - {row[0]}"
                body = f"<h3>Low Stock Alert</h3><p>Product: {row[0]}</p><p>Stock: {row[1]}</p><p>Reorder: {row[2]}</p>"
                return NotificationService.send_email(row[3], subject, body, tenant_id)
            return False

    @staticmethod
    def _log_notification(tenant_id: int, type: str, recipient: str, subject: str, 
                         status: str, error: str = None):
        with db_manager.get_session() as session:
            session.execute(
                "INSERT INTO notification_logs (tenant_id, notification_type, recipient, subject, status, error_message, sent_at) "
                "VALUES (:tid, :type, :recip, :subj, :stat, :err, :now)",
                {"tid": tenant_id, "type": type, "recip": recipient, "subj": subject, "stat": status, "err": error, "now": datetime.now()}
            )
