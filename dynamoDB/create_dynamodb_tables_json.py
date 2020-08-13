import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from base_dynamodb_tables import BaseDynamo

class CreateTables(BaseDynamo):
    def __init__(self):
        super().__init__(__file__)

if __name__ == "__main__":
    tb = CreateTables()
    if tb.table_names == []:
        tb.lg.info('No tables')
    json_open = open('dynamoDB/config/create_tables.json', 'r')
    json_data = json.load(json_open)
    for table in json_data['tables']:
        if table["TableName"] in tb.table_names:
            tb.lg.info(table["TableName"] + ' exists.')
            continue
        if "LocalSecondaryIndexes" in table:
            result = tb.client.create_table(
                TableName=table["TableName"],
                AttributeDefinitions=table["AttributeDefinitions"],
                KeySchema=table["KeySchema"],
                LocalSecondaryIndexes=table["LocalSecondaryIndexes"],
                ProvisionedThroughput=table["ProvisionedThroughput"]
            )
        else:
            result = tb.client.create_table(
                TableName=table["TableName"],
                AttributeDefinitions=table["AttributeDefinitions"],
                KeySchema=table["KeySchema"],
                ProvisionedThroughput=table["ProvisionedThroughput"]
            )
        tb.client.get_waiter('table_exists').wait(TableName=table["TableName"])
        tb.lg.info(table["TableName"] + ' has been created.')
    tb.end()

