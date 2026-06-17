import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, HardDrive, Activity } from 'lucide-react';
import { adminService } from '@/services/admin';
import type { AdminOverview } from '@/types/api';

export function AdminPage() {
    const [overview, setOverview] = useState<AdminOverview | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadOverview();
    }, []);

    const loadOverview = async () => {
        try {
            const data = await adminService.getOverview();
            setOverview(data);
        } catch (error) {
            console.error('Failed to load overview:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="p-6">Loading...</div>;
    }

    if (!overview) {
        return <div className="p-6">Failed to load system overview</div>;
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Admin Dashboard</h1>
                <p className="text-muted-foreground">
                    System overview and metrics
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Database className="h-5 w-5" />
                            Qdrant
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{overview.qdrant.total_points}</div>
                        <p className="text-sm text-muted-foreground">Total vectors</p>
                        <div className="mt-4 space-y-1">
                            {overview.qdrant.collections.map((col) => (
                                <div key={col.name} className="text-sm">
                                    {col.name}: {col.points_count}
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Activity className="h-5 w-5" />
                            Neo4j
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{overview.neo4j.nodes}</div>
                        <p className="text-sm text-muted-foreground">Nodes</p>
                        <div className="mt-2 text-2xl font-bold">{overview.neo4j.relationships}</div>
                        <p className="text-sm text-muted-foreground">Relationships</p>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <HardDrive className="h-5 w-5" />
                            Redis
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{overview.redis.keys_count}</div>
                        <p className="text-sm text-muted-foreground">Keys</p>
                    </CardContent>
                </Card>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Documents</CardTitle>
                    <CardDescription>
                        {overview.documents.length} documents in the system
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b">
                                    <th className="p-2 text-left font-medium">Title</th>
                                    <th className="p-2 text-left font-medium">Domain</th>
                                    <th className="p-2 text-left font-medium">Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {overview.documents.slice(0, 10).map((doc) => (
                                    <tr key={doc.id} className="border-b">
                                        <td className="p-2">{doc.title}</td>
                                        <td className="p-2">{doc.domain || '-'}</td>
                                        <td className="p-2">
                                            <span className={`rounded-full px-2 py-1 text-xs ${doc.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                    doc.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                                                        doc.status === 'queued' ? 'bg-yellow-100 text-yellow-800' :
                                                            'bg-gray-100 text-gray-800'
                                                }`}>
                                                {doc.status}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            <Card>
                <CardHeader>
                    <CardTitle>PostgreSQL Tables</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-2 md:grid-cols-2">
                        {Object.entries(overview.postgres).map(([table, count]) => (
                            <div key={table} className="flex justify-between rounded-md border p-2">
                                <span className="text-sm font-medium">{table}</span>
                                <span className="text-sm text-muted-foreground">{count} rows</span>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
