gitstatus() {
  # $1: full path of git repo

  /usr/local/bin/git -C "$1" status --porcelain=v2 -uall | (
  let tracked=0 untracked=0 unmerged=0 unmatched=0
  while read -r line; do
    case "${line}" in
      [12]*)                ((tracked+=1));   ;;
      \?*)		    ((untracked+=1)); ;;
      u*)		    ((unmerged+=1));  ;;
      *)		    ((unmatched+=1)); ;;
    esac
  done
  echo "${tracked} ${untracked} ${unmerged} ${unmatched}"
  )
}

gitline() {
  # $1: full path of git repo

  gitstatus "$1" | (
  read -r tracked untracked unmerged unmatched
  if ((tracked == 0)); then
    tracked=''
  fi
  if ((untracked == 0)); then
    untracked=''
  fi
  if ((unmerged == 0)); then
    unmerged=''
  fi
  printf "\e[32m%10s\e[34m%10s\e[36m%10s\e[0m\n" "${tracked}" "${untracked}" "${unmerged}"
  )
}

gitlines() {
  local lines
  lines="$(grep -v '^#' ~/.mygitrepos)"
  echo "$lines" | (
  while IFS=$'\t' read -r name path; do
    printf '%-12s%s\t%s\n' "${name}" "$(gitline "${path}")" "${path}"
  done
  )
}

fzffeed() {
  header="$(printf '%-12s%10s%10s%10s\tPathHiiden' REPO CHANGE NEW UNMERGED)"
  content="$(gitlines)"
  printf "%s\n%s" "${header}" "${content}"
}

gz() {
ret=$(fzffeed | fzf --ansi --header-lines=1 --delimiter="\t" --with-nth=1 | cut -d $'\t' -f2)
cd "${ret}"
}
