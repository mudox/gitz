import logging
from pathlib import Path


class MyFormatter(logging.Formatter):

  """Formatter tai lored for xlog"""

  def __init__(self):
    super(MyFormatter, self).__init__('%(message)s')

  def format(self, record):

    super(MyFormatter, self).format(record)

    if record.levelno == logging.CRITICAL:
      prefix = 'C'
    elif record.levelno == logging.ERROR:
      prefix = 'E'
    elif record.levelno == logging.WARNING:
      prefix = 'W'
    elif record.levelno == logging.INFO:
      prefix = 'I'
    elif record.levelno == logging.DEBUG:
      prefix = 'D'

    output = '{severity}|{file}.{func}] {message}'
    output = output.format(
      severity=prefix,
      file=record.module,
      func=record.funcName,
      message=record.message,
    )

    return output


rootLoggerInitialized = False


def Jack(name):
  """create logger for each module
  It will initialize the root logger onece, and return a local logger for each
  name passed in

  :name: name of the module, e.g. `__name__`
  :returns: the module local logger

  """

  global rootLoggerInitialized

  if not rootLoggerInitialized:

    # direct all log into one file
    log_dir = Path('/tmp/mudox/log/python/Gitz/')
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'gitz.log'

    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    formatter = MyFormatter()
    fh.setFormatter(formatter)

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    rootLogger.addHandler(fh)
    rootLogger.info('root logger initialized')

    rootLoggerInitialized = True

  jack = logging.getLogger(name)
  jack.info('logger [%s] intialized', name)
  return jack
