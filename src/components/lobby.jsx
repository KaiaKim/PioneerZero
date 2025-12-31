import React from 'react';
import { useLobby } from '../hooks/useLobby';
import Auth from './auth';
import '../../style/global.css';
import '../../style/lobby.css';

function Lobby() {
  const { sessions, createGame, killDB, openGameRoom } = useLobby();

  return (
    <div>
      <Auth />
      <div className="selection-screen">
        <h1>Game Lobby</h1>
        <button onClick={createGame}>New Game</button>
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

