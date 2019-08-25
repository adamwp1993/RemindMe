from flask import Flask, request
from RemindMeMain import IncomingMessage
from RemindMeMain import init_account
from twilio.rest import Client


# Init the account
# ======================================================================================================================

global twilio_bot_num
global client

init_account()


app = Flask(__name__)
# ======================================================================================================================


@app.route("/", methods=['GET', 'POST'])  # allows you to use GET and POST HTTP requests, defines the localhost path
def sms_receive():
    """Receives the message, enters it into the DB to be queued for reminder"""
    # start the response
    from_num = request.values.get('From')
    message_body = request.values.get('Body')
    incoming = IncomingMessage(str(message_body), str(from_num))
    incoming.test_output()
    # Build a response message
    resp_message = "Reminder will be sent within 5 minutes of " + IncomingMessage.reminder_time
    send_object = client.messages.create(
        body=resp_message,
        from_=twilio_bot_num,
        to=from_num,
    )
    return str(send_object)


@app.route("/homepage", methods=["GET", "POST"])
def hello():
    return "Hello World!"


if __name__ == "__main__":
    app.run(debug=True)


