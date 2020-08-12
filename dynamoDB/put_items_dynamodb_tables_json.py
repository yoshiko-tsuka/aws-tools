import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from common.logger import ColerdLog
from common.myconst import myconst as cst

if __name__ == "__main__":
    lg = ColerdLog.init_logger(__name__)
    lg.info('**** Put Items To DynamoDB Tables ****')
    session = boto3.Session(profile_name=cst.PROFILE_NAME)
    client = session.client('dynamodb', region_name=cst.REGION_NAME)
    table_names = client.list_tables()['TableNames']
    if table_names == []:
        lg.info('No tables')
    json_open = open('dynamoDB/config/put_items.json', 'r')
    json_data = json.load(json_open)
    for table in json_data['tables']:
        for item in table["Items"]:
            result = client.put_item(
                TableName=table["TableName"],
                Item=item
            )
        lg.info('Put ' + table["TableName"] + ' Items has been succeeded.')
    
    lg.info('**** End Delete All DynamoDB Tables ****')

