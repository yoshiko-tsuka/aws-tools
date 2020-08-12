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
    lg.info('**** Create DynamoDB Tables ****')
    session = boto3.Session(profile_name=cst.PROFILE_NAME)
    client = session.client('dynamodb', region_name=cst.REGION_NAME)
    table_names = client.list_tables()['TableNames']
    if table_names == []:
        lg.info('No tables')
    json_open = open('dynamoDB/config/create_tables.json', 'r')
    json_data = json.load(json_open)
    for table in json_data['tables']:
        if "LocalSecondaryIndexes" in table:
            result = client.create_table(
                TableName=table["TableName"],
                AttributeDefinitions=table["AttributeDefinitions"],
                KeySchema=table["KeySchema"],
                LocalSecondaryIndexes=table["LocalSecondaryIndexes"],
                ProvisionedThroughput=table["ProvisionedThroughput"]
            )
        else:
            result = client.create_table(
                TableName=table["TableName"],
                AttributeDefinitions=table["AttributeDefinitions"],
                KeySchema=table["KeySchema"],
                ProvisionedThroughput=table["ProvisionedThroughput"]
            )
        client.get_waiter('table_exists').wait(TableName=table["TableName"])
        lg.info(table["TableName"] + ' has been created.')
    
    lg.info('**** End Create DynamoDB Tables ****')

