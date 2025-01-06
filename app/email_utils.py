from flask_mail import Message
from __init__ import mail


def send_email(subject, recipient, body):
    """
    Sends an email using Flask-Mail.
    :param subject: Subject of the email
    :param recipient: Recipient's email address
    :param body: Email body content
    :return: True if email sent successfully, False otherwise
    """
    try:
        print(f"[DEBUG] Preparing to send email to {recipient} with subject: '{subject}'...")

        # Create the email message
        msg = Message(
            subject=subject,
            recipients=[recipient],
            body=body
        )
        print("[DEBUG] Email message created successfully.")

        # Send the email
        print("[DEBUG] Sending email...")
        mail.send(msg)
        print(f"[DEBUG] Email sent successfully to {recipient}.")
        return True
    except Exception as e:
        print(f"[ERROR] Error sending email: {e}")
        return False
