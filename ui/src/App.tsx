import Chat from './components/Chat';

function App() {
	return (
		<main className="app-shell">
			<header>
				<h1>TSP Copilot</h1>
				<p>Posez vos questions procédés et recevez des recommandations contextualisées.</p>
			</header>
			<Chat />
		</main>
	);
}

export default App;
