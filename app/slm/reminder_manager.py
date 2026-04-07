from datetime import datetime, timedelta
from typing import List, Dict
import json
from pathlib import Path

class ReminderManager:
    """Manage reminders with date/time"""
    
    def __init__(self):
        self.reminders_file = Path("data/reminders.json")
        self.reminders = self.load_reminders()
    
    def create_reminder(self, user_message: str, reminder_text: str, reminder_date: datetime) -> Dict:
        """Create a new reminder"""
        
        reminder = {
            "id": len(self.reminders) + 1,
            "created_at": datetime.now().isoformat(),
            "reminder_text": reminder_text,
            "reminder_date": reminder_date.isoformat(),
            "status": "active",  # active, sent, cancelled
            "user_message": user_message
        }
        
        self.reminders.append(reminder)
        self.save_reminders()
        
        return reminder
    
    def get_due_reminders(self) -> List[Dict]:
        """Get reminders that are due now"""
        
        now = datetime.now()
        due = []
        
        for reminder in self.reminders:
            if reminder["status"] != "active":
                continue
            
            reminder_date = datetime.fromisoformat(reminder["reminder_date"])
            
            # Check if reminder is due (within 1 hour window)
            if now >= reminder_date and now <= reminder_date + timedelta(hours=1):
                due.append(reminder)
        
        return due
    
    def mark_as_sent(self, reminder_id: int):
        """Mark reminder as sent"""
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["status"] = "sent"
        self.save_reminders()
    
    def save_reminders(self):
        """Save reminders to JSON file"""
        self.reminders_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.reminders_file, "w") as f:
            json.dump(self.reminders, f, indent=2)
    
    def load_reminders(self) -> List[Dict]:
        """Load reminders from JSON file"""
        if not self.reminders_file.exists():
            return []
        
        with open(self.reminders_file, "r") as f:
            return json.load(f)