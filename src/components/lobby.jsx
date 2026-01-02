import React, { useState } from 'react';
import { useLobby } from '../hooks/useLobby';
import Auth from './auth';
import '../../style/global.css';
import '../../style/lobby.css';

function Lobby() {
  const { sessions, createGame, killDB, openGameRoom } = useLobby();
  const [playerNum, setPlayerNum] = useState(4);

  return (
    <div>
      <Auth />
      <div className="selection-screen">
        <h1>Game Lobby</h1>
        <div className="game-settings">
          <label>player num:</label>
          <select value={playerNum} onChange={(e) => setPlayerNum(Number(e.target.value))}>
            <option value={2}>2</option>
            <option value={4}>4</option>
            <option value={6}>6</option>
          </select>
        </div>
        <button onClick={() => createGame(playerNum)}>New Game</button>

        <button onClick={killDB}>Kill DB</button>
        <div id="session-list-container">
          <h2>Active Game Sessions</h2>
          <div id="session-list">
            {!sessions || sessions.length === 0 ? (
              <p style={{ color: '#666', fontStyle: 'italic' }}>
                No active game sessions. Click "New Game" to create one.
              </p>
            ) : (
              sessions.map((session) => {
                const gameId = session.game_id;
                return (
                  <div
                    key={gameId}
                    className="session-item"
                    onClick={() => openGameRoom(gameId)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="session-thumb">Preview</div>
                    <span className="session-id">Game: {gameId}</span>
                    <button
                      className="join-button"
                      onClick={(e) => {
                        e.stopPropagation();
                        openGameRoom(gameId);
                      }}
                    >
                      Join
                    </button>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Lobby;

