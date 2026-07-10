import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { RefreshCw, Loader2 } from 'lucide-react';
import { documentsService } from '@/services/documents';
import type { DocumentListItem } from '@/types/api';

const STATUS_STYLES: Record<string, string> = {
    completed: 'bg-green-100 text-green-800',
    processing: 'bg-blue-100 text-blue-800',
    pending: 'bg-yellow-100 text-yellow-800',
    queued: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
};

function StatusBadge({ status }: { status: string }) {
    return (
        <span
            className={`rounded-full px-2 py-1 text-xs ${STATUS_STYLES[status] ?? 'bg-gray-100 text-gray-800'}`}
        >
            {status}
        </span>
    );
}

function formatDate(value?: string | null): string {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

export function DocumentLibraryPage() {
    const [documents, setDocuments] = useState<DocumentListItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadDocuments = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await documentsService.listDocuments();
            setDocuments(data);
        } catch (err) {
            console.error('Failed to load documents:', err);
            setError('Failed to load documents. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadDocuments();
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight">Document Library</h1>
                    <p className="text-muted-foreground">
                        All uploaded documents and their embedding status
                    </p>
                </div>
                <Button variant="outline" size="sm" onClick={loadDocuments} disabled={loading}>
                    {loading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                        <RefreshCw className="mr-2 h-4 w-4" />
                    )}
                    Refresh
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Documents</CardTitle>
                    <CardDescription>
                        {loading ? 'Loading...' : `${documents.length} document${documents.length === 1 ? '' : 's'}`}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {error && <p className="text-sm text-destructive">{error}</p>}
                    {!error && !loading && documents.length === 0 && (
                        <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
                    )}
                    {!error && documents.length > 0 && (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="border-b">
                                        <th className="p-2 text-left font-medium">Title</th>
                                        <th className="p-2 text-left font-medium">Domain</th>
                                        <th className="p-2 text-left font-medium">Uploaded</th>
                                        <th className="p-2 text-left font-medium">Status</th>
                                        <th className="p-2 text-left font-medium">Embedding Status</th>
                                        <th className="p-2 text-right font-medium">Total Pages</th>
                                        <th className="p-2 text-right font-medium">Embedding Count</th>
                                        <th className="p-2 text-left font-medium">Embedding Model</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {documents.map((doc) => (
                                        <tr key={doc.id} className="border-b">
                                            <td className="p-2">{doc.title}</td>
                                            <td className="p-2">{doc.domain || '-'}</td>
                                            <td className="p-2">{formatDate(doc.uploaded_at)}</td>
                                            <td className="p-2">
                                                <StatusBadge status={doc.status} />
                                            </td>
                                            <td className="p-2">
                                                <StatusBadge status={doc.embedding_status} />
                                            </td>
                                            <td className="p-2 text-right">{doc.total_pages}</td>
                                            <td className="p-2 text-right">{doc.embedding_count}</td>
                                            <td className="p-2">{doc.embedding_model}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
