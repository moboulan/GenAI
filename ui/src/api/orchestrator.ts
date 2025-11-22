import type { ChatRequestPayload, ChatResponsePayload } from '../types';

const DEFAULT_BASE_URL = 'http://localhost:8010';

function getBaseUrl(): string {
	const envUrl = import.meta.env.VITE_ORCH_BASE_URL as string | undefined;
	return envUrl?.trim() || DEFAULT_BASE_URL;
}

export async function sendChat(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
	const response = await fetch(`${getBaseUrl()}/chat`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
		},
		body: JSON.stringify(payload),
	});

	if (!response.ok) {
		const detail = await response.text();
		throw new Error(detail || 'Erreur lors de la réponse orchestrateur');
	}

	return (await response.json()) as ChatResponsePayload;
}
