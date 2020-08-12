import datetime
import yaml
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from common.logger import ColerdLog
from common.myconst import myconst as cst

if __name__ == "__main__":
    lg = ColerdLog.init_logger(__name__)
    lg.info('**** Delete DynamoDB Tables By Yaml ****')
    session = boto3.Session(profile_name=cst.PROFILE_NAME)
    client = session.client('dynamodb', region_name=cst.REGION_NAME)
    exist_tables = client.list_tables()['TableNames']
    with open('dynamoDB/config/delete_tables.yaml') as file:
        yml = yaml.load(file, Loader=yaml.FullLoader)
        for table in yml['tables']:
                if table in exist_tables:
                        client.delete_table(TableName=table)
                        client.get_waiter('table_not_exists').wait(TableName=table)
                        lg.info(table + ' has been deleted.')
                else:
                        lg.info(table + ' does not exist.')
    
    lg.info('**** End Delete DynamoDB Tables By Yaml ****')

