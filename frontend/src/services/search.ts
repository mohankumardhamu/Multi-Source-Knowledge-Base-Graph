import apiClient from './api';
import type {
    VectorSearchRequest,
    VectorSearchResponse,
    GraphSearchRequest,
    GraphSearchResponse,
} from '@/types/api';

export const searchService = {
    /**
     * Perform vector similarity search
     */
    async vectorSearch(
        request: VectorSearchRequest
    ): Promise<VectorSearchResponse> {
        const response = await apiClient.post<VectorSearchResponse>(
            '/v1/search/vector',
            request
        );
        return response.data;
    },

    /**
     * Execute read-only Cypher query
     */
    async graphSearch(
        request: GraphSearchRequest
    ): Promise<GraphSearchResponse> {
        const response = await apiClient.post<GraphSearchResponse>(
            '/v1/search/graph',
            request
        );
        return response.data;
    },
};
