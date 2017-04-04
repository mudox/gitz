#!/usr/bin/env bash

THIS_PATH=$(dirname "$0")

gz() {
  local ret
  if [[ $# == 1 ]]; then
    ret=$(python3 "${THIS_PATH}"/main.py start)
  else
    ret=$(python3 "${THIS_PATH}"/main.py "$@")
  fi

  if [[ -n $ret ]]; then
    cd "${ret}" || return
  fi
}
