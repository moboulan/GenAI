import React, { useCallback, useMemo, useRef, useState } from 'react';
import clsx from 'clsx';
import { v4 as uuid } from 'uuid';

import { sendChat } from '../api/orchestrator';
import type { ChatMessage } from '../types';

const DEFAULT_SESSION = uuid();

type PendingState = 'idle' | 'sending' | 'error';

export function Chat() {
	const [messages, setMessages] = useState<ChatMessage[]>([]);
	const [input, setInput] = useState('');
	const [status, setStatus] = useState<PendingState>('idle');
	const scrollRef = useRef<HTMLDivElement>(null);

	const lastAnswer = useMemo(() => {
		return messages.filter((msg: ChatMessage) => msg.role === 'assistant').pop();
	}, [messages]);

	const scrollToLatest = useCallback(() => {
		const container = scrollRef.current;
		if (container) {
			container.scrollTop = container.scrollHeight;
		}
	}, []);

	const handleSend = useCallback(async () => {
		if (!input.trim() || status === 'sending') {
			return;
		}
		const userMessage: ChatMessage = { id: uuid(), role: 'user', text: input.trim() };
		setMessages((prev) => [...prev, userMessage]);
		setInput('');
		setStatus('sending');
		scrollToLatest();
		try {
			const response = await sendChat({ message: userMessage.text, session_id: DEFAULT_SESSION });
			const assistantMessage: ChatMessage = {
				id: uuid(),
				role: 'assistant',
				text: response.answer,
				sources: response.sources,
				recommendations: response.recommendations,
			};
			setMessages((prev) => [...prev, assistantMessage]);
			setStatus('idle');
			scrollToLatest();
		} catch (error) {
			const assistantMessage: ChatMessage = {
				id: uuid(),
				role: 'system',
				text: error instanceof Error ? error.message : 'Erreur inconnue',
			};
			setMessages((prev) => [...prev, assistantMessage]);
			setStatus('error');
		}
	}, [input, scrollToLatest, status]);

	const handleKeyDown = useCallback(
		(event: React.KeyboardEvent<HTMLTextAreaElement>) => {
			if (event.key === 'Enter' && !event.shiftKey) {
				event.preventDefault();
				handleSend();
			}
		},
		[handleSend],
	);

	return (
		<div className="chat-shell">
			<div className="chat-messages" ref={scrollRef}>
				{messages.length === 0 && <p className="empty-state">Posez une question pour démarrer la session.</p>}
				{messages.map((message: ChatMessage) => (
					<article key={message.id} className={clsx('bubble', `bubble-${message.role}`)}>
						<header>
							<span>{message.role === 'user' ? 'Vous' : 'Copilote'}</span>
						</header>
						<p>{message.text}</p>
						{message.sources && message.sources.length > 0 && (
							<div className="sources">
								<strong>Sources</strong>
								<ul>
									{message.sources.map((source, index) => (
										<li key={`${message.id}-${source.title || index}`}>
											{source.title || `Source ${index + 1}`}
										</li>
									))}
								</ul>
							</div>
						)}
						{message.recommendations && message.recommendations.length > 0 && (
							<div className="recommendations">
								<strong>Recommandations</strong>
								<ul>
									{message.recommendations.map((rec, index) => (
										<li key={`${message.id}-${rec.action || index}`}>
											<span className="rec-action">{rec.action}</span>
											<span className="rec-meta">Impact: {rec.impact} | Risques: {rec.risks}</span>
										</li>
									))}
								</ul>
							</div>
						)}
					</article>
				))}
			</div>
			<div className="chat-composer">
				<textarea
					placeholder="Ex: Pourquoi le rendement baisse depuis 30 min ?"
					value={input}
					onChange={(event) => {
						setInput(event.currentTarget.value);
						if (status === 'error') {
							setStatus('idle');
						}
					}}
					onKeyDown={handleKeyDown}
					rows={3}
				/>
				<button type="button" onClick={handleSend} disabled={!input.trim() || status === 'sending'}>
					{status === 'sending' ? 'Envoi...' : 'Envoyer'}
				</button>
			</div>
			{lastAnswer?.sources && lastAnswer.sources.length > 0 && (
				<footer className="chat-footer">
					<p>
						Citations récentes:
						{lastAnswer.sources.map((source, index) => (
							<span key={`${source.title || index}`} className="chip">
								{source.title || `Source ${index + 1}`}
							</span>
						))}
					</p>
				</footer>
			)}
		</div>
	);
}

export default Chat;
