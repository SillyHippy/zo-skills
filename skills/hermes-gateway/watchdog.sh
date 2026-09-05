#!/bin/bash
# Hermes gateway watchdog — restarts the gateway if it dies

while true; do
    if ! pgrep -f "hermes gateway run" > /dev/null 2>&1; then
        echo "[$(date)] Gateway not running, starting..." >> /tmp/hermes-watchdog.log
        rm -f ~/.hermes/gateway.pid 2>/dev/null
        hermes gateway run &
        sleep 5
        if ! pgrep -f "hermes gateway run" > /dev/null 2>&1; then
            echo "[$(date)] Failed to start gateway" >> /tmp/hermes-watchdog.log
        else
            echo "[$(date)] Gateway started (PID: $(pgrep -f 'hermes gateway run'))" >> /tmp/hermes-watchdog.log
        fi
    fi
    sleep 30
done
