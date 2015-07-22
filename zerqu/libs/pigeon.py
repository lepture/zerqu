"""
    Sending mails with Pigeon
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Pigeon is a service for sending mails over HTTP.

    https://github.com/lepture/pigeon
"""

from flask_mail import Mail, Message

mail = Mail()


def send_text(email, title, content):
    msg = Message(title, recipients=[email])
    msg.body = content
    mail.send(msg)
