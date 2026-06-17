import { Button } from '@/components/ui/button';
import { Moon, Sun, LogIn, LogOut } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useAuth } from 'react-oidc-context';

export function Header() {
    const auth = useAuth();
    const [darkMode, setDarkMode] = useState(false);

    useEffect(() => {
        // Check for saved theme preference or default to light mode
        const isDark = localStorage.getItem('theme') === 'dark';
        setDarkMode(isDark);
        if (isDark) {
            document.documentElement.classList.add('dark');
        }
    }, []);

    const toggleDarkMode = () => {
        const newMode = !darkMode;
        setDarkMode(newMode);
        if (newMode) {
            document.documentElement.classList.add('dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.classList.remove('dark');
            localStorage.setItem('theme', 'light');
        }
    };

    return (
        <header className="flex h-16 items-center justify-between border-b bg-card px-6">
            <div className="flex items-center gap-4">
                <h2 className="text-lg font-semibold">Knowledge Graph RAG</h2>
            </div>
            <div className="flex items-center gap-4">
                {auth.isAuthenticated ? (
                    <>
                        <span className="text-sm text-muted-foreground">
                            {String(auth.user?.profile?.user_name ?? auth.user?.profile?.sub ?? '')}
                        </span>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => auth.removeUser()}
                            aria-label="Sign out"
                        >
                            <LogOut className="mr-2 h-4 w-4" />
                            Sign out
                        </Button>
                    </>
                ) : (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => auth.signinRedirect()}
                        aria-label="Sign in"
                    >
                        <LogIn className="mr-2 h-4 w-4" />
                        Sign in
                    </Button>
                )}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleDarkMode}
                    aria-label="Toggle dark mode"
                >
                    {darkMode ? (
                        <Sun className="h-5 w-5" />
                    ) : (
                        <Moon className="h-5 w-5" />
                    )}
                </Button>
            </div>
        </header>
    );
}
