import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import os

class EmailSender:
    """Send email notifications for reminders"""
    
    def __init__(self):
        # Email configuration (use environment variables)
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("EMAIL_USER", "your-email@gmail.com")
        self.sender_password = os.getenv("EMAIL_PASSWORD", "your-app-password")
    
    def send_reminder_email(self, recipient_email: str, reminder: Dict) -> bool:
        """Send reminder email"""
        
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"⏰ Reminder: {reminder['reminder_text']}"
            message["From"] = self.sender_email
            message["To"] = recipient_email
            
            # Email body
            text = f"""
Hello!

This is your reminder from Second Brain:

📌 {reminder['reminder_text']}

Created on: {reminder['created_at']}
Reminder date: {reminder['reminder_date']}

---
Second Brain - Your AI Knowledge Assistant
            """
            
            html = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #667eea;">⏰ Reminder from Second Brain</h2>
                    <p><strong>📌 {reminder['reminder_text']}</strong></p>
                    <p style="color: #666;">
                        Created: {reminder['created_at']}<br>
                        Reminder Date: {reminder['reminder_date']}
                    </p>
                    <hr>
                    <p style="color: #999; font-size: 12px;">
                        Second Brain - Your AI Knowledge Assistant
                    </p>
                </body>
            </html>
            """
            
            part1 = MIMEText(text, "plain")
            part2 = MIMEText(html, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipient_email, message.as_string())
            
            print(f"✅ Reminder email sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False