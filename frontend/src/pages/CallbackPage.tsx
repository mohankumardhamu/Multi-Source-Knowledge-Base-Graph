import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from 'react-oidc-context';

export function CallbackPage() {
    const auth = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (!auth.isLoading && auth.isAuthenticated) {
            navigate('/', { replace: true });
        }
    }, [auth.isLoading, auth.isAuthenticated, navigate]);

    if (auth.error) {
        return (
            <div className="flex h-full items-center justify-center p-8 text-destructive">
                Sign-in failed: {auth.error.message}
            </div>
        );
    }

    return (
        <div className="flex h-full items-center justify-center p-8 text-muted-foreground">
            Signing in...
        </div>
    );
}
