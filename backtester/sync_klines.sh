#!/usr/bin/env bash
set -euo pipefail

# Synchronize historical klines into backtest_klines.
# Usage: backtester/sync_klines.sh [-v|--verbose] [--start ISO] [--months N] [--full-sync] SYMBOL TIMEFRAME

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_PATH="${ROOT_DIR}/data/bot.db"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

QUIET=1
START_RANGE=""
SYNC_MONTHS=${SYNC_MONTHS:-42}
FULL_SYNC=0

while [[ $# -gt 0 ]]; do
  case "$1" in
  -v | --verbose)
    QUIET=0
    shift
    ;;
  --start)
    if [[ $# -lt 2 ]]; then
      echo "Error: --start requires a value" >&2
      exit 1
    fi
    START_RANGE="$2"
    shift 2
    ;;
  --months)
    if [[ $# -lt 2 ]]; then
      echo "Error: --months requires a value" >&2
      exit 1
    fi
    SYNC_MONTHS="$2"
    shift 2
    ;;
  --full-sync)
    FULL_SYNC=1
    shift
    ;;
  --)
    shift
    break
    ;;
  -*)
    echo "Unknown option: $1" >&2
    exit 1
    ;;
  *)
    break
    ;;
  esac
done

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 [-v|--verbose] [--start ISO] [--months N] [--full-sync] SYMBOL TIMEFRAME"
  echo "Example (incremental): $0 -v ADAUSDC 1m"
  echo "Example (full range): $0 --full-sync --start 2024-01-01 ADAUSDC 1m"
  exit 1
fi

SYMBOL="$1"
TIMEFRAME="$2"

log() {
  if [[ "$QUIET" -eq 0 ]]; then
    echo "$@"
  fi
}

run_python_module() {
  local module="$1"
  shift
  if command -v p >/dev/null 2>&1; then
    p -m "$module" "$@"
  else
    uv run python -m "$module" "$@"
  fi
}

calculate_requested_start_date() {
  if [[ -n "${START_RANGE}" ]]; then
    echo "${START_RANGE}"
    return 0
  fi

  if command -v date >/dev/null 2>&1; then
    local calculated_date
    calculated_date=$(date -v-"${SYNC_MONTHS}"m "+%Y-%m-%d" 2>/dev/null)
    if [[ -z "$calculated_date" ]]; then
      calculated_date=$(date -d "${SYNC_MONTHS} months ago" "+%Y-%m-%d" 2>/dev/null)
    fi
    echo "$calculated_date"
  else
    log "Warning: 'date' command not found, cannot calculate default start date"
    echo ""
  fi
}

check_and_clear_klines() {
  if [[ "$FULL_SYNC" -eq 1 ]]; then
    log "Clearing existing klines for ${SYMBOL} ${TIMEFRAME} due to full sync request"
    sqlite3 "$DB_PATH" "DELETE FROM backtest_klines WHERE symbol='${SYMBOL}' AND timeframe='${TIMEFRAME}';" >/dev/null 2>&1
    log "Cleared existing klines"
    return 0
  fi

  local requested_date
  requested_date=$(calculate_requested_start_date)

  if [[ -z "$requested_date" ]]; then
    log "Cannot determine requested start date, skipping kline range check"
    return 0
  fi

  local query="SELECT MIN(open_time) as earliest FROM backtest_klines WHERE symbol='${SYMBOL}' AND timeframe='${TIMEFRAME}';"
  local earliest_ts
  earliest_ts=$(sqlite3 "$DB_PATH" "$query" 2>/dev/null | head -1)

  if [[ -z "$earliest_ts" ]] || [[ "$earliest_ts" == "" ]]; then
    log "No existing klines found, will sync from scratch"
  else
    local requested_ts
    if command -v date >/dev/null 2>&1; then
      local normalized_date="${requested_date}T00:00:00"
      requested_ts=$(date -u -j -f "%Y-%m-%dT%H:%M:%S" "${normalized_date}" "+%s" 2>/dev/null)
      if [[ -z "$requested_ts" ]]; then
        requested_ts=$(date -u -d "${normalized_date}" "+%s" 2>/dev/null)
      fi
      if [[ -z "$requested_ts" ]]; then
        log "Warning: unable to parse requested date ${requested_date} as UTC, skipping kline range check"
        requested_ts=""
      else
        requested_ts=$((requested_ts * 1000))
      fi
    fi

    if [[ -n "$requested_ts" ]] && [[ "$requested_ts" -lt "$earliest_ts" ]]; then
      log "Requested start time (${requested_date}) is earlier than existing klines"
      log "Clearing existing klines for ${SYMBOL} ${TIMEFRAME} to allow full range sync..."
      sqlite3 "$DB_PATH" "DELETE FROM backtest_klines WHERE symbol='${SYMBOL}' AND timeframe='${TIMEFRAME}';" >/dev/null 2>&1
      log "Cleared existing klines"
    else
      log "Existing klines cover requested range (${requested_date}), will use incremental sync"
    fi
  fi
}

sync_klines() {
  log "Syncing historical klines for ${SYMBOL} ${TIMEFRAME}..."
  local sync_args=("${SYMBOL}" "${TIMEFRAME}")

  if [[ -n "${START_RANGE}" ]]; then
    log "Using start date: ${START_RANGE}"
    sync_args+=("--start" "${START_RANGE}")
  else
    log "Using default: ${SYNC_MONTHS} months"
    sync_args+=("--months" "${SYNC_MONTHS}")
  fi

  if [[ "$QUIET" -eq 1 ]]; then
    run_python_module backtester.klines_syncer "${sync_args[@]}" >/dev/null 2>&1
  else
    run_python_module backtester.klines_syncer "${sync_args[@]}"
  fi

  log "Kline sync complete"
}

log "Preparing historical dataset for ${SYMBOL} ${TIMEFRAME}"

if [[ "$FULL_SYNC" -eq 1 ]]; then
  log "Full sync requested; existing klines will be cleared"
  check_and_clear_klines
else
  log "Incremental mode; existing klines will be preserved"
fi
sync_klines
