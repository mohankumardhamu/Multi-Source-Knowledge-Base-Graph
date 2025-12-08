import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Map, Loader2 } from 'lucide-react';
import { qaService } from '@/services/qa';
import { RoadmapResponse } from '@/types/api';

export function RoadmapPage() {
    const [domain, setDomain] = useState('');
    const [roadmap, setRoadmap] = useState<RoadmapResponse | null>(null);
    const [loading, setLoading] = useState(false);

    const handleGenerate = async () => {
        if (!domain) return;
        setLoading(true);
        try {
            const result = await qaService.getRoadmap(domain);
            setRoadmap(result);
        } catch (error) {
            console.error('Failed to get roadmap:', error);
            // Try generating if it doesn't exist
            try {
                const generated = await qaService.generateRoadmap({ domain });
                setRoadmap(generated);
            } catch (genError) {
                console.error('Failed to generate roadmap:', genError);
                alert('Failed to get or generate roadmap. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    // Group nodes by week
    const nodesByWeek = roadmap?.nodes.reduce((acc, node) => {
        if (!acc[node.week]) {
            acc[node.week] = [];
        }
        acc[node.week].push(node);
        return acc;
    }, {} as Record<number, typeof roadmap.nodes>);

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Learning Roadmap</h1>
                <p className="text-muted-foreground">
                    Generate personalized learning paths for any domain
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Map className="h-5 w-5" />
                        Generate Roadmap
                    </CardTitle>
                    <CardDescription>
                        Enter a domain to generate or view a learning roadmap
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <label className="text-sm font-medium">Domain</label>
                        <Input
                            placeholder="e.g., python, machine-learning, web-development"
                            value={domain}
                            onChange={(e) => setDomain(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
                            className="mt-1"
                        />
                    </div>
                    <Button onClick={handleGenerate} disabled={loading || !domain}>
                        {loading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Loading...
                            </>
                        ) : (
                            'Get Roadmap'
                        )}
                    </Button>
                </CardContent>
            </Card>

            {roadmap && nodesByWeek && (
                <div className="space-y-6">
                    <h2 className="text-2xl font-bold">Roadmap: {roadmap.domain}</h2>
                    {Object.keys(nodesByWeek)
                        .sort((a, b) => Number(a) - Number(b))
                        .map((week) => (
                            <Card key={week}>
                                <CardHeader>
                                    <CardTitle>Week {week}</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <ul className="space-y-2">
                                        {nodesByWeek[Number(week)].map((node) => (
                                            <li key={node.id} className="flex items-start gap-2">
                                                <div className="mt-1 h-2 w-2 rounded-full bg-primary" />
                                                <div>
                                                    <p className="font-medium">{node.label}</p>
                                                    <p className="text-sm text-muted-foreground">
                                                        {node.hours} hours
                                                    </p>
                                                </div>
                                            </li>
                                        ))}
                                    </ul>
                                </CardContent>
                            </Card>
                        ))}
                </div>
            )}
        </div>
    );
}
