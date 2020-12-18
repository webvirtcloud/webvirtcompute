import logging
import os
import sys
import json
import traceback
import datetime
from logging import handlers
from settings import WHEN, LOG_DIR, LOG_LEVEL, BACKUP_COUNT, INTERVAL, MAX_SIZE


class SizeTimedRotatingFileHandler(handlers.TimedRotatingFileHandler):
    def __init__(self, filename, when='h', interval=1, backupCount=0,
                 encoding=None, delay=False, utc=False, maxBytes=8192):
        super(SizeTimedRotatingFileHandler, self).__init__(filename, when, interval, backupCount, encoding, delay, utc)
        self.maxBytes = maxBytes

    def shouldRollover(self, record):
        size_result = 0
        time_result = super(SizeTimedRotatingFileHandler, self).shouldRollover(record)
        if not time_result:
            if self.stream is None:
                self.stream = self._open()
            if self.maxBytes > 0:
                msg = "%s\n" % self.format(record)
                self.stream.seek(0, 2)
                if self.stream.tell() + len(msg) >= self.maxBytes:
                    size_result = 1
        self.size_flag = size_result
        return size_result or time_result


class VirtmgrdLogger(object):

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    info_logger = logging.getLogger('info')
    info_file = os.path.join(LOG_DIR, 'info.log')
    info_handler = SizeTimedRotatingFileHandler(info_file, WHEN, INTERVAL, backupCount=BACKUP_COUNT, maxBytes=MAX_SIZE)
    info_logger.addHandler(info_handler)
    info_logger.setLevel(logging.INFO)

    error_logger = logging.getLogger('error')
    error_file = os.path.join(LOG_DIR, 'error.log')
    error_handler = SizeTimedRotatingFileHandler(error_file, WHEN, INTERVAL, backupCount=BACKUP_COUNT, maxBytes=MAX_SIZE)
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)

    debug_logger = logging.getLogger('debug')
    debug_file = os.path.join(LOG_DIR, 'debug.log')
    debug_handler = SizeTimedRotatingFileHandler(debug_file, WHEN, INTERVAL, backupCount=BACKUP_COUNT, maxBytes=MAX_SIZE)
    debug_logger.addHandler(debug_handler)
    debug_logger.setLevel(logging.DEBUG)

    def INFO(self, action, message):
        if LOG_LEVEL <= logging.INFO:
            line = self.format_message(logging.INFO, action=action, message=message)
            self.info_logger.info(line)

    def ERROR(self, message, exc_info=True):
        if LOG_LEVEL <= logging.ERROR:
            line = self.format_message(logging.ERROR, message=message)
            self.error_logger.error(line, exc_info=exc_info)

    def DEBUG(self, _type, **kwargs):
        if LOG_LEVEL <= logging.DEBUG:
            line = self.format_message(logging.DEBUG, _type=_type, **kwargs)
            self.debug_logger.debug(line)

    def format_message(self, LEVEL, **kwargs):
        line = ''
        if LEVEL == logging.INFO:
            line = '[{}] {}: {}'.format(str(datetime.datetime.now()), kwargs.get('action'), kwargs.get('message'))
        elif LEVEL == logging.ERROR:
            line = '[{}] exception occured: {}'.format(str(datetime.datetime.now()), kwargs.get('message'))
        elif LEVEL == logging.DEBUG:
            if kwargs.get('_type') == 'return':
                line = '[{}] routine [{}]: return={}'.format(str(datetime.datetime.now()),
                                                             kwargs.get('routine'),
                                                             kwargs.get('_return'))
            elif kwargs.get('_type') == 'call':
                line = '[{}] calling routine [{}]: *args={}, **kwargs={}'.format(str(datetime.datetime.utcnow()),
                                                                                 kwargs.get('routine'),
                                                                                 json.dumps(kwargs.get('args', []),
                                                                                            default=str),
                                                                                 json.dumps(kwargs.get('kwargs', {}),
                                                                                            default=str)
                                                                                 )
            elif kwargs.get('_type') == 'error':
                line = '[{}] routine [{}]: raise exception.\n{}'.format(str(datetime.datetime.now()),
                                                                        kwargs.get('routine'),
                                                                        kwargs.get('trace'))
        return line


def function_logger(logger=VirtmgrdLogger()):
    def logging_decorator(func):
        def wrapper(*args, **kwargs):
            logger.DEBUG('call', routine=func.__name__, args=args, kwargs=kwargs)
            try:
                res = func(*args, **kwargs)
            except Exception as e:
                ex_type, ex, tb = sys.exc_info()
                tb_str = ''.join(traceback.format_exception(etype=ex_type, value=ex, tb=tb))
                logger.DEBUG('error', routine=func.__name__, trace=tb_str)
                raise e
            logger.DEBUG('return', routine=func.__name__, _return=res)
            return res
        return wrapper
    return logging_decorator


def method_logger(logger=VirtmgrdLogger()):
    def logging_decorator(method):
        def wrapper(self, *args, **kwargs):
            logger.DEBUG('call', routine=self.__class__.__name__+"."+method.__name__, args=args, kwargs=kwargs)
            try:
                res = method(self, *args, **kwargs)
            except Exception as e:
                ex_type, ex, tb = sys.exc_info()
                tb_str = ''.join(traceback.format_exception(etype=ex_type, value=ex, tb=tb))
                logger.DEBUG('error', routine=self.__class__.__name__+"."+method.__name__, trace=tb_str)
                raise e
            logger.DEBUG('return', routine=self.__class__.__name__+"."+method.__name__, _return=res)
            return res

        return wrapper
    return logging_decorator


"""
if __name__ == '__main__':
    logger = VirtmgrdLogger()
    logger.INFO('create_sgroup', 'test description')
    try:
        raise Exception('this is test exception')
    except:
        logger.ERROR('new exception')

    logger.DEBUG('call', args=[1, 2, 3], kwargs={'msg': 'Hello World'}, routine='my_test_function')
    logger.DEBUG('return', _return=True)
    try:
        raise Exception('this is debug test exception')
    except Exception as e:
        ex_type, ex, tb = sys.exc_info()
        tb_str = ''.join(traceback.format_exception(etype=ex_type, value=ex, tb=tb))
        logger.DEBUG('error', routine='test_routine', trace=tb_str)

    @function_logger(logger)
    def test_func(n):
        if not n:
            raise TypeError('expecting int but got None')
        if n == 1:
            return 'hello'
        else:
            return 'what', None

    test_func(1)
    test_func(2)
    #test_func(None)

    class Test:
        @method_logger()
        def __init__(self, x, y):
            self.x = x
            self.y = y

        @method_logger()
        def add(self):
            return self.x + self.y

        @method_logger()
        def divide(self):
            return self.x / self.y

    t = Test(1, 0)
    t.add()
    t.divide()
"""
