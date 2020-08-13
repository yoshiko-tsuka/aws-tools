import datetime
import yaml
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from base_dynamodb_tables import BaseDynamo

class DeleteTables(BaseDynamo):
    def __init__(self):
        super().__init__(__file__)

if __name__ == "__main__":
    tb = DeleteTables()
    with open('dynamoDB/config/delete_tables.yaml') as file:
        yml = yaml.load(file, Loader=yaml.FullLoader)
        for table in yml['tables']:
                if table in tb.table_names:
                        tb.client.delete_table(TableName=table)
                        tb.client.get_waiter('table_not_exists').wait(TableName=table)
                        tb.lg.info(table + ' has been deleted.')
                else:
                        tb.lg.info(table + ' does not exist.')
    
    tb.end()

