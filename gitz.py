#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import re
from pathlib import Path

from repo import Repo


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

REPO_SYMBOL = ' '
TRACKING_SYMBOL = ' '
UNTRACKED_SYMBOL = ' '
UNMERGED_SYMBOL = ' '
EQUAL_SYMBOL = '⟚ '
AHEAD_SYMBOL = '⇢ '
BEHIND_SYMBOL = '⇠ '
AB_SYMBOL = ' '


class Gitz(object):  # {{{

  DATA_FILE_PATH = '~/.gitz.json'
  """Docstring for Gitz. """

  def __init__(self):
    """TODO: to be defined1. """
    with open(os.path.expanduser(Gitz.DATA_FILE_PATH)) as file:

      # repos from ~/.gitz.json
      data = json.load(file)
      self.repos = [Repo(dict) for dict in data]

      # repos from ~/Git
      paths = [p for p in Path('~/Git').expanduser().glob('*/') if p.is_dir()]
      jack.debug(paths)
      paths = filter(lambda p: (p / '.git').is_dir(), paths)
      names = [p.parts[-1] for p in paths]
      repos = [Repo({"name": n, "path": p}) for n, p in zip(names, paths)]
      self.repos += repos

      jack.debug(names)

      # statistics
      self.max_name_width = 0

      self.max_tracking_width = 0
      self.max_untracked_width = 0
      self.max_unmerged_width = 0

      self.max_branch_head_width = 0
      self.max_upstream_width = 0
      self.max_a_width = 0
      self.max_b_width = 0

      self.show_tracking = False
      self.show_untracked = False
      self.show_unmerged = False

      for repo in self.repos:
        # remove tilder `~` if any
        repo.path = os.path.expanduser(repo.path)

        # column width statistic
        self.max_name_width = max(
          self.max_name_width,
          len(repo.name),
        )
        self.max_tracking_width = max(
          self.max_tracking_width,
          len(str(repo.tracking)),
        )
        self.max_untracked_width = max(
          self.max_untracked_width,
          len(str(repo.untracked)),
        )
        self.max_unmerged_width = max(
          self.max_unmerged_width,
          len(str(repo.unmerged)),
        )
        self.max_branch_head_width = max(
          self.max_branch_head_width,
          len(repo.branch_head),
        )
        self.max_upstream_width = max(
          self.max_upstream_width,
          len(repo.branch_upstream),
        )
        a, b = repo.branch_ab
        self.max_a_width = max(self.max_a_width, len(str(a)))
        self.max_b_width = max(self.max_b_width, len(str(b)))

        if repo.tracking > 0:
          self.show_tracking = True
        if repo.untracked > 0:
          self.show_untracked = True
        if repo.unmerged > 0:
          self.show_unmerged = True

      # fields width
      self.name_field_with = max(self.max_name_width, 14)
      self.tracking_field_width = max(self.max_tracking_width, 9)
      self.untracked_field_width = max(self.max_untracked_width, 9)
      self.unmerged_field_width = max(self.max_unmerged_width, 9)

      self.branch_field_width = sum(
        [
          self.max_branch_head_width,
          1,
          self.max_a_width,
          4,
          self.max_b_width,
          1,
          self.max_upstream_width,
        ])

      jack.debug(
        'widths: name:%d tracking:%d untracked:%d unmerged:%d',
        self.max_name_width,
        self.max_tracking_width,
        self.max_untracked_width,
        self.max_unmerged_width,
      )

      self.sort()

  def sort(self):
    # IDEA!: improve sorting algorithm
    # sort repos by change weight
    self.repos.sort(
      key=lambda x: x.tracking + x.untracked + x.unmerged,
      reverse=True,
    )

  def status_lines(self):
    """ generate colorized lines to feed to `fzf`
        :returns: a string lines with ANSI control code

        """
    return '\n'.join([self.line(repo) for repo in self.repos])

  def header(self):
    """ header line for fzf
      :returns: header line
    """
    name = '{:<%d}' % self.name_field_with
    name = name.format('REPO')
    name_ = '{:‾>%d}' % self.name_field_with
    name_ = name_.format('')

    if self.show_tracking:
      tracking = ' {:^%d}' % self.tracking_field_width
      tracking = tracking.format('UPDATE')
      tracking_ = ' {:‾>%d}' % self.tracking_field_width
      tracking_ = tracking_.format('')
    else:
      tracking = ''
      tracking_ = ''

    if self.show_untracked:
      untracked = ' {:^%d}' % self.untracked_field_width
      untracked = untracked.format('UNTRACKED')
      untracked_ = ' {:‾>%d}' % self.untracked_field_width
      untracked_ = untracked_.format('')
    else:
      untracked = ''
      untracked_ = ''

    if self.show_unmerged:
      unmerged = ' {:^%d}' % self.unmerged_field_width
      unmerged = unmerged.format('UNMERGED')
      unmerged_ = ' {:‾>%d}' % self.unmerged_field_width
      unmerged_ = unmerged_.format('')
    else:
      unmerged = ''
      unmerged_ = ''

    branch = ' {:^%d}' % self.branch_field_width
    branch = branch.format('BRANCH INFO')
    branch_ = ' {:‾>%d}' % self.branch_field_width
    branch_ = branch_.format('')

    line1 = '{}{}{}{}{}'.format(name, tracking, untracked, unmerged, branch)

    line2 = '{}{}{}{}{}'.format(
      name_, tracking_, untracked_, unmerged_, branch_)

    return line1 + '\n' + line2

  def count_field(self, which, number):
    if which == 'tracking':
      field_width = self.tracking_field_width
      digit_width = self.max_tracking_width
    elif which == 'untracked':
      field_width = self.untracked_field_width
      digit_width = self.max_untracked_width
    elif which == 'unmerged':
      field_width = self.unmerged_field_width
      digit_width = self.max_unmerged_width
    else:
      assert False, "invalid argument `which`: %s" % which

    width = int((field_width - digit_width) / 2 + digit_width)
    return '{0:{1}}'.format(number, width)

  def line(self, repo):
    """generate line to feed for fzf with ansi control code
        :returns: a string with ANSI control code
        """

    # name field
    name = '{:<%d}' % self.name_field_with
    name = name.format(repo.name)

    # tracking / untracked / merged field
    # hide if there is no counts to show
    if self.show_tracking:
      tracking = ' \x1b[33m{0:^{1}}\x1b[0m'.format(
        self.count_field('tracking', repo.tracking), self.tracking_field_width)
    else:
      tracking = ''

    if self.show_untracked:
      untracked = ' \x1b[32m{0:^{1}}\x1b[0m'.format(
        self.count_field('untracked', repo.untracked),
        self.untracked_field_width)
    else:
      untracked = ''

    if self.show_unmerged:
      unmerged = ' \x1b[34m{0:^{1}}\x1b[0m'.format(
        self.count_field('unmerged', repo.unmerged), self.unmerged_field_width)
    else:
      unmerged = ''

    # branch fields
    (ahead, behind) = repo.branch_ab

    left = right = link = ''

    # branch left & right part
    left = '{1:{0}}'.format(self.max_branch_head_width, repo.branch_head)
    right = '{1:{0}}'.format(self.max_upstream_width, repo.branch_upstream)

    # link part
    link_symbol = '' if repo.branch_upstream == ''       \
      else AHEAD_SYMBOL if (ahead != 0 and behind == 0)  \
      else BEHIND_SYMBOL if (ahead == 0 and behind != 0) \
      else EQUAL_SYMBOL if (ahead == 0 and behind == 0)  \
      else AB_SYMBOL

    link = '{a:>{a_width}} {link:2} {b:<{b_width}}'
    link = link.format(
      a=ahead or '',
      a_width=self.max_a_width,
      link=link_symbol,
      b=behind or '',
      b_width=self.max_b_width,
    )

    branch = ' {} {} {}'.format(left, link, right)

    return '{}{}{}{}{}'.format(
      name,
      tracking,
      untracked,
      unmerged,
      branch,
    )

  def fzf_lines(self):
    return self.header() + "\n" + self.status_lines()

  def __getitem__(self, name):
    return list(filter(lambda x: x.name == name, self.repos))[0]


# }}}


def name_of_fzf_line(line):
  return re.match('^\w+', line).group(0)


def start():
  gz = Gitz()
  lines = gz.fzf_lines()
  try:
    selected_line = subprocess.check_output(
      [
        # 'fzf-tmux',
        # '-u30%',
        'fzf',
        '--height=50%',
        '--min-height=15',
        '--header-lines=2',
        '--ansi',
        '--no-border',
        '--margin=1',
        '--nth=1',
        # '--color=bg:-1,bg+:-1',
      ],
      input=lines,
      universal_newlines=True).strip()
  except subprocess.CalledProcessError as e:
    if e.returncode != 130:  # user canceled in fzf
      raise
  except:
    raise
  else:
    name = name_of_fzf_line(selected_line)
    print(gz[name].path)
  finally:
    pass
