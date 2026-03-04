"""
Simple email service for transactional emails.
Uses SMTP — works with Gmail, SendGrid, Mailgun etc.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html: str) -> bool:
    """Send an HTML email. Returns True on success."""
    if not settings.SMTP_USER:
        logger.warning(f"Email not configured — skipping send to {to}: {subject}")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.FROM_EMAIL
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.FROM_EMAIL, to, msg.as_string())
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


def send_welcome_email(to: str, company_name: str, slug: str, admin_email: str):
    subject = f"Welcome to Syyaim EIQ — {company_name} is live!"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #1E5FA8; padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Syyaim EIQ ERP</h1>
        </div>
        <div style="padding: 30px; background: #f9f9f9;">
            <h2>Welcome, {company_name}! 🎉</h2>
            <p>Your ERP is ready. Here's how to get started:</p>

            <div style="background: white; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <p><strong>Your ERP URL:</strong><br>
                <a href="https://{slug}.syyaimeiq.com" style="color: #1E5FA8;">
                    https://{slug}.syyaimeiq.com
                </a></p>
                <p><strong>Admin Login:</strong> {admin_email}</p>
                <p><strong>Trial:</strong> 14 days free — no credit card needed</p>
            </div>

            <p>Your AI agents are already active:</p>
            <ul>
                <li>🤖 Lead Scoring — scores every new lead automatically</li>
                <li>✅ PR Approval — reviews purchase requisitions for policy compliance</li>
                <li>📦 MRP Planning — forecasts stock and raises PRs automatically</li>
                <li>💰 Payroll Audit — flags anomalies before you process payroll</li>
                <li>📊 Financial Insights — weekly P&L commentary</li>
            </ul>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://{slug}.syyaimeiq.com"
                   style="background: #1E5FA8; color: white; padding: 14px 28px;
                          border-radius: 6px; text-decoration: none; font-size: 16px;">
                    Open Your ERP →
                </a>
            </div>

            <p style="color: #666; font-size: 14px;">
                Need help? Reply to this email or WhatsApp us at +91-XXXXXXXXXX
            </p>
        </div>
    </div>
    """
    send_email(to, subject, html)


def send_trial_expiry_warning(to: str, company_name: str, slug: str, days_left: int):
    subject = f"Your Syyaim EIQ trial ends in {days_left} days"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #f59e0b; padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Trial Ending Soon</h1>
        </div>
        <div style="padding: 30px;">
            <h2>Hi {company_name},</h2>
            <p>Your free trial ends in <strong>{days_left} days</strong>.</p>
            <p>Subscribe now to keep your data and continue using all AI agents.</p>
            <p><strong>Growth Plan: ₹12,999/month</strong></p>
            <ul>
                <li>Unlimited users (up to 25)</li>
                <li>All modules — CRM, Purchase, Inventory, HR, Finance</li>
                <li>2,500 AI agent actions/month</li>
                <li>Priority support</li>
            </ul>
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://{slug}.syyaimeiq.com/billing"
                   style="background: #1E5FA8; color: white; padding: 14px 28px;
                          border-radius: 6px; text-decoration: none;">
                    Subscribe Now →
                </a>
            </div>
        </div>
    </div>
    """
    send_email(to, subject, html)


def send_payment_failed_email(to: str, company_name: str):
    subject = "Action required — Payment failed for Syyaim EIQ"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #ef4444; padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0;">Payment Failed</h1>
        </div>
        <div style="padding: 30px;">
            <h2>Hi {company_name},</h2>
            <p>We couldn't process your payment for Syyaim EIQ.</p>
            <p>Please update your payment method to avoid service interruption.</p>
            <div style="text-align: center; margin: 30px 0;">
                <a href="https://app.syyaimeiq.com/billing"
                   style="background: #ef4444; color: white; padding: 14px 28px;
                          border-radius: 6px; text-decoration: none;">
                    Update Payment Method →
                </a>
            </div>
        </div>
    </div>
    """
    send_email(to, subject, html)
