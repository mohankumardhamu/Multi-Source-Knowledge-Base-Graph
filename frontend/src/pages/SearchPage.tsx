import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Search as SearchIcon, Database } from 'lucide-react';
import { searchService } from '@/services/search';
import type { VectorSearchResponse, GraphSearchResponse } from '@/types/api';

export function SearchPage() {
    const [activeTab, setActiveTab] = useState<'vector' | 'graph'>('vector');
    const [vectorQuery, setVectorQuery] = useState('');
    const [vectorDomain, setVectorDomain] = useState('');
    const [vectorResults, setVectorResults] = useState<VectorSearchResponse | null>(null);
    const [graphQuery, setGraphQuery] = useState('MATCH (t:Topic)-[:REFINES]->(d:Domain) RETURN t.name, d.name LIMIT 50');
    const [graphResults, setGraphResults] = useState<GraphSearchResponse | null>(null);
    const [loading, setLoading] = useState(false);

    const handleVectorSearch = async () => {
        if (!vectorQuery || !vectorDomain) return;
        setLoading(true);
        try {
            const results = await searchService.vectorSearch({
                query: vectorQuery,
                domain: vectorDomain,
                top_k: 10,
            });
            setVectorResults(results);
        } catch (error) {
            console.error('Search failed:', error);
            alert('Search failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleGraphSearch = async () => {
        if (!graphQuery) return;
        setLoading(true);
        try {
            const results = await searchService.graphSearch({
                cypher: graphQuery,
            });
            setGraphResults(results);
        } catch (error) {
            console.error('Search failed:', error);
            alert('Search failed. Please check your Cypher query.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Search</h1>
                <p className="text-muted-foreground">
                    Search your knowledge base using vector or graph queries
                </p>
            </div>

            <div className="flex gap-2">
                <Button
                    variant={activeTab === 'vector' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('vector')}
                >
                    <SearchIcon className="mr-2 h-4 w-4" />
                    Vector Search
                </Button>
                <Button
                    variant={activeTab === 'graph' ? 'default' : 'outline'}
                    onClick={() => setActiveTab('graph')}
                >
                    <Database className="mr-2 h-4 w-4" />
                    Graph Search
                </Button>
            </div>

            {activeTab === 'vector' && (
                <Card>
                    <CardHeader>
                        <CardTitle>Vector Search</CardTitle>
                        <CardDescription>
                            Search for similar content using semantic similarity
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="text-sm font-medium">Query</label>
                            <Input
                                placeholder="Enter your search query..."
                                value={vectorQuery}
                                onChange={(e) => setVectorQuery(e.target.value)}
                                className="mt-1"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium">Domain</label>
                            <Input
                                placeholder="e.g., python, javascript"
                                value={vectorDomain}
                                onChange={(e) => setVectorDomain(e.target.value)}
                                className="mt-1"
                            />
                        </div>
                        <Button onClick={handleVectorSearch} disabled={loading}>
                            {loading ? 'Searching...' : 'Search'}
                        </Button>

                        {vectorResults && (
                            <div className="mt-6 space-y-4">
                                <h3 className="font-semibold">Results ({vectorResults.hits.length})</h3>
                                {vectorResults.hits.map((hit, index) => (
                                    <Card key={index}>
                                        <CardContent className="pt-6">
                                            <div className="space-y-2">
                                                <div className="flex items-center justify-between">
                                                    <span className="text-sm font-medium">Score: {hit.score.toFixed(4)}</span>
                                                </div>
                                                <p className="text-sm">{hit.payload.content || 'No content'}</p>
                                                {hit.payload.page_from && (
                                                    <p className="text-xs text-muted-foreground">
                                                        Pages: {hit.payload.page_from} - {hit.payload.page_to}
                                                    </p>
                                                )}
                                            </div>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}

            {activeTab === 'graph' && (
                <Card>
                    <CardHeader>
                        <CardTitle>Graph Search</CardTitle>
                        <CardDescription>
                            Execute read-only Cypher queries on the knowledge graph
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div>
                            <label className="text-sm font-medium">Cypher Query</label>
                            <textarea
                                className="mt-1 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                                rows={6}
                                value={graphQuery}
                                onChange={(e) => setGraphQuery(e.target.value)}
                            />
                        </div>
                        <Button onClick={handleGraphSearch} disabled={loading}>
                            {loading ? 'Executing...' : 'Execute Query'}
                        </Button>

                        {graphResults && (
                            <div className="mt-6">
                                <h3 className="mb-2 font-semibold">Results</h3>
                                <div className="overflow-x-auto">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="border-b">
                                                {graphResults.columns.map((col) => (
                                                    <th key={col} className="p-2 text-left font-medium">
                                                        {col}
                                                    </th>
                                                ))}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {graphResults.rows.map((row, index) => (
                                                <tr key={index} className="border-b">
                                                    {row.map((cell, cellIndex) => (
                                                        <td key={cellIndex} className="p-2">
                                                            {JSON.stringify(cell)}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
