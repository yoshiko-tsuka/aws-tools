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
    lg.info('**** Delete All DynamoDB Tables ****')
    session = boto3.Session(profile_name=cst.PROFILE_NAME)
    client = session.client('dynamodb', region_name=cst.REGION_NAME)
    table_names = client.list_tables()['TableNames']
    if table_names == []:
        lg.info('No tables')
    for table_name in table_names:
            client.delete_table(TableName=table_name)
            client.get_waiter('table_not_exists').wait(TableName=table_name)
            lg.info(table_name + ' has been deleted.')
    
    lg.info('**** End Delete All DynamoDB Tables ****')

