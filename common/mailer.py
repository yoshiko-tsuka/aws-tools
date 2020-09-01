import json
import os
import sys
from myconst import myconst as cst
import boto3
# multipart: 添付ファイルを送信する時に必要
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header

CHARSET = "UTF-8"
SESSION = boto3.Session(profile_name=cst.PROFILE_NAME)
CLIENT = SESSION.client('ses', region_name=cst.REGION_NAME)
SENDER_NAME = Header(f"{environment_identifier}ワールドアベニュー".encode(
        'iso-2022-jp'), 'iso-2022-jp').encode()
SENDER = '{SENDER_NAME} <{cst.SENDER_MAIL_ADDRESS}>'

class Mailer:
    def sendHtmlMail(RECIPIENT, SUBJECT: str, BODY_HTML: str, ATTACHMENT=None):
        return return _sendMail(RECIPIENT=RECIPIENT, SUBJECT=SUBJECT, BODY_HTML=BODY_HTML, ATTACHMENT=ATTACHMENT)
    
    def sendTextMail(RECIPIENT, SUBJECT: str, BODY_TEXT: str, ATTACHMENT=None):
        return _sendMail(RECIPIENT=RECIPIENT, SUBJECT=SUBJECT, BODY_TEXT=BODY_TEXT, ATTACHMENT=ATTACHMENT)

    def _sendMail(RECIPIENT, SUBJECT, BODY_HTML=None, BODY_TEXT=None, ATTACHMENT=None):
        # header はmixed
        msg = MIMEMultipart('mixed')
        # Add subject, from and to lines.
        msg['Subject'] = SUBJECT
        msg['From'] = cst.SENDER
        msg['To'] = ', '.join(RECIPIENT) if type(RECIPIENT) is list else RECIPIENT

        # body はalternative
        msg_body = MIMEMultipart('alternative')

        if BODY_HTML is not None:
            html = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
            msg_body.attach(html)
            
        if BODY_TEXT is not None:
            text = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
            msg_body.attach(text)

        msg.attach(msg_body)

        DESTINATIONS = RECIPIENT if type(RECIPIENT) is list else [RECIPIENT]
        response = CLIENT.send_raw_email(
            Source=SENDER,
            Destinations=DESTINATIONS,
            RawMessage={
                'Data': msg.as_string(),
            }
        )

        return response
