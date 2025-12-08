import apiClient from './api';
import {
    DocumentUploadResponse,
    IngestionStatus,
    BulkUploadResponse,
} from '@/types/api';

export const documentsService = {
    /**
     * Upload a single PDF document
     */
    async uploadDocument(
        file: File,
        title: string,
        domain?: string
    ): Promise<DocumentUploadResponse> {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('title', title);
        if (domain) {
            formData.append('domain', domain);
        }

        const response = await apiClient.post<DocumentUploadResponse>(
            '/v1/docs',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    },

    /**
     * Upload multiple PDF documents
     */
    async uploadDocumentsBulk(
        files: File[],
        domain?: string
    ): Promise<BulkUploadResponse> {
        const formData = new FormData();
        files.forEach((file) => {
            formData.append('files', file);
        });
        if (domain) {
            formData.append('domain', domain);
        }

        const response = await apiClient.post<BulkUploadResponse>(
            '/v1/docs/bulk',
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    },

    /**
     * Get document ingestion status
     */
    async getDocumentStatus(docId: string): Promise<IngestionStatus> {
        const response = await apiClient.get<IngestionStatus>(
            `/v1/docs/${docId}/status`
        );
        return response.data;
    },
};
