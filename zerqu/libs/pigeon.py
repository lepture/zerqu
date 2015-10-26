
from flask import current_app
from flask_mail import Mail, Message

mail = Mail()


def send_text(email, title, content):
    msg = Message(title, recipients=[email])
    msg.body = content
    if current_app.debug:
        current_app.logger.info(msg.body)
    else:
        mail.send(msg)


def send_html(email, title, content):
    msg = Message(title, recipients=[email])
    msg.html = content
    mail.send(msg)
