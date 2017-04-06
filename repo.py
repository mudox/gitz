#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from log import init_logging

jack = init_logging(__name__)

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

    self.priority = 0

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
