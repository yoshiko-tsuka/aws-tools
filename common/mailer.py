import json
import os
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header

def _sendMail(RECIPIENT, SUBJECT, BODY_HTML=None, BODY_TEXT=None, ATTACHMENT=None):
    # Create a multipart/mixed parent container.
    msg = MIMEMultipart('mixed')
    # Add subject, from and to lines.
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = ', '.join(RECIPIENT) if type(RECIPIENT) is list else RECIPIENT

    # Create a multipart/alternative child container.
    msg_body = MIMEMultipart('alternative')

    # Set html body.
    if BODY_HTML is not None:
        # The HTML body of the email.
        htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
        msg_body.attach(htmlpart)
    # Set text body.
    if BODY_TEXT is not None:
        # The email body for recipients with non-HTML email clients.
        textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
        msg_body.attach(textpart)

    # Attach the multipart/alternative child container to the multipart/mixed
    # parent container.
    msg.attach(msg_body)

    # Send the email.
    # Provide the contents of the email.
    DESTINATIONS = RECIPIENT if type(RECIPIENT) is list else [RECIPIENT]
    response = CLIENT.send_raw_email(
        Source=SENDER,
        Destinations=DESTINATIONS,
        RawMessage={
            'Data': msg.as_string(),
        }
    )

    return response
