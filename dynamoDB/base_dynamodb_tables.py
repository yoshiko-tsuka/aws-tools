import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from abc import ABCMeta
from abc import abstractmethod
from common.logger import ColerdLog
from common.myconst import myconst as cst

class BaseDynamo(metaclass = ABCMeta):
    @abstractmethod
    def __init__(self, file_name):
        self.name = file_name
        self.lg = ColerdLog.init_logger(self.name)
        self.lg.info('**** Start ' + self.name + ' ****')
        self.session = boto3.Session(profile_name=cst.PROFILE_NAME)
        self.client = self.session.client('dynamodb', region_name=cst.REGION_NAME)
        self.table_names = self.client.list_tables()['TableNames']
    
    def end(self):
        self.lg.info('**** End '+ self.name + ' ****')