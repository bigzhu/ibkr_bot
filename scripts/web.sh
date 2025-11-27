#!/usr/bin/env bash

FRONTEND_DIR=${FRONTEND_DIR:-web_admin/frontend}
FRONTEND_CMD=${FRONTEND_CMD:-"npx quasar dev"}

echo "Starting frontend dev server: $FRONTEND_CMD"
(
  cd "$FRONTEND_DIR"
  bash -lc "$FRONTEND_CMD"
)
