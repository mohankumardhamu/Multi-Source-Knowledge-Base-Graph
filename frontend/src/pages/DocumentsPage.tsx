import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Upload, FileText, Loader2 } from 'lucide-react';
import { documentsService } from '@/services/documents';

export function DocumentsPage() {
    const [uploading, setUploading] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [domain, setDomain] = useState('');

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            setSelectedFiles(Array.from(e.target.files));
        }
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;

        setUploading(true);
        try {
            if (selectedFiles.length === 1) {
                const title = selectedFiles[0].name.replace('.pdf', '');
                await documentsService.uploadDocument(
                    selectedFiles[0],
                    title,
                    domain || undefined
                );
            } else {
                await documentsService.uploadDocumentsBulk(
                    selectedFiles,
                    domain || undefined
                );
            }
            alert('Upload successful!');
            setSelectedFiles([]);
            setDomain('');
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Upload failed. Please try again.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">Documents</h1>
                <p className="text-muted-foreground">
                    Upload and manage your PDF documents
                </p>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>Upload Documents</CardTitle>
                    <CardDescription>
                        Upload PDF files to add them to your knowledge base
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div>
                        <label
                            htmlFor="file-upload"
                            className="flex h-32 cursor-pointer items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 transition-colors hover:border-muted-foreground/50"
                        >
                            <div className="text-center">
                                <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
                                <p className="mt-2 text-sm text-muted-foreground">
                                    Click to upload or drag and drop
                                </p>
                                <p className="text-xs text-muted-foreground">PDF files only</p>
                            </div>
                            <input
                                id="file-upload"
                                type="file"
                                className="hidden"
                                accept=".pdf"
                                multiple
                                onChange={handleFileChange}
                            />
                        </label>
                    </div>

                    {selectedFiles.length > 0 && (
                        <div className="space-y-2">
                            <p className="text-sm font-medium">Selected files:</p>
                            {selectedFiles.map((file, index) => (
                                <div
                                    key={index}
                                    className="flex items-center gap-2 rounded-md border p-2"
                                >
                                    <FileText className="h-4 w-4 text-muted-foreground" />
                                    <span className="text-sm">{file.name}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    <div>
                        <label htmlFor="domain" className="text-sm font-medium">
                            Domain (optional)
                        </label>
                        <Input
                            id="domain"
                            placeholder="e.g., python, javascript, machine-learning"
                            value={domain}
                            onChange={(e) => setDomain(e.target.value)}
                            className="mt-1"
                        />
                    </div>

                    <Button
                        onClick={handleUpload}
                        disabled={uploading || selectedFiles.length === 0}
                        className="w-full"
                    >
                        {uploading ? (
                            <>
                                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                Uploading...
                            </>
                        ) : (
                            <>
                                <Upload className="mr-2 h-4 w-4" />
                                Upload {selectedFiles.length > 0 && `(${selectedFiles.length})`}
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>
        </div>
    );
}
