import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from base_dynamodb_tables import BaseDynamo

class PutItems(BaseDynamo):
    def __init__(self):
        super().__init__(__file__)

if __name__ == "__main__":
    tb = PutItems()
    json_open = open('dynamoDB/config/put_items.json', 'r')
    json_data = json.load(json_open)
    for table in json_data['tables']:
        if table["TableName"] in tb.table_names:
            for item in table["Items"]:
                result = tb.client.put_item(
                    TableName=table["TableName"],
                    Item=item
                )
            tb.lg.info('Put ' + table["TableName"] + ' Items has been succeeded.')
        else:
            tb.lg.info(table["TableName"] + ' does not exist.')
    
    tb.end()

