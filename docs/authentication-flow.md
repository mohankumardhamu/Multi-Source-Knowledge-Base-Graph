# Authentication Flow

## What authentication is used

The kg-rag stack uses **OAuth2 / OpenID Connect**, with
[CloudFoundry UAA](https://github.com/cloudfoundry/uaa) as the identity
provider (IdP):

- **Frontend (`frontend/`)**: signs users in via the **Authorization Code +
  PKCE** flow (`react-oidc-context` / `oidc-client-ts`). No client secret is
  used — the SPA is registered in UAA as a public client (`kg-rag-frontend`).
- **API (`apps/api`)**: every `/v1/*` route requires a `Bearer` access token
  in the `Authorization` header. FastAPI validates the token's signature
  against UAA's JWKS endpoint (`/token_keys`) and checks the `iss` claim
  matches `KG_UAA_ISSUER_URL` (see `apps/api/kg_rag_api/auth.py`).
- `/health`, `/metrics`, and the legacy `ui/` app remain **unauthenticated**.

## How to use it

Full setup steps (running UAA, registering the OAuth client, env vars) are
documented in the project [README](../README.md#authentication-uaa).
Summary:

1. Run UAA locally: `cd <uaa-repo>/uaa && ../gradlew run` →
   `http://localhost:8080/uaa`.
2. Register the SPA client: `./scripts/register-uaa-client.sh`.
3. Configure env vars:
   - API: `KG_UAA_ISSUER_URL`, `KG_UAA_CLIENT_ID` (already set in
     `infra/docker-compose.yml`).
   - Frontend: `VITE_UAA_AUTHORITY`, `VITE_UAA_CLIENT_ID`,
     `VITE_UAA_REDIRECT_URI` (see `frontend/.env.example`).
4. Open `http://localhost:3001`, sign in as `marissa` / `koala`.

To call the API directly (e.g. with curl), obtain an access token from UAA
and pass it as `Authorization: Bearer <token>`:

```bash
curl -u kg-rag-frontend: \
  -d "grant_type=password&username=marissa&password=koala&response_type=token" \
  http://localhost:8080/uaa/oauth/token
```

## Application flow before authentication

Before this integration, the API trusted every caller — there was no
identity concept anywhere in the stack.

```
Browser (frontend, :3001)
   │
   │  GET /v1/docs, /v1/search, /v1/admin/overview, ... (no credentials)
   ▼
FastAPI (api, :8000)
   │  - every /v1/* route handled directly
   │  - no identity, no token, no user context
   ▼
Postgres / Qdrant / Neo4j / MinIO / Redis
```

- Any client that could reach `:8000` could call any endpoint.
- The UI never showed a login screen; all pages rendered immediately.
- `libs/common/kg_rag_common/settings.py` had no notion of a user or
  identity provider.

## Application flow after authentication

```
┌──────────┐  1. open app, no session         ┌──────────────────┐
│ Browser  │ ───────────────────────────────▶ │ UAA (:8080/uaa)   │
│ (:3001)  │  2. redirect to /oauth/authorize  │ - /oauth/authorize│
│          │ ◀─────────────────────────────── │ - /login          │
│          │  3. user logs in (marissa/koala)  │ - /oauth/token     │
│          │ ───────────────────────────────▶ │ - /token_keys      │
│          │  4. redirect to /callback?code=.. │ - /userinfo        │
│          │ ◀─────────────────────────────── └──────────────────┘
│          │  5. POST /oauth/token (code +
│          │     PKCE verifier) → access_token,
│          │     id_token, refresh_token
└────┬─────┘
     │ 6. AuthSync stores access_token (in memory),
     │    every apiClient request adds
     │    Authorization: Bearer <access_token>
     ▼
┌──────────────────┐
│ FastAPI (:8000)   │
│  /v1/* routes     │
│  └─ verify_token  │  7. fetch signing key from UAA /token_keys
│     dependency    │     (cached PyJWKClient)
│                    │  8. jwt.decode(token, key, issuer=KG_UAA_ISSUER_URL)
│                    │     - valid  → request proceeds, claims passed on
│                    │     - invalid/expired → 401 Unauthorized
└─────────┬─────────┘
          ▼
Postgres / Qdrant / Neo4j / MinIO / Redis
```

Key behavioral changes:

- **Unauthenticated browser session**: visiting a protected route
  (`/documents`, `/search`, `/qa`, `/roadmap`, `/admin`) triggers
  `ProtectedRoute` → `auth.signinRedirect()` → UAA login page. `/health`,
  `/metrics`, and the home page remain reachable without login.
- **Token issuance**: UAA issues a short-lived JWT `access_token` (RS256,
  signed with UAA's private key) plus an `id_token` and `refresh_token`.
  The frontend never sees a client secret (PKCE).
- **API enforcement**: `apps/api/kg_rag_api/main.py` attaches
  `Depends(verify_token)` to every `/v1/*` router. `auth.py` validates the
  token's signature (via JWKS) and issuer on each request — there is no
  server-side session state; the JWT itself is the credential.
- **Sign out**: `auth.removeUser()` clears the local token; the next API
  call has no `Authorization` header and `/v1/*` requests return `401`.
- **Token expiry**: once the `access_token` expires, `/v1/*` calls return
  `401` and the frontend should re-trigger `signinRedirect()` (the SPA
  currently does not auto-refresh; this is a follow-up improvement).
