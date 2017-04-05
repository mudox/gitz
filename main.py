#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import argparse

import gitz

from log import init_logging
jack = init_logging(__name__)


def handle_sub_cmd_start(ns):
  gitz.start()


def handle_sub_cmd_list(ns):
  print(gitz.Gitz().fzf_lines(), file=sys.stderr)


def handle_sub_cmd_preview(ns):
  jack.warning('preview subcommand not implemented yet')


# create the top-level parser
top_cmd = argparse.ArgumentParser(prog='gitz')

subparsers = top_cmd.add_subparsers(
  title='subcomands', description='valid subcommands', help='sub-command help')

# subcommand `start`
sub_cmd_start = subparsers.add_parser('start', help='show main fzf interface')
sub_cmd_start.set_defaults(func=handle_sub_cmd_start)

# subcommand `list`
sub_cmd_list = subparsers.add_parser(
  'list', help='print out ansi lines to feed to fzf, for debug purpose')
sub_cmd_list.set_defaults(func=handle_sub_cmd_list)

# subcommand `preview`
sub_cmd_preview = subparsers.add_parser(
  'preview', help='print out command lines for `fzf --preview`')
sub_cmd_preview.set_defaults(func=handle_sub_cmd_preview)

if __name__ == "__main__":
  if len(sys.argv) == 1:
    gitz.start()
  else:
    ns = top_cmd.parse_args()
    ns.func(ns)
