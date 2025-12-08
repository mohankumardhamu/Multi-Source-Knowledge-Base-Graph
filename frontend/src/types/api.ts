// Document Management Types
export interface Document {
    id: string;
    title: string;
    domain?: string;
    s3_bucket: string;
    s3_key: string;
    checksum_sha256: string;
    status: string;
    created_at?: string;
    updated_at?: string;
}

export interface IngestionStatus {
    status: string;
    stages: {
        events: Array<{
            stage: string;
            status: string;
            timestamp: string;
            message?: string;
        }>;
    };
}

export interface DocumentUploadResponse {
    id: string;
    status: string;
}

export interface BulkUploadResult {
    filename: string;
    id?: string;
    status?: string;
    error?: string;
}

export interface BulkUploadResponse {
    results: BulkUploadResult[];
}

// Search Types
export interface VectorSearchRequest {
    query: string;
    domain: string;
    top_k?: number;
    filters?: Record<string, any>;
}

export interface VectorSearchHit {
    score: number;
    payload: {
        doc_id?: string;
        chunk_id?: string;
        content?: string;
        page_from?: number;
        page_to?: number;
        heading_path?: string[];
        [key: string]: any;
    };
    preview_url: string;
}

export interface VectorSearchResponse {
    hits: VectorSearchHit[];
}

export interface GraphSearchRequest {
    cypher: string;
    params?: Record<string, any>;
}

export interface GraphSearchResponse {
    columns: string[];
    rows: any[][];
}

// Q&A Types
export interface AnswerRequest {
    query: string;
    domain?: string;
    top_k?: number;
}

export interface Citation {
    doc_id: string;
    page_from?: number;
    page_to?: number;
    heading_path?: string[];
}

export interface AnswerResponse {
    answer: string;
    citations: Citation[];
    metrics: {
        p50_ms: number;
        p95_ms: number;
    };
}

// Agent Types
export interface AgentRequest {
    query: string;
    mode?: 'qa' | 'tutor' | 'interview';
    domain?: string;
}

export interface AgentResponse {
    response: string;
    mode: string;
    [key: string]: any;
}

// Roadmap Types
export interface RoadmapNode {
    id: string;
    label: string;
    topic: string;
    week: number;
    hours: number;
}

export interface RoadmapEdge {
    from: string;
    to: string;
    type: string;
}

export interface RoadmapResponse {
    domain: string;
    nodes: RoadmapNode[];
    edges: RoadmapEdge[];
}

export interface GenerateRoadmapRequest {
    domain: string;
}

// Question Generation Types
export interface GenerateQuestionsRequest {
    domain: string;
    topic?: string;
    count?: number;
}

export interface GenerateResponse {
    questions: string[];
    status: 'vector' | 'fallback';
}

export interface QuestionOut {
    id: string;
    question: string;
    domain: string;
    topic?: string;
    created_at: string;
}

// Admin Types
export interface AdminOverview {
    documents: Document[];
    qdrant: {
        collections: Array<{
            name: string;
            points_count: number;
        }>;
        total_points: number;
    };
    neo4j: {
        nodes: number;
        relationships: number;
    };
    redis: {
        keys_count: number;
    };
    postgres: Record<string, number>;
}

// Health Types
export interface HealthResponse {
    status: string;
    timestamp: string;
}
