#!/bin/sh
# Salesforce SOQL helper. Bypasses corp SSL inspection, uses sf CLI via node directly.
# Usage: ./sf-query.sh "SELECT Id FROM User LIMIT 1"
NODE_TLS_REJECT_UNAUTHORIZED=0 \
  "/c/Program Files/sf/client/bin/node.exe" \
  "/c/Program Files/sf/client/bin/run" \
  data query --query "$1" --target-org DevSelim-EMEA --json 2>/dev/null
