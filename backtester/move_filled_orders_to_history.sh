#!/usr/bin/env bash
set -euo pipefail

# Move matched orders (unmatched_qty = 0) from filled_orders to filled_his_orders.
# Safe for repeated execution; uses INSERT OR IGNORE to avoid duplicate key issues.
# Usage:
#   bash backtester/move_filled_orders_to_history.sh          # loop every 5 minutes (default)
#   bash backtester/move_filled_orders_to_history.sh --once   # run once and exit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DB_PATH="${ROOT_DIR}/data/bot.db"

SQL=$(cat <<'EOF'
PRAGMA busy_timeout = 5000;
BEGIN;
INSERT OR IGNORE INTO filled_his_orders
SELECT * FROM filled_orders WHERE unmatched_qty = 0;

DELETE FROM filled_orders
WHERE unmatched_qty = 0
  AND id IN (SELECT id FROM filled_his_orders);
SELECT changes();
COMMIT;
EOF
)

run_once() {
  echo "Moving settled orders to filled_his_orders..."
  if count=$(sqlite3 "$DB_PATH" "$SQL" | tail -n 1); then
    echo "Moved $count orders."
    echo "Done."
  else
    echo "Error: SQLite command failed (likely locked). Retrying in next loop."
  fi
}

if [[ "${1:-}" == "--once" ]]; then
  run_once
else
  while true; do
    run_once
    sleep 300
  done
fi
