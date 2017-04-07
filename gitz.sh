#!/usr/bin/env bash

THIS_PATH=$(dirname "$0")

gz() {
  local ret
  if [[ $# == 0 ]]; then
    ret=$(python3 "${THIS_PATH}"/main.py start)
  else
    ret=$(python3 "${THIS_PATH}"/main.py "$@")
  fi
  __gitz_handle_result "$ret"
}

gza() {
  local ret
  if [[ $# == 0 ]]; then
    ret=$(python3 "${THIS_PATH}"/main.py start --all)
  else
    ret=$(python3 "${THIS_PATH}"/main.py "$@")
  fi
  __gitz_handle_result "$ret"
}

__gitz_handle_result() {
  if [[ $1 =~ '^cd:' ]]; then
    local cdto
    cdto="${1:3}"
    printf "\e[34mcd to: %s ...\n" "$cdto"
    cd "$cdto" || return
  fi
}
