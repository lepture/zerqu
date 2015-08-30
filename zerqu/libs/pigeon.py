
from flask_mail import Mail, Message

mail = Mail()


def send_text(email, title, content):
    msg = Message(title, recipients=[email])
    msg.body = content
    mail.send(msg)


def send_html(email, title, content):
    msg = Message(title, recipients=[email])
    msg.html = content
    mail.send(msg)
