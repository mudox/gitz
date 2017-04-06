#!/usr/bin/env bash

THIS_PATH=$(dirname "$0")

gz() {
  local ret
  if [[ $# == 0 ]]; then
    ret=$(python3 "${THIS_PATH}"/main.py start)
    if [[ -n $ret ]]; then
      cd "${ret}" || return
    fi
  else
    python3 "${THIS_PATH}"/main.py "$@"
  fi
}

gza() {
  local ret
  if [[ $# == 0 ]]; then
    ret=$(python3 "${THIS_PATH}"/main.py start --all)
    if [[ -n $ret ]]; then
      cd "${ret}" || return
    fi
  else
    python3 "${THIS_PATH}"/main.py "$@"
  fi
}
