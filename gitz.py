#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
import re
from pathlib import Path

# init logging {{{
import logging

jack = logging.getLogger(__name__)
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
# }}}

REPO_SYMBOL = ' '
TRACKING_SYMBOL = ' '
UNTRACKED_SYMBOL = ' '
UNMERGED_SYMBOL = ' '
AB_SYMBOL = '⟚ '
AHEAD_SYMBOL = '⇢ '
BEHIND_SYMBOL = '⇠ '
EQUAL_SYMBOL = ' '


class Gitz(object):  # {{{

  DATA_FILE_PATH = '~/.gitz.json'
  """Docstring for Gitz. """

  def __init__(self):
    """TODO: to be defined1. """
    with open(os.path.expanduser(Gitz.DATA_FILE_PATH)) as file:

      # repos from ~/.gitz.json
      data = json.load(file)
      self.repos = [Repo(dict) for dict in data]

      paths = [p for p in Path('~/Git').expanduser().glob('*/') if p.is_dir()]
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

      self.branch_field_width = self.max_branch_head_width + 10 + self.max_upstream_width

      jack.debug(
        'name:%d tracking:%d untracked:%d unmerged:%d',
        self.max_name_width,
        self.max_tracking_width,
        self.max_untracked_width,
        self.max_unmerged_width,
      )

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
      tracking = ' \x1b[32m{0:^{1}}\x1b[0m'.format(
        self.count_field('tracking', repo.tracking), self.tracking_field_width)
    else:
      tracking = ''

    if self.show_untracked:
      untracked = ' \x1b[32m{0:^{1}}\x1b[0m'.format(
        self.count_field('untracked', repo.untracked), self.untracked_field_width)
    else:
      untracked = ''

    if self.show_unmerged:
      unmerged = ' \x1b[32m{0:^{1}}\x1b[0m'.format(
        self.count_field('unmerged', repo.unmerged), self.unmerged_field_width)
    else:
      unmerged = ''


    # branch fields
    (ahead, behind) = repo.branch_ab

    # link part in the middle of branch field
    if ahead == 0 and behind != 0:
      link = '    {} {:<3}'.format(BEHIND_SYMBOL, behind)
    elif ahead != 0 and behind == 0:
      link = '{:>3} {}    '.format(ahead, AHEAD_SYMBOL)
    elif ahead == 0 and behind == 0:
      link = '    {}    '.format(EQUAL_SYMBOL)
    else:
      link = '{:>3} {} {:<3}'.format(ahead, AB_SYMBOL, behind)

    left = '{:>%d}' % self.max_branch_head_width
    left = left.format(repo.branch_head)
    right = '{:<%d}' % self.max_upstream_width
    right = right.format(repo.branch_upstream)
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
