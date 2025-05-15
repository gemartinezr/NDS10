#!/bin/bash

# First arg: mode flag (optional)
MODE=$1

# Second arg: duration in minutes (optional)
DURATION_MIN=${2:-5}

# Clamp duration between 1 and 10
if (( DURATION_MIN < 1 )); then
  DURATION_MIN=1
elif (( DURATION_MIN > 10 )); then
  DURATION_MIN=10
fi

# Convert to seconds for timeout
DURATION_SEC=$((DURATION_MIN * 60))

TS=$(date -u +"%Y-%m-%dT%H-%M-%SZ")

if [[ "$MODE" == "--candump-only" ]]; then
  echo "[INFO] Skipping /dev/ttyUSB0 capture. Logging candump only for $DURATION_MIN min..."
  timeout ${DURATION_SEC}s candump -tz can0,7DF:7FF > canlogs_$TS.txt
else
  while [ ! -e /dev/ttyUSB0 ]; do
    echo "[WARN] /dev/ttyUSB0 not found, retrying in 5s..."
    sleep 5
  done

  echo "[INFO] Starting captures for $DURATION_MIN min..."
  timeout 10s sudo cat -A /dev/ttyUSB0 > fmc003_raw_$TS.txt &
  timeout ${DURATION_SEC}s candump -tz can0,7DF:7FF > canlogs_$TS.txt &

  wait
  echo "[INFO] Captures complete."
fi



# ./script.sh                   # Both captures, 5 minutes default
# ./script.sh --candump-only    # Only CAN log, 5 minutes
# ./script.sh --candump-only 2  # Only CAN log, 2 minutes
# ./script.sh full 7            # Both logs, 7 minutes (label "full" is ignored unless it's --candump-only)
