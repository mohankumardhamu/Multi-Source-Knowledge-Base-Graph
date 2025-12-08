import apiClient from './api';
import {
    AnswerRequest,
    AnswerResponse,
    AgentRequest,
    AgentResponse,
    GenerateQuestionsRequest,
    GenerateResponse,
    QuestionOut,
    RoadmapResponse,
    GenerateRoadmapRequest,
} from '@/types/api';

export const qaService = {
    /**
     * Get an answer with citations
     */
    async getAnswer(request: AnswerRequest): Promise<AnswerResponse> {
        const response = await apiClient.post<AnswerResponse>(
            '/v1/answer',
            request
        );
        return response.data;
    },

    /**
     * Interact with the agent
     */
    async askAgent(request: AgentRequest): Promise<AgentResponse> {
        const response = await apiClient.post<AgentResponse>(
            '/v1/agent/ask',
            request
        );
        return response.data;
    },

    /**
     * Generate questions for a domain/topic
     */
    async generateQuestions(
        request: GenerateQuestionsRequest
    ): Promise<GenerateResponse> {
        const response = await apiClient.post<GenerateResponse>(
            '/v1/generate/questions',
            request
        );
        return response.data;
    },

    /**
     * Get a specific question by ID
     */
    async getQuestion(questionId: string): Promise<QuestionOut> {
        const response = await apiClient.get<QuestionOut>(
            `/v1/questions/${questionId}`
        );
        return response.data;
    },

    /**
     * Generate a learning roadmap
     */
    async generateRoadmap(
        request: GenerateRoadmapRequest
    ): Promise<RoadmapResponse> {
        const response = await apiClient.post<RoadmapResponse>(
            '/v1/generate/roadmap',
            request
        );
        return response.data;
    },

    /**
     * Get an existing roadmap for a domain
     */
    async getRoadmap(domain: string): Promise<RoadmapResponse> {
        const response = await apiClient.get<RoadmapResponse>(
            `/v1/roadmaps/${domain}`
        );
        return response.data;
    },
};
