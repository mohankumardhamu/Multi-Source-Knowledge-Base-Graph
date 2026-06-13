import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { AuthProvider } from 'react-oidc-context'
import './index.css'
import App from './App.tsx'
import { AuthSync } from './components/AuthSync.tsx'

const oidcConfig = {
  authority: import.meta.env.VITE_UAA_AUTHORITY,
  client_id: import.meta.env.VITE_UAA_CLIENT_ID,
  redirect_uri: import.meta.env.VITE_UAA_REDIRECT_URI,
  scope: 'openid',
  onSigninCallback: () => {
    window.history.replaceState({}, document.title, window.location.pathname.replace(/\/callback\/?$/, '/'))
  },
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider {...oidcConfig}>
      <AuthSync />
      <App />
    </AuthProvider>
  </StrictMode>,
)
