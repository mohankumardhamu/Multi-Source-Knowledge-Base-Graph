import apiClient from './api';
import { AdminOverview, HealthResponse } from '@/types/api';

export const adminService = {
    /**
     * Get system overview with metrics
     */
    async getOverview(): Promise<AdminOverview> {
        const response = await apiClient.get<AdminOverview>('/v1/admin/overview');
        return response.data;
    },

    /**
     * Get health status
     */
    async getHealth(): Promise<HealthResponse> {
        const response = await apiClient.get<HealthResponse>('/health');
        return response.data;
    },

    /**
     * Re-run ingestion for a document
     */
    async rerunIngestion(docId: string): Promise<void> {
        await apiClient.post(`/admin/ingest/${docId}/rerun`);
    },
};
