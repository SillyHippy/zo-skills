#!/bin/bash
set -e

ACTION="${1:-status}"
LOGFILE="/dev/shm/hermes-gateway.log"

case "$ACTION" in
  start)
    if hermes gateway status >/dev/null 2>&1; then
      echo "Hermes gateway is already running."
    else
      hermes gateway run &>>"$LOGFILE" &
      sleep 3
      if hermes gateway status >/dev/null 2>&1; then
        echo "Hermes gateway started successfully."
      else
        echo "ERROR: Hermes gateway failed to start." >&2
        exit 1
      fi
    fi
    ;;
  stop)
    PID=$(pgrep -f "hermes gateway run" || true)
    if [ -n "$PID" ]; then
      kill "$PID" 2>/dev/null || true
      sleep 2
      echo "Hermes gateway stopped."
    else
      echo "Hermes gateway is not running."
    fi
    ;;
  restart)
    $0 stop
    sleep 1
    $0 start
    ;;
  status)
    hermes gateway status 2>&1
    ;;
  install)
    echo "Installing Hermes gateway as a boot-time service..."
    hermes gateway install 2>&1
    echo "Installed. Hermes will now start automatically on boot."
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|install}"
    exit 1
    ;;
esac
