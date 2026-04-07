from apscheduler.schedulers.background import BackgroundScheduler
from app.slm.reminder_manager import ReminderManager
from app.notifications.email_sender import EmailSender
import os

def check_and_send_reminders():
    """Check for due reminders and send emails"""
    
    print("🔔 Checking for due reminders...")
    
    reminder_manager = ReminderManager()
    email_sender = EmailSender()
    
    due_reminders = reminder_manager.get_due_reminders()
    
    if not due_reminders:
        print("   No reminders due")
        return
    
    recipient_email = os.getenv("USER_EMAIL", "user@example.com")
    
    for reminder in due_reminders:
        print(f"   Sending reminder: {reminder['reminder_text']}")
        
        success = email_sender.send_reminder_email(recipient_email, reminder)
        
        if success:
            reminder_manager.mark_as_sent(reminder["id"])

def start_reminder_scheduler():
    """Start background scheduler to check reminders every hour"""
    
    scheduler = BackgroundScheduler()
    
    # Check every hour
    scheduler.add_job(check_and_send_reminders, 'interval', hours=1)
    
    scheduler.start()
    print("✅ Reminder scheduler started (checks every hour)")