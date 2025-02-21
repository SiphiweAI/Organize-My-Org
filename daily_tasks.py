import datetime
import schedule
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Member, Event
from twilio.rest import Client

# Database setup
DATABASE_URL = "sqlite:///church.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Twilio setup
TWILIO_ACCOUNT_SID = 'account_sid'
TWILIO_AUTH_TOKEN = 'auth_token'
TWILIO_WHATSAPP_NUMBER = 'whatsapp:+twilio_whatsapp_number'
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def send_whatsapp_message(to_number, message):
    for message in message:
        for phone_number in to_number:
            try:
                client.messages.create(
                    body=message,
                    from_=TWILIO_WHATSAPP_NUMBER,
                    to=f'whatsapp:{phone_number}'
                )
            except Exception as e:
                raise(f"Failed to send message to {to_number}: {e}")

def send_reminders():
    today = datetime.date.today()
    upcoming_events = session.query(Event).filter(
        Event.event_date == today + datetime.timedelta(days=5)
    ).all()

    for event in upcoming_events:
        reminder_message = f"Reminder: The event '{event.name}' is scheduled for {event.event_date} at {event.start_time}."
        # Here you might send this message to all members
        return reminder_message
    phone_numbs = session.query(Member.phone_number).all()  # returns a tuple of all the phone numbers
    phone_numbers = [number[0] for number in phone_numbs]  # convert the result (tuple) to a list of phone numbers
    send_whatsapp_message(phone_numbers, reminder_message)


def send_birthday_messages():
    today = datetime.date.today()
    members_with_birthday_today = session.query(Member).filter(
        Member.date_of_birth.has(
            datetime.date(year=today.year, month=Member.date_of_birth.month, day=Member.date_of_birth.day)
        )
    ).all()

    for member in members_with_birthday_today:
        birthday_message = f"Happy Birthday {member.first_name} {member.last_name}!"
        send_whatsapp_message(member.phone_number, birthday_message)

# Scheduling tasks
def schedule_tasks():
    schedule.every().day.at("08:00").do(send_reminders)
    schedule.every().day.at("08:00").do(send_birthday_messages)

if __name__ == "__main__":
    schedule_tasks()
    while True:
        schedule.run_pending()
        time.sleep(60)  # Wait a minute before checking again
