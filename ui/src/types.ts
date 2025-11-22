export type Role = 'user' | 'assistant' | 'system';

export interface SourcePayload {
	type: string;
	title: string;
	excerpt: string;
	metadata: Record<string, unknown>;
}

export interface RecommendationBlock {
	action: string;
	impact: string;
	risks: string;
	prerequisites: string;
}

export interface ChatMessage {
	id: string;
	role: Role;
	text: string;
	sources?: SourcePayload[];
	recommendations?: RecommendationBlock[];
}

export interface ChatResponsePayload {
	intent: string;
	confidence: number;
	answer: string;
	sources: SourcePayload[];
	recommendations: RecommendationBlock[];
}

export interface ChatRequestPayload {
	message: string;
	session_id?: string;
	max_sources?: number;
}
