import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { MessageSquare, Send } from 'lucide-react';
import { qaService } from '@/services/qa';
import { AnswerResponse } from '@/types/api';

export function QAPage() {
    const [query, setQuery] = useState('');
    const [domain, setDomain] = useState('');
    const [answer, setAnswer] = useState<AnswerResponse | null>(null);
    const [loading, setLoading] = useState(false);

    const handleAsk = async () => {
        if (!query) return;
        setLoading(true);
        try {
            const result = await qaService.getAnswer({
                query,
                domain: domain || undefined,
                top_k: 5,
            });
            setAnswer(result);
        } catch (error) {
            console.error('Failed to get answer:', error);
            alert('Failed to get answer. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Q&A Assistant</h1>
                <p className="text-muted-foreground">
                    Ask questions and get answers with citations from your knowledge base
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <MessageSquare className="h-5 w-5" />
                        Ask a Question
                    </CardTitle>
                    <CardDescription>
                        Enter your question and optionally specify a domain
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <label className="text-sm font-medium">Question</label>
                        <Input
                            placeholder="What would you like to know?"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
                            className="mt-1"
                        />
                    </div>
                    <div>
                        <label className="text-sm font-medium">Domain (optional)</label>
                        <Input
                            placeholder="e.g., python, javascript"
                            value={domain}
                            onChange={(e) => setDomain(e.target.value)}
                            className="mt-1"
                        />
                    </div>
                    <Button onClick={handleAsk} disabled={loading || !query}>
                        {loading ? (
                            'Thinking...'
                        ) : (
                            <>
                                <Send className="mr-2 h-4 w-4" />
                                Ask
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>

            {answer && (
                <Card>
                    <CardHeader>
                        <CardTitle>Answer</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="whitespace-pre-wrap rounded-md bg-muted p-4">
                            {answer.answer}
                        </div>

                        {answer.citations.length > 0 && (
                            <div>
                                <h3 className="mb-2 font-semibold">Citations</h3>
                                <div className="space-y-2">
                                    {answer.citations.map((citation, index) => (
                                        <Card key={index}>
                                            <CardContent className="pt-4">
                                                <p className="text-sm">
                                                    <span className="font-medium">Document:</span> {citation.doc_id}
                                                </p>
                                                {citation.page_from && (
                                                    <p className="text-sm text-muted-foreground">
                                                        Pages: {citation.page_from} - {citation.page_to}
                                                    </p>
                                                )}
                                                {citation.heading_path && citation.heading_path.length > 0 && (
                                                    <p className="text-sm text-muted-foreground">
                                                        Path: {citation.heading_path.join(' > ')}
                                                    </p>
                                                )}
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            </div>
                        )}

                        <div className="text-xs text-muted-foreground">
                            Response time: p50={answer.metrics.p50_ms.toFixed(0)}ms, p95={answer.metrics.p95_ms.toFixed(0)}ms
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
