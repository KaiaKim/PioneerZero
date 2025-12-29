import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Lobby from './components/lobby';
import GameRoom from './components/gameRoom';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/room/:gameId" element={<GameRoom />} />
      </Routes>
    </Router>
  );
}

export default App;

