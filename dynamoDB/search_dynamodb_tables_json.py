import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from common.logger import ColerdLog

if __name__ == "__main__":
    lg = ColerdLog.init_logger(__name__)
    lg.info('**** Search DynamoDB Tables ****')
    session = boto3.Session(profile_name='yoshiko')
    client = session.client('dynamodb', region_name='us-east-2')
    result = []
    table_names = client.list_tables()['TableNames']
    if table_names == []:
        lg.info('No tables')
    json_open = open('dynamoDB/config/query.json', 'r')
    json_data = json.load(json_open)
    response = self.__dynamo_query(area, weeks, visa, timetable, school)
        if not key in response:
            return None
    result.extend(response[key])
        if "LastEvaluatedKey" in response:
            nextKey = response["LastEvaluatedKey"]
        while nextKey:
            query_result = self.__dynamo_query(
                area, weeks, visa, timetable, school, nextKey)
            result.extend(query_result[key])
            if not "LastEvaluatedKey" in query_result:
                break
            else:
                nextKey = query_result["LastEvaluatedKey"]
        lg.info('Put ' + table["TableName"] + ' Items has been succeeded.')
    
    lg.info('**** End Search DynamoDB Tables ****')

