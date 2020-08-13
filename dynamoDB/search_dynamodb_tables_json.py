import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from base_dynamodb_tables import BaseDynamo

class SearchItems(BaseDynamo):
    def __init__(self):
        super().__init__(__file__)

if __name__ == "__main__":
    result = []
    tb = SearchItems()
    json_open = open('dynamoDB/config/query.json', 'r')
    json_data = json.load(json_open)
    if json_data['TableName'] in tb.table_names:
        response = tb.client.query(
            TableName=json_data['TableName'],
            KeyConditionExpression=json_data['Query'],
            ExpressionAttributeValues=json_data['Attribute'],
            FilterExpression=json_data['Filter'],
            ProjectionExpression=json_data['Projection']
            )
        result.extend(response)
        print(response)
        if "LastEvaluatedKey" in response:
            nextKey = response["LastEvaluatedKey"]
            while nextKey:
                query_result = tb.client.query(
                    TableName=json_data['TableName'],
                    KeyConditionExpression=json_data['Query'],
                    ExpressionAttributeValues=json_data['Attribute'],
                    FilterExpression=json_data['Filter'],
                    ProjectionExpression=json_data['Projection'],
                    ExclusiveStartKey=nextKey
                )
                result.extend(query_result["Items"])
                if not "LastEvaluatedKey" in query_result:
                    break
                else:
                    nextKey = query_result["LastEvaluatedKey"]
        tb.lg.info(result)
        tb.lg.info('Search ' + json_data['TableName'] + ' Items has been succeeded.')
    else:
        tb.lg.info(json_data['TableName'] + ' does not exist.')
    
    tb.end()

