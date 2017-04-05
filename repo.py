#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path


# init logging {{{
def init_logging(name=__name__):
  import logging

  jack = logging.getLogger(name)
  jack.setLevel(logging.DEBUG)

  log_dir = Path('/tmp/mudox/log/python/Gitz/')
  log_dir.mkdir(parents=True, exist_ok=True)
  log_file = log_dir / __name__
  fh = logging.FileHandler(log_file, mode='w')
  fh.setLevel(logging.DEBUG)

  formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s:\n %(message)s')
  fh.setFormatter(formatter)

  jack.addHandler(fh)
  jack.info('logger [%s] init complete', __name__)
  return jack


jack = init_logging()

# }}}


class Repo(object):  # {{{

  """Docstring for Repo. """

  def __init__(self, dict):
    """TODO: to be defined1. """
    self.name = dict['name']
    self.path = dict['path']

    # derived
    self.tracking = 0
    self.untracked = 0
    self.unmerged = 0
    self.skipped = 0

    self.branch_head = ''
    self.branch_upstream = ''
    self.branch_ab = (0, 0)

    self.parse()

  def parse(self):
    """ Parse `git status ...` output, filter out info
        :returns: (tracked, untracked, unmerged)

        """
    cmd = 'git -C {} status --porcelain=v2 --untracked-files=all --branch'

    for line in os.popen(cmd.format(self.path)):
      if line.startswith('# branch.head'):
        self.branch_head = re.match('^# branch\.head (.*)$', line).group(1)

      elif line.startswith('# branch.upstream'):
        self.branch_upstream = re.match('^# branch\.upstream (.*)$',
                                        line).group(1)

      elif line.startswith('# branch.ab'):
        mat = re.match('^# branch\.ab \+(.*) \-(.*)$', line)
        self.branch_ab = (int(mat.group(1)), int(mat.group(2)))

      elif line.startswith('1') or line.startswith('2'):
        self.tracking += 1

      elif line.startswith('u'):
        self.unmerged += 1

      elif line.startswith('?'):
        self.untracked += 1

      else:
        self.skipped += 1


# }}}
