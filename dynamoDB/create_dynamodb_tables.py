import datetime
import json
import os
import sys
import time
import boto3
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from common import logger

if __name__ == "__main__":
    lg = logger.init_logger(__name__)
    lg.info('**** Load dynamoDB create json ****')
    # __loadDynamoJSON('create')
    lg.info('**** Create dynamoDB tables ****')
    
    lg.info('**** End dynamoDB create tables ****')

