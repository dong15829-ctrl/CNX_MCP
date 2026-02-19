#!/usr/bin/env bash

di_monitor__autostart_main() {
  # Only for interactive shells.
  case "$-" in
    *i*) ;;
    *) return 0 ;;
  esac

  # Allow disabling per-session or globally.
  if [[ "${DI_MONITOR_AUTOSTART-1}" != "1" ]]; then
    return 0
  fi

  if [[ -n "${DI_MONITOR_SESSION_DIR-}" || "${DI_MONITOR_IN_SESSION-0}" == "1" ]]; then
    return 0
  fi

  local enabled_file="${XDG_CONFIG_HOME:-$HOME/.config}/di_monitoring/autostart.enabled"
  if [[ ! -f "${enabled_file}" ]]; then
    return 0
  fi

  if [[ -n "${DI_MONITOR_AUTOSTARTED-}" ]]; then
    return 0
  fi
  export DI_MONITOR_AUTOSTARTED=1

  local script_dir di_root start_script
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  di_root="$(cd "${script_dir}/../.." && pwd)"
  start_script="${di_root}/start_work.sh"

  if [[ ! -x "${start_script}" ]]; then
    return 0
  fi

  cd "${di_root}" || return 0
  exec "${start_script}" --name "autostart"
}

di_monitor__autostart_main
