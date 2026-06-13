import { useEffect } from 'react';
import { useAuth } from 'react-oidc-context';
import { setAccessToken } from '@/services/api';

export function AuthSync() {
    const auth = useAuth();

    useEffect(() => {
        setAccessToken(auth.user?.access_token ?? null);
    }, [auth.user]);

    return null;
}
