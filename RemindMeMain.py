#! python3
# README
# ======================================================================================================================
# How to set up the program:
# Path to VirtualEnvironment - C:\Users\adpeters\MyPyScripts\RemindMe
# Scripts\activate <- activate the virtual environment in Windows , it should show (RemindMe)
# run python FlaskRemindMe.py

# We will be using Ngrok to make the Flask server accessible from the internet
# C:\Users\adpeters\MyPyScripts\RemindMe\ngrok
# start ngrok while Flask server is running ngrok http 5000 -host-header="localhost:5000" -subdomain=remindme.ngrok.io
# From there, copy the ngrok URL, go to the twilio Page->the phone number, add the URL to the webhook

# TODO; future features
# ======================================================================================================================
# Recurring Reminders
# Clean init_account logic
# Finish Verify Phone number function
# Error Handling / bad input handling
# User Accounts/ Verified phone numbers
# Natural Language support - "RemindMe to go to the grocery store at 3pm today"
# Quick/stored Phone numbers - "Remind Laura to go to the grocery store at 4pm"

# Dependencies
# ======================================================================================================================
from twilio.rest import Client
from datetime import datetime
import time
import threading
import re
import sqlite3
import threading
import os

# Functions
# ======================================================================================================================

def init_account():
    """Attempt to retrieve twilio API account info from environmental vars, else set them."""
    # TODO: Clean up this logic, so instead of being forced to re-set all account info, when a none is found you
    # will only need to set that specific variable.
    account_sid = input("\n\nPlease enter your Twilio Account SID: ")
    auth_token = input("\n\nPlease enter your Twilio Auth Token: ")
    twilio_bot_num = input("\n\nPlease enter your Twilio Phone number, including Country and Area code: ")
    client = Client(account_sid, auth_token)


def set_account():
    """ Set the Twilio API info as environmental variables. """
    # set_account_sid = input("\n\nPlease enter your Twilio Account SID: ")
    # set_account_token = input("\n\nPlease enter your Twilio Auth Token: ")
    # set_account_num = input("\n\nPlease enter your Twilio Phone number, including Country and Area code: ")
    # os.environ["ACCOUNT_SID"] = set_account_sid
    # os.environ["ACCOUNT_TOKEN"] = set_account_token
    # os.environ["TWILIO_BOT_NUM"] = set_account_num



def create_table():
    """Creates a table if it does not exist already in the Database."""
    database = sqlite3.connect('remindMeDB', check_same_thread=False, timeout=10)
    cursor = database.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Message(
    message_ID INTEGER PRIMARY KEY, message_body TEXT NOT NULL, reminder_time TEXT NOT NULL, create_time TEXT NOT NULL,
    send_to_num TEXT NOT NULL, from_num TEXT NOT NULL );
    ''')
    database.commit()
    database.close()


def calculate_time_difference(time_to_remind):
    """Takes an input time, and finds the difference"""
    # This section for use in testing, when manually entering the time.
    # timeToRemind = input("Please enter the time you would like to be reminded in the following format: YYYYMMDD \
    # HH:MM\nPlease keep in mind that this uses the 24 hour scale.")

    # parse the time string into a datetime object(machine readable)
    parsed_time = datetime.strptime(time_to_remind, '%Y%m%d %H:%M')
    print(parsed_time)
    # print the difference between the reminder time and
    time_difference = parsed_time - datetime.now()
    print("Okay! we will remind you in " + str(time_difference))


def test_reminder_loop():
    """Standalone function for simple CLI loop for testing"""
    input("Would you like to send a message?")
    user_input_number = input("enter the phone number you would like to text:+12345678910")
    user_input_message = input("please enter the message to send")
    user_input_time = input("please enter the time")
    new_reminder = ReminderObject(user_input_time, user_input_message, user_input_number)
    new_reminder.send_reminder_text()


def query_db_all():
    """Simple test query that displays all entries in the DB."""
    run_loop = input("\n\nWould you like to query the DB? y/n\n")
    if run_loop == "y":
        database = sqlite3.connect('remindMeDB', check_same_thread=False, timeout=10)
        cursor = database.cursor()
        results = cursor.execute("""
                SELECT * 
                FROM message;
                
                """,).fetchall()
        print("\n\nQuery Results:\n")
        for row in results:
            print(row)
        database.commit()
        database.close()
    elif run_loop == "N" or run_loop == "n":
        return


def query_db_past():
    """Query the SQLite3 DB and display all rows with a Reminder Time in the past."""
    run_loop = input("Would you like to query the DB? y/n")
    if run_loop == "Y" or run_loop == "y":
        now = datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M")
        database = sqlite3.connect('remindMeDB', check_same_thread=False, timeout=10)
        cursor = database.cursor()
        results = cursor.execute("""
        SELECT * 
        FROM message
        WHERE reminder_time <= datetime(?);
        """, (now,)).fetchall()
        for row in results:
            print(row)
        database.commit()
        database.close()
    elif run_loop == "N" or run_loop == "n":
        return


def send_text_message(message, number):
    """ simple function to send a text message """
    client.messages.create(
        body=message,
        from_=twilio_bot_num,
        to=number,
    )


def get_thread_count():
    count = threading.active_count()
    print("\n\nThreads active: " + str(count))
    time.sleep(2)


def create_reminder_gui():
    """create a reminder and insert it into the DB from the client GUI (remindMeMain.py)"""
    try:
        time_input = input("\nPlease enter the time you would like to set a reminder in this format: yyyymmdd hh:mm")
        reminder_time = IncomingMessage.parse_time(time_input)
        message_body = input("\nEnter the Reminder message:\n")
        creation_time = datetime.now()
        send_to = input("\nEnter the number you would like to send to : +11234567890\n")
        # TODO: Add some logic here to make sure the phone number is correctly entered
        from_num = "Created from RemindMe! Server client"
        IncomingMessage.insert_row_db(message_body, reminder_time, creation_time, send_to, from_num)
        print("\n\nReminder Successfully added to the DB.")
        time.sleep(2)
    except:
        print("Input failed. try again.")
        time.sleep(1)

def verify_phone_number(phone_num):
    """Verify the input is a phone number, and returns as a boolean value."""
    phone_regex = re.compile(r'[+]/d/d{3} /d{3} /d{4}')


# Classes
# ======================================================================================================================

class MainController(threading.Thread):
    """the 'Main controller' - this is the Object that queries the database and sends the reminder message.
    """
    # Need to add logging here in the future
    # Possibly we could consider threading each message here, in stead of queueing them within the already threaded
    # MainController class. Since i am not expecting this to need to handle thousands of text messages per controller
    # thread, this is overkill for the current use case (personal use).
    results = ''
    queue = 0
    now = ""

    def run(self):
            MainController.results = MainController.query_db(self)
            MainController.remove_db_entries(self)
            right_now = datetime.now()
            MainController.now = right_now.strftime("%Y-%m-%d %H:%M")
            for row in MainController.results:
                message_var = """
                MESSAGE: {}
                
                created: {}
                sent by: {}
                """.format(row[1], row[3], row[5])
                send_text_message(message_var, row[4])

    def query_db(self):
        """Queries the Database, pulling all records with a reminder_time in the past. """
        database = sqlite3.connect('remindMeDB', check_same_thread=False, timeout=10)
        cursor = database.cursor()
        rows = cursor.execute("""
        SELECT * 
        FROM message
        WHERE reminder_time <= datetime(?);
        """, (MainController.now,)).fetchall()
        database.close()
        return rows

    def remove_db_entries(self):
        database = sqlite3.connect('remindMeDB', check_same_thread=False, timeout=10)
        cursor = database.cursor()
        cursor.execute("""
        DELETE
        FROM
        message
        WHERE reminder_time <= datetime(?);
        """, (MainController.now,)).fetchall()
        database.commit()
        database.close()


class IncomingMessage:
    """Creates a Parsed message and stores in the DB"""
    raw_message_body = ""
    reminder_time = datetime.now()
    raw_time = 0
    send_to_num = ""
    formatted_message_body = ""
    from_number = 0
    creation_time = ""

    def __init__(self, input_message, input_num):
        """Construct the incoming message for database storage"""
        IncomingMessage.raw_message_body = input_message
        IncomingMessage.parse_message_body(self)
        IncomingMessage.reminder_time = IncomingMessage.parse_time(IncomingMessage.raw_time)
        IncomingMessage.from_number = input_num
        IncomingMessage.creation_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        IncomingMessage.insert_row_db(IncomingMessage.formatted_message_body, IncomingMessage.reminder_time,  \
                                      IncomingMessage.creation_time, IncomingMessage.send_to_num, \
                                      IncomingMessage.from_number)
        IncomingMessage.test_output(self)

    def parse_message_body(self):
        """Parses the message body.
        Needs Error handling for bad input"""
        result = re.search('MESSAGE:(.*)TIME:(.*)TO:(.*)', IncomingMessage.raw_message_body)
        IncomingMessage.formatted_message_body = result.group(1).strip()
        IncomingMessage.raw_time = result.group(2).strip()
        IncomingMessage.send_to_num = result.group(3).strip()
        # TODO: Add logic here to make sure a send-to number is correctly formatted

    @staticmethod
    def parse_time(raw_time):
        """Parses the time into a datetime object that we can store in the database.
        static method for use in other places (GUI reminder creation)"""
        date_time_obj = datetime.strptime(raw_time, "%Y%m%d %H:%M")
        reminder_time = date_time_obj.strftime("%Y-%m-%d %H:%M")
        return reminder_time

    @staticmethod
    def insert_row_db(formatted_message_body, reminder_time, creation_time, send_to_num, from_number):
        """Inserts the data into the DB for storage. Static method for use in other places.(GUI reminder creation)"""
        database = sqlite3.connect('remindMeDB', check_same_thread=False, timeout=10)
        cursor = database.cursor()
        insert_tuple = (formatted_message_body, reminder_time, creation_time, send_to_num, from_number)
        cursor.execute("""
        INSERT INTO message ( 
        message_body, reminder_time, create_time, send_to_num, from_num 
        )
        VALUES (
        ?,?,?,?,?
        );
        """, insert_tuple)
        database.commit()
        database.close()


    def test_output(self):
        """Test the output"""
        print(IncomingMessage.formatted_message_body)
        print(IncomingMessage.reminder_time)
        print(IncomingMessage.send_to_num)


class UserInterface(threading.Thread):
    """Creates the Command Line UI thread, so user may interact with program while is is executing the main control"""
    program_flag = True

    def run(self):
        while UserInterface.program_flag:
            loop_message = """
            OPTIONS:
            1. query DB for queued messages
            2. set reminder
            3. Configure settings
            4. get concurrent threads
            5. quit"""
            print(openingMsg)
            answer = input(loop_message)
            options = {
                "1": query_db_all,
                "2": create_reminder_gui,
                # "3": settings here - change DB query times, delete recurring reminders
                "4": get_thread_count,
                "5": quit

            }
            try:
                options[answer]()
            except:
                print("invalid input, try again.")


# Main Loop / execution
# ======================================================================================================================

if __name__ == '__main__':
    global twilio_bot_num
    global client
    global opening_msg
    display_now = datetime.now()
    init_account()
    openingMsg = """
    
     _______                           __                  __  __       __            __ 
    /       \                         /  |                /  |/  \     /  |          /  |
    $$$$$$$  |  ______   _____  ____  $$/  _______    ____$$ |$$  \   /$$ |  ______  $$ |
    $$ |__$$ | /      \ /     \/    \ /  |/       \  /    $$ |$$$  \ /$$$ | /      \ $$ |
    $$    $$< /$$$$$$  |$$$$$$ $$$$  |$$ |$$$$$$$  |/$$$$$$$ |$$$$  /$$$$ |/$$$$$$  |$$ |
    $$$$$$$  |$$    $$ |$$ | $$ | $$ |$$ |$$ |  $$ |$$ |  $$ |$$ $$ $$/$$ |$$    $$ |$$/ 
    $$ |  $$ |$$$$$$$$/ $$ | $$ | $$ |$$ |$$ |  $$ |$$ \__$$ |$$ |$$$/ $$ |$$$$$$$$/  __ 
    $$ |  $$ |$$       |$$ | $$ | $$ |$$ |$$ |  $$ |$$    $$ |$$ | $/  $$ |$$       |/  |
    $$/   $$/  $$$$$$$/ $$/  $$/  $$/ $$/ $$/   $$/  $$$$$$$/ $$/      $$/  $$$$$$$/ $$/ 
    
    Adam Petersen, 2019
    Server Client version 1.0
    {}                                                               
    """.format(display_now)
    create_table()
    ui_thread = UserInterface()
    ui_thread.start()
    while ui_thread.program_flag:
            main_thread = MainController()
            main_thread.start()
            time.sleep(30)







