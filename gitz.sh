#!/usr/bin/env bash

THIS_PATH=$(dirname "$0")

gz() {
  local ret
  ret="$(python3 "${THIS_PATH}/gitz.py")"
  if [[ -n $ret ]]; then
    cd "${ret}"
  fi
}
