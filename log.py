import logging
from pathlib import Path


class MyFormatter(logging.Formatter):

  """Formatter tai lored for xlog"""

  def __init__(self):
    pass

  def format(self, record):

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
      message=record.msg,
    )

    return output


def init_logging(name):
  """create logger for each module

  :name: name of the module, e.g. `__name__`
  :returns: the module local logger

  """
  jack = logging.getLogger(name)
  jack.setLevel(logging.DEBUG)

  log_dir = Path('/tmp/mudox/log/python/Gitz/')
  log_dir.mkdir(parents=True, exist_ok=True)
  log_file = log_dir / 'gitz.log'

  fh = logging.FileHandler(log_file)
  fh.setLevel(logging.DEBUG)

  formatter = MyFormatter()
  fh.setFormatter(formatter)

  jack.addHandler(fh)
  jack.info('logger [%s] init complete', name)
  return jack


jack = init_logging(__name__)
