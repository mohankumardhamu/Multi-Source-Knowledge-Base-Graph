import { useEffect } from 'react';
import { useAuth } from 'react-oidc-context';
import type { ReactNode } from 'react';

export function ProtectedRoute({ children }: { children: ReactNode }) {
    const auth = useAuth();

    useEffect(() => {
        if (!auth.isLoading && !auth.isAuthenticated && !auth.activeNavigator) {
            auth.signinRedirect();
        }
    }, [auth, auth.isLoading, auth.isAuthenticated, auth.activeNavigator]);

    if (!auth.isAuthenticated) {
        return (
            <div className="flex h-full items-center justify-center p-8 text-muted-foreground">
                Redirecting to sign in...
            </div>
        );
    }

    return <>{children}</>;
}
