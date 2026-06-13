#!/usr/bin/env bash
# Registers the kg-rag-frontend OAuth client with a running UAA server.
#
# Prerequisites:
#   - UAA running locally: cd <uaa-repo>/uaa && ../gradlew run
#     (listens on http://localhost:8080/uaa with the default admin client)
#
# Usage:
#   ./register-uaa-client.sh [UAA_BASE_URL] [REDIRECT_URI]
#
# Defaults:
#   UAA_BASE_URL  = http://localhost:8080/uaa
#   REDIRECT_URI  = http://localhost:3001/callback

set -euo pipefail

UAA_BASE_URL="${1:-http://localhost:8080/uaa}"
REDIRECT_URI="${2:-http://localhost:3001/callback}"
CLIENT_ID="kg-rag-frontend"

echo "Fetching admin token from ${UAA_BASE_URL}/oauth/token ..."
ADMIN_TOKEN=$(curl -sS -u admin:adminsecret \
  -d "grant_type=client_credentials" \
  "${UAA_BASE_URL}/oauth/token" | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')

if [ -z "${ADMIN_TOKEN}" ]; then
  echo "Failed to obtain admin token. Is UAA running at ${UAA_BASE_URL}?" >&2
  exit 1
fi

echo "Registering OAuth client '${CLIENT_ID}' with redirect URI ${REDIRECT_URI} ..."
curl -sS -X POST "${UAA_BASE_URL}/oauth/clients" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
  "client_id": "${CLIENT_ID}",
  "authorized_grant_types": ["authorization_code", "refresh_token"],
  "redirect_uri": ["${REDIRECT_URI}"],
  "scope": ["openid", "profile", "email"],
  "authorities": ["uaa.resource"],
  "autoapprove": ["openid"],
  "access_token_validity": 3600,
  "refresh_token_validity": 86400
}
EOF

echo
echo "Done. '${CLIENT_ID}' is registered as a public client (no secret, PKCE)."
echo
echo "IMPORTANT: enable CORS for the SPA origin so the browser can call /oauth/token directly."
echo "Add to uaa.yml and restart UAA:"
echo
echo "cors:"
echo "  xhr:"
echo "    enabled: true"
echo "    allowed-origins:"
echo "      - ^http://localhost:3001\$"
echo "    allowed-uris:"
echo "      - ^/oauth/token\$"
echo "      - ^/userinfo\$"
