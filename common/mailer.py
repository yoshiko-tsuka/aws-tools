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
SENDER = cst.SENDER_MAIL_ADDRESS

class Mailer:
    def sendHtmlMail(RECIPIENT, SUBJECT: str, BODY_HTML: str, ATTACHMENT=None):
        return return _sendMail(RECIPIENT=RECIPIENT, SUBJECT=SUBJECT, BODY_HTML=BODY_HTML, ATTACHMENT=ATTACHMENT)
    
    def sendTextMail(RECIPIENT, SUBJECT: str, BODY_TEXT: str, ATTACHMENT=None):
        return _sendMail(RECIPIENT=RECIPIENT, SUBJECT=SUBJECT, BODY_TEXT=BODY_TEXT, ATTACHMENT=ATTACHMENT)

    def _sendMail(RECIPIENT, SUBJECT, BODY_HTML=None, BODY_TEXT=None, ATTACHMENT=None):
        msg = {}
        msg['Body'] = {}

        if BODY_HTML is not None:
            msg['Body']['Html']['Charset'] = CHARSET
            msg['Body']['Html']['Data'] = BODY_HTML.encode(CHARSET)
            
        if BODY_TEXT is not None:
            msg['Body']['Text']['Charset'] = CHARSET
            msg['Body']['Text']['Data'] = BODY_TEXT.encode(CHARSET)

        msg['Subject']['Charset'] = SUBJECT
        msg['Subject']['Data'] = SUBJECT

        DESTINATIONS['ToAddresses'] = RECIPIENT
        response = CLIENT.send_email(
            Source=SENDER,
            Destinations=DESTINATIONS,
            Message=msg
        )

        return response
