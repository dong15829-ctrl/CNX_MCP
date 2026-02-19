#!/usr/bin/env bash

di_monitor_install() {
  if [[ -z "${DI_MONITOR_SESSION_DIR-}" ]]; then
    return 0
  fi

  mkdir -p "${DI_MONITOR_SESSION_DIR}" 2>/dev/null || true

  shopt -s histappend 2>/dev/null || true
  export HISTFILE="${DI_MONITOR_SESSION_DIR}/bash_history"
  export HISTSIZE="${HISTSIZE:-200000}"
  export HISTFILESIZE="${HISTFILESIZE:-200000}"

  if [[ "${DI_MONITOR_ENABLE_EXEC_HASH-1}" == "1" ]]; then
    export DI_MONITOR_ENABLE_EXEC_HASH=1
  else
    export DI_MONITOR_ENABLE_EXEC_HASH=0
  fi

  if [[ -z "${PROMPT_COMMAND-}" ]]; then
    PROMPT_COMMAND="di_monitor__prompt_hook"
  elif [[ "${PROMPT_COMMAND}" != *"di_monitor__prompt_hook"* ]]; then
    PROMPT_COMMAND="${PROMPT_COMMAND};di_monitor__prompt_hook"
  fi
}

di_monitor__prompt_hook() {
  local exit_code="$?"

  if [[ -z "${DI_MONITOR_SESSION_DIR-}" ]]; then
    return 0
  fi

  history -a 2>/dev/null || true

  local hist_line cmd ts
  hist_line="$(history 1 2>/dev/null || true)"
  cmd="$(printf '%s' "${hist_line}" | sed 's/^[[:space:]]*[0-9]\+[[:space:]]*//')"

  if [[ -z "${cmd}" ]]; then
    return 0
  fi
  if [[ "${cmd}" == "${DI_MONITOR__LAST_CMD-}" && "${PWD}" == "${DI_MONITOR__LAST_PWD-}" ]]; then
    return 0
  fi
  DI_MONITOR__LAST_CMD="${cmd}"
  DI_MONITOR__LAST_PWD="${PWD}"

  ts="$(date -Iseconds)"
  printf '%s\t%s\t%s\t%s\n' "${ts}" "${exit_code}" "${PWD}" "${cmd}" >> "${DI_MONITOR_SESSION_DIR}/commands.tsv"

  if [[ "${DI_MONITOR_ENABLE_EXEC_HASH-0}" == "1" ]]; then
    di_monitor__maybe_log_exec_file "${ts}" "${PWD}" "${cmd}"
  fi
}

di_monitor__maybe_log_exec_file() {
  local ts="$1"
  local pwd="$2"
  local cmd="$3"

  local candidate=""
  candidate="$(di_monitor__extract_exec_file "${cmd}")" || true
  if [[ -z "${candidate}" ]]; then
    return 0
  fi

  local file_path=""
  if [[ "${candidate}" == /* ]]; then
    file_path="${candidate}"
  else
    file_path="${pwd}/${candidate}"
  fi

  if [[ ! -f "${file_path}" ]]; then
    return 0
  fi

  local size sha
  size="$(stat -c '%s' "${file_path}" 2>/dev/null || echo 0)"
  sha=""
  if [[ "${size}" -le 10485760 ]]; then
    read -r sha _ < <(sha256sum "${file_path}" 2>/dev/null || true)
  fi

  printf '%s\t%s\t%s\t%s\t%s\n' "${ts}" "${pwd}" "${candidate}" "${sha}" "${cmd}" >> "${DI_MONITOR_SESSION_DIR}/executed_files.tsv"
}

di_monitor__extract_exec_file() {
  local cmd="$1"

  # Naive tokenization (best-effort; ignores complex quoting).
  local -a tokens
  read -r -a tokens <<< "${cmd}"
  if [[ "${#tokens[@]}" -eq 0 ]]; then
    return 0
  fi

  local i=0
  if [[ "${tokens[0]}" == "sudo" && "${#tokens[@]}" -ge 2 ]]; then
    i=1
  fi

  local first="${tokens[$i]}"

  case "${first}" in
    python|python3|bash|sh|node|ruby|perl|php)
      local j
      for ((j=i+1; j<${#tokens[@]}; j++)); do
        if [[ "${tokens[$j]}" == -* ]]; then
          continue
        fi
        printf '%s' "${tokens[$j]}"
        return 0
      done
      return 0
      ;;
  esac

  if [[ "${first}" == ./* || "${first}" == /* ]]; then
    printf '%s' "${first}"
    return 0
  fi

  case "${first}" in
    *.sh|*.py|*.rb|*.pl|*.php|*.js)
      printf '%s' "${first}"
      return 0
      ;;
  esac

  return 0
}
