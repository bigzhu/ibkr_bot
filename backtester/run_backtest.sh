#!/usr/bin/env bash
set -euo pipefail

# Run the backtester with optional pre-sync.
# Usage: backtester/run_backtest.sh [options] SYMBOL TIMEFRAME CASH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_PATH="${ROOT_DIR}/data/bot.db"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

QUIET=1
START_RANGE=""
END_RANGE=""
DISABLE_LOGS=1
WITH_SYNC=0
SYNC_MONTHS=${SYNC_MONTHS:-42}

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
  --end)
    if [[ $# -lt 2 ]]; then
      echo "Error: --end requires a value" >&2
      exit 1
    fi
    END_RANGE="$2"
    shift 2
    ;;
  --enable-logs)
    DISABLE_LOGS=0
    shift
    ;;
  --with-sync)
    WITH_SYNC=1
    shift
    ;;
  --sync-months)
    if [[ $# -lt 2 ]]; then
      echo "Error: --sync-months requires a value" >&2
      exit 1
    fi
    SYNC_MONTHS="$2"
    shift 2
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

if [[ $# -lt 3 ]]; then
  cat <<EOF
Usage: $0 [options] SYMBOL TIMEFRAME CASH
Options:
  -v, --verbose        Show sync/backtest logs
  --start ISO          Limit backtest data to start date
  --end ISO            Limit backtest data to end date
  --enable-logs        Enable trading logs output (disabled by default)
  --with-sync          Run sync_klines.sh before backtest
  --sync-months N      Months to sync when --with-sync is used (default: ${SYNC_MONTHS})
EOF
  exit 1
fi

SYMBOL="$1"
TIMEFRAME="$2"
CASH="$3"

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

run_backtester() {
  run_python_module backtester "${BACKTEST_ARGS[@]}"
}

clear_symbol_data() {
  local symbol="$1"
  local timeframe="$2"
  local alt_timeframe="${timeframe}_1"

  log "Clearing backtest data for ${symbol} ${timeframe}..."

  if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='trading_logs';" | grep -q "trading_logs"; then
    sqlite3 "$DB_PATH" "DELETE FROM trading_logs WHERE symbol='${symbol}' AND kline_timeframe='${timeframe}';" >/dev/null 2>&1 || true
  fi

  if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='filled_orders';" | grep -q "filled_orders"; then
    sqlite3 "$DB_PATH" "UPDATE filled_orders SET unmatched_qty = 0 WHERE pair='${symbol}' AND (client_order_id='${timeframe}' OR client_order_id='${alt_timeframe}');" >/dev/null 2>&1 || true
    sqlite3 "$DB_PATH" "DELETE FROM filled_orders WHERE pair='${symbol}' AND (client_order_id='${timeframe}' OR client_order_id='${alt_timeframe}');" >/dev/null 2>&1 || true
  fi

  if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='order_matches';" | grep -q "order_matches"; then
    sqlite3 "$DB_PATH" "DELETE FROM order_matches WHERE pair='${symbol}' AND (timeframe='${timeframe}' OR timeframe='${alt_timeframe}');" >/dev/null 2>&1 || true
  fi

  log "Cleared backtest data for ${symbol} ${timeframe}"
}

reset_backtest_tables() {
  log "Resetting trading_logs, filled_orders, order_matches..."

  if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='trading_logs';" | grep -q "trading_logs"; then
    sqlite3 "$DB_PATH" "DELETE FROM trading_logs;" >/dev/null 2>&1 || true
  fi

  if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='filled_orders';" | grep -q "filled_orders"; then
    sqlite3 "$DB_PATH" "DELETE FROM filled_orders;" >/dev/null 2>&1 || true
  fi

  if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='filled_his_orders';" | grep -q "filled_his_orders"; then
    sqlite3 "$DB_PATH" "DELETE FROM filled_his_orders;" >/dev/null 2>&1 || true
  fi

  if sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='order_matches';" | grep -q "order_matches"; then
    sqlite3 "$DB_PATH" "DELETE FROM order_matches;" >/dev/null 2>&1 || true
  fi

  log "Global reset completed"
}

# 运行即清空表数据,确保回测干净
reset_backtest_tables

if [[ "$WITH_SYNC" -eq 1 ]]; then
  log "Running kline sync before backtest..."
  SYNC_CMD=("${SCRIPT_DIR}/sync_klines.sh")
  [[ "$QUIET" -eq 0 ]] && SYNC_CMD+=("-v")
  if [[ -n "${START_RANGE}" ]]; then
    SYNC_CMD+=("--start" "${START_RANGE}")
  else
    SYNC_CMD+=("--months" "${SYNC_MONTHS}")
  fi
  SYNC_CMD+=("${SYMBOL}" "${TIMEFRAME}")
  "${SYNC_CMD[@]}"
fi

log "Running VACUUM/ANALYZE for clean backtest..."
sqlite3 "$DB_PATH" "VACUUM; ANALYZE;"
log "Database maintenance completed"

SQLITE_PRAGMAS=$(
  cat <<'EOF'
PRAGMA cache_size = -524288; -- 512MB measured in KB
PRAGMA temp_store = MEMORY;
EOF
)
log "Applying SQLite PRAGMAs for backtest performance..."
sqlite3 "$DB_PATH" "$SQLITE_PRAGMAS"

log "Preparing backtest dataset for ${SYMBOL} ${TIMEFRAME}"
clear_symbol_data "${SYMBOL}" "${TIMEFRAME}"

BACKTEST_ARGS=("${SYMBOL}" "${TIMEFRAME}" "--cash" "${CASH}")
if [[ -n "${START_RANGE}" ]]; then
  BACKTEST_ARGS+=("--start" "${START_RANGE}")
fi
if [[ -n "${END_RANGE}" ]]; then
  BACKTEST_ARGS+=("--end" "${END_RANGE}")
fi
if [[ ${DISABLE_LOGS} -eq 0 ]]; then
  # Only add flag when logs are enabled (non-default)
  :
else
  BACKTEST_ARGS+=("--disable-trading-logs")
fi

export DISABLE_ORDER_MATCH_PERSISTENCE=1

LOG_MSG="Running backtester: ${SYMBOL} ${TIMEFRAME} --cash ${CASH}"
[[ -n "${START_RANGE}" ]] && LOG_MSG+=" --start ${START_RANGE}"
[[ -n "${END_RANGE}" ]] && LOG_MSG+=" --end ${END_RANGE}"
[[ ${DISABLE_LOGS} -eq 0 ]] && LOG_MSG+=" --enable-logs"
log "${LOG_MSG}"

if [[ "$QUIET" -eq 1 ]]; then
  (cd "$ROOT_DIR" && run_backtester) >/dev/null 2>&1
else
  (cd "$ROOT_DIR" && run_backtester)
fi
