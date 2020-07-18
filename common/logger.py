from logging import getLogger, StreamHandler, Filter, basicConfig, DEBUG
import coloredlogs

class ColerdLog:
    def init_logger(name):
        logger = getLogger(name)
        coloredlogs.CAN_USE_BOLD_FONT = True
        coloredlogs.DEFAULT_FIELD_STYLES = {'asctime': {'color': 'green'},
                                            'hostname': {'color': 'magenta'},
                                            'levelname': {'color': 'magenta', 'bold': True},
                                            'name': {'color': 'blue'},
                                            'programname': {'color': 'cyan'}
                                            }
        coloredlogs.DEFAULT_LEVEL_STYLES = {'critical': {'color': 'red', 'bold': True},
                                            'error': {'color': 'red'},
                                            'warning': {'color': 'yellow'},
                                            'notice': {'color': 'magenta'},
                                            'info': {'color': 'green'},
                                            'debug': {'color': 'green'},
                                            'spam': {'color': 'green', 'faint': True},
                                            'success': {'color': 'green', 'bold': True},
                                            'verbose': {'color': 'blue'}
                                            }
        coloredlogs.install(level='DEBUG', logger=logger, fmt='[%(asctime)s] %(name)s %(levelname)s: %(message)s', datefmt='%Y/%m/%d %H:%M:%S')
        return logger
