import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from common.logger import ColerdLog
from common.myconst import myconst as cst
from base_dynamodb_tables import BaseDynamo

class DeleteAllTables(BaseDynamo):
    def __init__(self):
        super().__init__(__file__)

if __name__ == "__main__":
    tb = DeleteAllTables()
    if tb.table_names == []:
        tb.lg.info('No tables')
    for table_name in tb.table_names:
            tb.client.delete_table(TableName=table_name)
            tb.client.get_waiter('table_not_exists').wait(TableName=table_name)
            tb.lg.info(table_name + ' has been deleted.')
    tb.end()

