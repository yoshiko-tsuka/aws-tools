'''
# ************************************************* #
  Function : Sending thanks mails.
  Argument example :
{
  "recipient": "44534453yoshiko@gmail.com",
  "content": {
      "name": "山田 太郎",
      "nameFurigana": "ヤマダ タロウ",
      "age": 25,
      "prefecture": "北海道",
      "phone": "123-4567-8900"
  }
}
# ************************************************* #
'''

import json
import os
import sys
import boto3
# multipart: 添付ファイルを送信する時に必要
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.header import Header

CHARSET = "UTF-8"
client = boto3.client('ses', region_name="ap-northeast-1")
SENDER = "44534453yoshiko@gmail.com"
nl = '\n'

def _sendMail(RECIPIENT, SUBJECT, BODY_HTML=None, ATTACHMENT=None):
    response = client.send_email(
        Source=SENDER,
        Destination={
            'ToAddresses': [
                RECIPIENT,
            ]
        },
        Message={
            'Subject': {
                'Charset': CHARSET,
                'Data': SUBJECT,
            },
            'Body': {
                'Html': {
                    'Charset': CHARSET,
                    'Data': BODY_HTML,
                },
            }
        }
    )

    return response

def __getHtmlBody(recipient, content):
    html_body = f"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style type="text/css">
        body {{
		font-family: 'Hiragino Kaku Gothic ProN','Meiryo',sans-serif;
		color:#222222;
		text-align: center;
		margin:0;
        padding:0;
        -ms-text-size-adjust: 100%;
        -webkit-text-size-adjust: 100%;
    	}}
        table {{
            border-spacing: 0;
        }}
    	table, td {{
    		border-collapse: collapse;
    		mso-table-lspace: 0;
    		mso-table-rspace: 0;
    	}}
    	img {{
    	  outline: none;
    	  border: none;
    	  text-decoration: none;
    	}}
    	a img {{
    	  border: none;
    	}}
    	.visible-xs-block{{
    				display: none !important;
    	}}
        .align-right{{
                    text-align: right;
        }}
        .w-th{{
            width: 200px;
        }}
        .w-space{{
            width: 200px;
        }}
        .w-price{{
            width: 200px;
        }}
        @media only screen and (max-width: 768px) {{
			.base {{
				width: 100% !important;
				min-width: 100% !important;
			}}
			td.responsive {{
				width: 100% !important;
				padding-left: 8px !important;
				padding-right: 8px !important;
				box-sizing: border-box !important;
				display: block !important;
			}}
			img {{
				/*width: 100% !important;*/
				max-width: 100% !important;
				height: auto !important;
			}}
			.visible-xs-block{{
				display: block !important;
			}}
			.hidden-xs{{
				display:none;
			}}
            .align-right{{
                text-align: left;
            }}
            .w-space{{
                width: 20%;
            }}
            .w-th{{
                width: 50%;
            }}
            .w-price{{
                width: 30%;
            }}
    	}}

        </style>
        </head>
        <body style='margin:0; padding:0;'>
        <table width='600' border='0' align='center' cellpadding='0' cellspacing='0' bgcolor='#fff' class='base'>
          <tr>
            <td>
                <table width='100%' border='0' cellpadding='10' cellspacing='0' bgcolor='#ffffff'>
                  <tbody>
                      <tr>
                        <td class='responsive' valign='top' align='left'><font color='#222222' style='font-size: 15px; line-height:1.7; '>
                        { content['name'] } 様<br /><br />
                        お問い合わせありがとうございます。＊お問い合わせ内容：年齢「{ content['age'] }」, 都道府県「{ content['prefecture'] }」, 電話番号「{ content['phone'] }」</font></td>
                      </tr>
                      <tr>
                        <td class='responsive' valign='top' align='left'><font color='#222222' style='font-size:15px; line-height:1.7; '>
                        なお、48時間以内に担当者からお電話、またはメールでの連絡がない場合、ご入力いただいた内容に誤りがあるか、システムにエラーが発生している可能性がございます。下記のお問合せ先までご連絡いただきますようお願いいたします。</font></td>
                      </tr>
                  </tbody>
              </table>
            </td>
          </tr>
        </table>
        </body>
        </body>
    </html>
    """
    return html_body

def lambda_handler(event, context):
    recipient_user = event['recipient']
    subject = f"{event['content']['name']} 様 見積書の送付と留学カウンセリング仮予約完了のお知らせ【ワールドアベニュー】"
    html_body = __getHtmlBody(recipient_user, event['content'])
    # print(html_body)
    _sendMail(recipient_user, subject, html_body, None)