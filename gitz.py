#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import re

REPO_SYMBOL = ' '
TRACKING_SYMBOL = ' '
UNTRACKED_SYMBOL = ' '
UNMERGED_SYMBOL = ' '


class Gitz(object):

  DATA_FILE_PATH = '~/.gitz.json'
  """Docstring for Gitz. """

  def __init__(self):
    """TODO: to be defined1. """
    with open(os.path.expanduser(Gitz.DATA_FILE_PATH)) as file:
      self.data = json.load(file)
      self.repos = [Repo(dict) for dict in self.data]

  def fzf_lines(self):
    """ generate colorized lines to feed to `fzf`
        :returns: a string lines with ANSI control code

        """
    return '\n'.join([repo.line() for repo in self.repos])

  def header_line(self):
    """ header line for fzf
    :returns: header line

    """
    return '{:14}{:>7}{:>7}{:>7}'.format(' ', 'UPDATE', 'ADD', 'MERGE')

  def __getitem__(self, name):
    return list(filter(lambda x: x.name == name, gz.repos))[0]


class Repo(object):
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

    self.parse()

  def parse(self):
    """ Parse `git status ...` output, filter out info
        :returns: (tracked, untracked, unmerged)

        """
    cmd = 'git -C {} status --porcelain=v2 --untracked-files=all'

    for line in os.popen(cmd.format(self.path)):
      if line.startswith('1') or line.startswith('2'):
        self.tracking += 1
      elif line.startswith('u'):
        self.untracked += 1
      elif line.startswith('?'):
        self.unmerged += 1
      else:
        self.skipped += 1

  def line(self):
    """generate line to feed for fzf with ansi control code
        :returns: a string with ANSI control code

        """
    tracking = '\x1b[33m{:7}\x1b[0m'.format(self.tracking) if (
      self.tracking > 0) else ''
    untracked = '\x1b[32m{:7}\x1b[0m'.format(self.untracked) if (
      self.untracked > 0) else ''
    unmerged = '\x1b[34m{:7}\x1b[0m'.format(self.unmerged) if (
      self.unmerged > 0) else ''

    return '{:14}{}{}{}'.format(self.name, tracking, untracked, unmerged)


def name_of_fzf_line(line):
  return re.match('^\w+', line).group(0)


if __name__ == "__main__":
  gz = Gitz()
  lines = gz.header_line() + "\n" + gz.fzf_lines()

  try:
    selected_line = subprocess.check_output(
      ['fzf', '--header-lines=1', '--ansi'],
      input=lines,
      universal_newlines=True).strip()
  except subprocess.CalledProcessError as e:
    if e.returncode != 130:
      raise
  except:
    raise
  else:
    name = name_of_fzf_line(selected_line)
    print(gz[name].path)
  finally:
    pass