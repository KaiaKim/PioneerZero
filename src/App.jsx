import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Lobby from './components/lobby';
import Room from './components/room';
import MyCharacter from './components/MyCharacter';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/room/:gameId" element={<Room />} />
        <Route path="/edit-character" element={<MyCharacter />} />
      </Routes>
    </Router>
  );
}

export default App;

