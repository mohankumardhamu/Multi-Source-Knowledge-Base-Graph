# Frontend Authentication Setup (Remote Access)

This document explains how to configure the modern React frontend to work with UAA authentication when accessed from a remote machine (e.g., via an IP address like `192.168.7.158`).

## Prerequisites
- UAA server running on the host (default port 8080).
- Docker and Docker Compose installed.

## 1. Configure Frontend Environment
Vite embeds environment variables at build time. When accessing the UI via an IP address, you must create a `.env` file in the `frontend/` directory with that IP.

Create `frontend/.env`:
```bash
VITE_API_BASE_URL=http://<SERVER_IP>:3001
VITE_UAA_AUTHORITY=http://<SERVER_IP>:8080/uaa
VITE_UAA_CLIENT_ID=kg-rag-frontend
VITE_UAA_REDIRECT_URI=http://<SERVER_IP>:3001/callback
```

## 2. Register OAuth Client in UAA
UAA must be configured to allow redirects to the specific IP and port of the frontend.

Run the registration script with the server's IP:
```bash
chmod +x scripts/register-uaa-client.sh
./scripts/register-uaa-client.sh http://<SERVER_IP>:8080/uaa http://<SERVER_IP>:3001/callback
```

## 3. Enable CORS in UAA
Ensure the UAA server allows requests from the frontend origin. In your `uaa.yml` (or wherever UAA configuration is managed), add the frontend URL to the CORS allowed origins:

```yaml
cors:
  xhr:
    enabled: true
    allowed-origins:
      - "^http://<SERVER_IP>:3001$"
    allowed-uris:
      - "^/oauth/token$"
      - "^/userinfo$"
```

## 4. Rebuild and Restart
Since Vite variables are baked in during the build, you must rebuild the frontend container:

```bash
make up
```

## Troubleshooting
- **ERR_SSL_PROTOCOL_ERROR**: Ensure you are using `http://` and not `https://` if SSL is not configured.
- **Sign In Button does nothing**: Check that `frontend/.env` was present during the `docker build` phase.
- **Invalid Redirect URI**: Ensure the URL in `VITE_UAA_REDIRECT_URI` matches exactly what was passed to the registration script.
