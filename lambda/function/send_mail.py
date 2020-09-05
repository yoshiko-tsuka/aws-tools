'''
# ************************************************* #
  Function : Sending any kind of mail.
  Argument example :
{
  "mailType": "Thanks",
  "recipient": "testuser@test.com"
}
# ************************************************* #
'''

import inspect
import json
import sys
import traceback
import boto3
from src.layer.common import myconst, lambda_to_lambda
from src.layer.common.environment import isDev, isSt


def lambda_handler(event, context):
    try:
        mail_type = event['mailType']
        if mail_type == myconst.cst.THANKS_MAIL:
            # Thanksメール
            response = lambda_to_lambda.executeLambdaSync(
                'send_thanks_mail', event)
        elif mail_type == myconst.cst.TABLE_UPDATE_FAILED_MAIL:
            # Table update failed mail
            subject = f"【テーブル更新失敗】{event['subject']}"
            response = __sendErrorMail(
                event['recipient'], subject, event['caller'], event['params'], event['exceptionInfo'])
        elif mail_type == myconst.cst.CSV_READ_FAILED_MAIL:
            # CSV read failed mail
            subject = f"【CSV読み込み失敗】{event['subject']}"
            response = __sendErrorMail(
                event['recipient'], subject, event['caller'], event['params'], event['exceptionInfo'])
        elif mail_type == myconst.cst.OTHER_ERROR_MAIL:
            # Other error mail
            response = __sendErrorMail(
                event['recipient'], event['subject'], event['caller'], event['params'], event['exceptionInfo'])
        else:
            raise ValueError("mailType is invalid.")
    except Exception as e:
        # Setting error information for sending an error mail.
        response = {
            "errorMessage": str(e),
            "errorType": type(e).__name__,
            "stackTrace": traceback.format_exc()
        }

    # If the content of the response exists and has an error message, it's determined that the processing has failed.
    # Because when the processing is succeeded, the content of the response is empty.
    if response is not None:
        if 'errorMessage' in response:
            __sendErrorMail(myconst.cst.SYSTEM_MAIL_ADDRESS,
                            'SESからのメール送信失敗', inspect.stack()[1][3], event, response)


# Sending the error message.
def __sendErrorMail(recipient, subject, caller, params, exceptionInfo):
    # formated_subject
    if isDev():
        formated_subject = f"【開発】{subject}"
    elif isSt():
        formated_subject = f"【テスト】{subject}"
    else:
        formated_subject = subject
    return lambda_to_lambda.executeLambdaSync('send_errorlog_mail', {
        "recipient": recipient,
        "subject": formated_subject,
        "caller": caller,
        "params": params,
        "exceptionInfo": exceptionInfo
    })
