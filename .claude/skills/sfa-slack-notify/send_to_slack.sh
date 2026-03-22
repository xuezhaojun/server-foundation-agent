#!/bin/bash
# send_to_slack.sh — Send Slack Block Kit JSON payload via webhook
#
# Usage:
#   send_to_slack.sh <payload.json>       # read from file
#   echo '{"blocks":[...]}' | send_to_slack.sh   # read from stdin
#
# Supports single payload object or array of payloads for multi-part messages.
# Requires: SLACK_WEBHOOK_URL environment variable

set -euo pipefail

if [ -z "${SLACK_WEBHOOK_URL:-}" ]; then
  echo "ERROR: SLACK_WEBHOOK_URL is not set" >&2
  exit 1
fi

PAYLOAD_FILE="${1:--}"
if [ "$PAYLOAD_FILE" = "-" ]; then
  PAYLOAD_JSON=$(cat)
else
  PAYLOAD_JSON=$(cat "$PAYLOAD_FILE")
fi

send_payload() {
  local payload="$1"
  local response http_code body

  response=$(curl -s -w "\n%{http_code}" -X POST \
    -H 'Content-type: application/json; charset=utf-8' \
    -d "$payload" \
    "$SLACK_WEBHOOK_URL")

  http_code=$(echo "$response" | tail -1)
  body=$(echo "$response" | sed '$d')

  if [ "$http_code" = "200" ] && [ "$body" = "ok" ]; then
    echo "Message sent successfully"
    return 0
  elif [ "$http_code" = "429" ]; then
    local retry_after
    retry_after=$(echo "$response" | grep -i "retry-after" | awk '{print $2}' || echo "2")
    echo "Rate limited. Retrying after ${retry_after:-2}s..." >&2
    sleep "${retry_after:-2}"
    curl -s -X POST -H 'Content-type: application/json; charset=utf-8' \
      -d "$payload" "$SLACK_WEBHOOK_URL" > /dev/null
    echo "Retry sent"
    return 0
  else
    echo "ERROR: Slack returned HTTP $http_code: $body" >&2
    return 1
  fi
}

# Detect if payload is an array (multi-part) or single object
IS_ARRAY=$(echo "$PAYLOAD_JSON" | jq -r 'if type == "array" then "true" else "false" end')

if [ "$IS_ARRAY" = "true" ]; then
  TOTAL=$(echo "$PAYLOAD_JSON" | jq 'length')
  for i in $(seq 0 $((TOTAL - 1))); do
    PAYLOAD=$(echo "$PAYLOAD_JSON" | jq -c ".[$i]")
    echo "Sending part $((i + 1))/$TOTAL..."
    send_payload "$PAYLOAD"
    if [ "$i" -lt $((TOTAL - 1)) ]; then
      sleep 1
    fi
  done
else
  send_payload "$PAYLOAD_JSON"
fi
