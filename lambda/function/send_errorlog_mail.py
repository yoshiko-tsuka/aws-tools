'''
# ************************************************* #
  Function : Sending an error log mail.
  Argument example :
{
  "recipient": "redmine@world-avenue.com.au",
  "subject": "`コースデータ更新失敗 school: テストスクール16-テストキャンパス16, courseId:テストスクール16-テストキャンパス16_観光_ワーキングホリデー_学生_メルボルン_m_general-english_イブニング_フルタイム_25_19",
  "params": {
	"Item": {
		"courseId": "テストスクール16-テストキャンパス16_観光_ワーキングホリデー_学生_メルボルン_m_general-english_イブニング_フルタイム_25_19",
		"course": "General English",
		"type": "M",
		"visaSt": "T",
		"visaWh": "F",
		"visaTo": "F",
		"country": "オーストラリア",
		"area": "メルボルン",
		"school": "テストスクール16-テストキャンパス16",
		"school_url": "https://www.world-avenue.co.jp/schoolinfo/mit-institute",
		"comissionRate": 30,
		"commisionPrice": 0,
		"timetableTime": "イブニング",
		"timetableType": "フルタイム",
		"timetable": 25,
		"weeks": 19,
		"fees": {
			"basic": {
				"enrolment": 250,
				"material": 190,
				"tuitionTotal": 1550
			},
			"promotion": {
				"enrolment": 250,
				"material": 190,
				"tuitionTotal": 1350,
				"discount": 120
			},
			"validDate": "2020/12/31",
			"paymentDate": "2020/12/31",
			"mustStart": "2020/12/31"
		}
	}
  },
  "exceptionInfo": {
      "errorType": "ProvisionedThroughputExceededException",
      "errorMessage": "An error occurred (ProvisionedThroughputExceededException) when calling the PutItem operation (reached max retries: 9): The level of configured provisioned throughput for the table was exceeded. Consider increasing your provisioning level with the UpdateTable API.",
      "caller": "run",
      "stackTrace": "Traceback (most recent call last):
         File "/opt/python/src/models/dynamodb/layer_base_table.py", line 55, in _createItem
           response = table.put_item(
         File "/var/runtime/boto3/resources/factory.py", line 520, in do_action
           response = action(self, *args, **kwargs)
         File "/var/runtime/boto3/resources/action.py", line 83, in __call__
           response = getattr(parent.meta.client, operation_name)(**params)
         File "/var/runtime/botocore/client.py", line 316, in _api_call
           return self._make_api_call(operation_name, kwargs)
         File "/var/runtime/botocore/client.py", line 626, in _make_api_call
           raise error_class(parsed_response, operation_name)
        botocore.errorfactory.ProvisionedThroughputExceededException: An error occurred (ProvisionedThroughputExceededException) when calling the PutItem operation (reached max retries: 9): The level of configured provisioned throughput for the table was exceeded. Consider increasing your provisioning level with the UpdateTable API."
  }
}

  How to execute on local:
  1. Launch a mail server
    docker run --rm -it -e DEFAULT_REGION="ap-northeast-1" -e SERVICES="ses" -p 4567-4582:4567-4582 -p 8080:8080 localstack/localstack
  2. Execute this function
    docker run --rm -e DOCKER_LAMBDA_DEBUG=1 -p 9001:9001 -v "$PWD":/var/task lambci/lambda:python3.8 src.function.send_errorlog_mail.lambda_handler '{"params": {"recipient": "koki.nakamura22@gmail.com", ...}'
# ************************************************* #
'''

import json
from src.layer.mailer.mailer import sendTextMail
from src.layer.common import myconst


def lambda_handler(event, context):
    recipient = event['recipient']
    subject = event['subject']
    exception_info = event['exceptionInfo']
    text_body = f'''実行時パラメータ: {event['params']}
    呼び出し元: {event['caller']}\n
    エラー種類: {exception_info['errorType']}\n
    エラーメッセージ: {exception_info['errorMessage']}\n
    スタックトレース: {exception_info['stackTrace']}\n
    '''
    attachment = event['attachment'] if 'attachment' in event else None
    sendTextMail(recipient, subject, text_body, attachment)
