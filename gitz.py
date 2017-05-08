#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import subprocess
from pathlib import Path
import sys

import mdxlog
from repo import Repo

jack = mdxlog.MdxLogger(__name__)

REPO_SYMBOL = ' '
TRACKING_SYMBOL = ' '
UNTRACKED_SYMBOL = ' '
UNMERGED_SYMBOL = ' '
EQUAL_SYMBOL = '⟚ '
AHEAD_SYMBOL = '⇢ '
BEHIND_SYMBOL = '⇠ '
AB_SYMBOL = '⟚ '

EL = subprocess.check_output(['tput', 'el'], universal_newlines=True)
EL1 = subprocess.check_output(['tput', 'el1'], universal_newlines=True)
SC = subprocess.check_output(['tput', 'sc'], universal_newlines=True)
RC = subprocess.check_output(['tput', 'rc'], universal_newlines=True)
CUU1 = subprocess.check_output(['tput', 'cuu1'], universal_newlines=True)

# SMCUP = subprocess.check_output(['tput', 'smcup'], universal_newlines=True)
# RMCUP = subprocess.check_output(['tput', 'rmcup'], universal_newlines=True)


class Gitz(object):  # {{{

  DATA_FILE_PATH = '~/.gitz.json'
  """Docstring for Gitz. """

  def __init__(self, *, include_all=False):
    """TODO: to be defined1. """
    with open(os.path.expanduser(Gitz.DATA_FILE_PATH)) as file:

      json_dict = json.load(file)

      # repos from ~/.gitz.json
      self.repos = [Repo(dict) for dict in json_dict['repos']]
      for repo in self.repos:
        repo.priority = 10

      if include_all:
        # repos from ~/Git
        dirs = json_dict['repos_under']
        for dir in dirs:
          paths = [p for p in Path(dir).expanduser().glob('*/') if p.is_dir()]
          names = [p.parts[-1] for p in paths]
          repos = [Repo({"name": n, "path": p}) for n, p in zip(names, paths)]
          for repo in repos:
            repo.priority = 5
          self.repos += repos

      # collect status up
      print(
        'collecting status: {}'.format(SC),
        end='',
        file=sys.stderr,
        flush=True)
      for idx, repo in enumerate(self.repos, start=1):
        print(
          '{}{}{}/{}'.format(RC, EL, idx, len(self.repos)),
          end='',
          file=sys.stderr,
          flush=True)
        repo.parse()
      print(CUU1, end='', file=sys.stderr, flush=True)

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

      self.show_a = False
      self.show_b = False

      for repo in self.repos:
        # remove tilder `~` if any
        repo.path = os.path.expanduser(repo.path)

        # name width
        self.max_name_width = max(
          self.max_name_width,
          len(repo.name),
        )

        # tracking & untracked & unmerged width
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

        # branch part components width
        self.max_branch_head_width = max(
          self.max_branch_head_width,
          len(repo.branch_head),
        )
        self.max_upstream_width = max(
          self.max_upstream_width,
          len(repo.branch_upstream),
        )

        a, b = repo.branch_ab
        if (a > 0):
          self.show_a = True
        if (b > 0):
          self.show_b = True

        self.max_a_width = max(self.max_a_width, len(str(a)))
        self.max_b_width = max(self.max_b_width, len(str(b)))

        if repo.tracking > 0:
          self.show_tracking = True
        if repo.untracked > 0:
          self.show_untracked = True
        if repo.unmerged > 0:
          self.show_unmerged = True

      # fields width
      self.name_field_width = max(self.max_name_width, 14)
      self.tracking_field_width = max(self.max_tracking_width, 9)
      self.untracked_field_width = max(self.max_untracked_width, 9)
      self.unmerged_field_width = max(self.max_unmerged_width, 9)

      # branch width
      self.branch_field_width = sum(
        [
          self.max_branch_head_width,
          4,
          self.max_upstream_width,
        ])

      if self.show_a:
        self.branch_field_width += 1 + self.max_a_width

      if self.show_b:
        self.branch_field_width += 1 + self.max_b_width

      jack.debug(
        'widths: name:%d tracking:%d untracked:%d unmerged:%d',
        self.max_name_width,
        self.max_tracking_width,
        self.max_untracked_width,
        self.max_unmerged_width,
      )

      self.sort()

  def get_sorting_weight(self, repo):
    """sorting key for repo object

    :repo: the Repo object
    :returns: the calculated weight value

    """
    weight = 0
    weight += repo.priority * 300
    weight += 200 if repo.branch_upstream != '' else 0
    weight += repo.tracking
    weight += repo.untracked
    weight += repo.unmerged
    a, b = repo.branch_ab
    weight += a + b

    return weight

  def sort(self):
    # IDEA!: improve sorting algorithm
    # sort repos by change weight

    self.repos.sort(
      key=self.get_sorting_weight,
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
    name = '{:>%d}' % self.name_field_width
    name = name.format('REPO')
    name_ = '{:‾>%d}' % self.name_field_width
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
    return '{0:{1}}'.format(number or '', width)

  def line(self, repo):
    """generate line to feed for fzf with ansi control code
        :returns: a string with ANSI control code
        """

    # name field
    name = '{:>%d}' % self.name_field_width
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

    # branch field
    (ahead, behind) = repo.branch_ab

    left = right = link = ''

    # branch left & right part
    left = '{1:>{0}}'.format(self.max_branch_head_width, repo.branch_head)
    right = '{1:<{0}}'.format(self.max_upstream_width, repo.branch_upstream)

    # link symbol
    link_symbol = '' if repo.branch_upstream == ''       \
      else AHEAD_SYMBOL if (ahead != 0 and behind == 0)  \
      else BEHIND_SYMBOL if (ahead == 0 and behind != 0) \
      else EQUAL_SYMBOL if (ahead == 0 and behind == 0)  \
      else AB_SYMBOL

    # line part
    # link = '\x1b[35m{a:>{a_width}}\x1b[0m {link:2} \x1b[36m{b:<{b_width}}\x1b[0m'
    link = '{a:>{a_width}} {link:2} {b:<{b_width}}'
    link = link.format(
      a='\x1b[35m{}\x1b[0m'.format(ahead) if ahead > 0 else '',
      a_width=self.max_a_width,
      link=link_symbol,
      b='\x1b[36m{}\x1b[0m'.format(behind) if behind > 0 else '',
      b_width=self.max_b_width,
    )

    if not self.show_a:
      link = link[self.max_a_width + 1:]

    if not self.show_b:
      link = link[:-self.max_b_width - 1]

    if ahead > 0 or behind > 0:
      branch = ' {} {} \x1b[0m{}'.format(left, link, right)
    else:
      branch = [
        ' \x1b[38;2;100;100;100m{}',
        '\x1b[38;2;100;100;100m{}',
        '\x1b[38;2;100;100;100m{}\x1b[0m',
      ]
      branch = ' '.join(branch)
      branch = branch.format(left, link, right)

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

  def get_name_for_fzf_line(self, line):
    return line[:self.name_field_width].strip()


# }}}


def start(show_all):
  gz = Gitz(include_all=show_all)
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
      universal_newlines=True)
  except subprocess.CalledProcessError as e:
    if e.returncode != 130:  # user canceled in fzf
      raise
  except:
    raise
  else:
    name = gz.get_name_for_fzf_line(selected_line)
    print('cd:{}'.format(gz[name].path))
  finally:
    pass
