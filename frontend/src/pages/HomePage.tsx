import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Search, MessageSquare, Map, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';

export function HomePage() {
    const features = [
        {
            title: 'Document Management',
            description: 'Upload and manage PDF documents with automatic ingestion',
            icon: FileText,
            href: '/documents',
        },
        {
            title: 'Smart Search',
            description: 'Vector and graph-based search across your knowledge base',
            icon: Search,
            href: '/search',
        },
        {
            title: 'Q&A Assistant',
            description: 'Get answers with citations and interact with AI agents',
            icon: MessageSquare,
            href: '/qa',
        },
        {
            title: 'Learning Roadmaps',
            description: 'Generate personalized learning paths for any domain',
            icon: Map,
            href: '/roadmap',
        },
    ];

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-bold tracking-tight">
                    Welcome to KG-RAG
                </h1>
                <p className="mt-2 text-lg text-muted-foreground">
                    Knowledge Graph Retrieval-Augmented Generation System
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {features.map((feature) => (
                    <Link key={feature.title} to={feature.href}>
                        <Card className="transition-all hover:shadow-lg">
                            <CardHeader>
                                <div className="flex items-center gap-4">
                                    <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                                        <feature.icon className="h-6 w-6" />
                                    </div>
                                    <div>
                                        <CardTitle>{feature.title}</CardTitle>
                                        <CardDescription>{feature.description}</CardDescription>
                                    </div>
                                </div>
                            </CardHeader>
                        </Card>
                    </Link>
                ))}
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="h-5 w-5" />
                        Getting Started
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <h3 className="font-semibold">1. Upload Documents</h3>
                        <p className="text-sm text-muted-foreground">
                            Start by uploading PDF documents to build your knowledge base
                        </p>
                    </div>
                    <div>
                        <h3 className="font-semibold">2. Search & Explore</h3>
                        <p className="text-sm text-muted-foreground">
                            Use vector or graph search to find relevant information
                        </p>
                    </div>
                    <div>
                        <h3 className="font-semibold">3. Ask Questions</h3>
                        <p className="text-sm text-muted-foreground">
                            Get AI-powered answers with citations from your documents
                        </p>
                    </div>
                    <div>
                        <h3 className="font-semibold">4. Generate Roadmaps</h3>
                        <p className="text-sm text-muted-foreground">
                            Create personalized learning paths based on your knowledge graph
                        </p>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
