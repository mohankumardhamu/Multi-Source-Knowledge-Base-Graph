import { Link, useLocation } from 'react-router-dom';
import {
    Home,
    FileText,
    Search,
    MessageSquare,
    Map,
    Settings
} from 'lucide-react';
import { cn } from '@/utils/cn';

const navigation = [
    { name: 'Home', href: '/', icon: Home },
    { name: 'Documents', href: '/documents', icon: FileText },
    { name: 'Search', href: '/search', icon: Search },
    { name: 'Q&A', href: '/qa', icon: MessageSquare },
    { name: 'Roadmap', href: '/roadmap', icon: Map },
    { name: 'Admin', href: '/admin', icon: Settings },
];

export function Sidebar() {
    const location = useLocation();

    return (
        <div className="flex h-full w-64 flex-col border-r bg-card">
            <div className="flex h-16 items-center border-b px-6">
                <h1 className="text-xl font-bold">KG-RAG</h1>
            </div>
            <nav className="flex-1 space-y-1 px-3 py-4">
                {navigation.map((item) => {
                    const isActive = location.pathname === item.href;
                    return (
                        <Link
                            key={item.name}
                            to={item.href}
                            className={cn(
                                'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                                isActive
                                    ? 'bg-primary text-primary-foreground'
                                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                            )}
                        >
                            <item.icon className="h-5 w-5" />
                            {item.name}
                        </Link>
                    );
                })}
            </nav>
        </div>
    );
}
