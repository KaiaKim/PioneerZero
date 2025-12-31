import React, { useState, useRef, useEffect } from 'react';
import { useGame } from '../hooks/useGame';
import { useAuth } from '../hooks/useAuth';
import '../../style/global.css';
import '../../style/room.css';

function GameRoom() {
  const { gameData, chatMessages, characters, guestNumber, sendMessage, chatLogRef } = useGame();
  const { loginSIWG } = useAuth();
  const [chatInput, setChatInput] = useState('');
  const [showFloor3D, setShowFloor3D] = useState(false);
  const [showWaitingRoom, setShowWaitingRoom] = useState(true);
  const chatInputRef = useRef(null);

  // Create floor grid cells
  const xyCells = ['Y1', 'Y2', 'Y3', 'Y4', 'X1', 'X2', 'X3', 'X4'];
  const abCells = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4'];

  // Handle chat input keydown
  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (sendMessage(chatInput)) {
        setChatInput('');
      }
    }
  };

  // Load tokens onto floor grid
  useEffect(() => {
    // This will be handled by CSS and the characters state
    // Tokens are rendered as part of the floor grid
  }, [characters]);

  return (
    <div className="game-screen">
      <div className="left-menu">
        <button id="btn-siwg" onClick={loginSIWG}>
          <img src="/images/google2.png" alt="Google" />
          Sign in with Google
        </button>
      </div>
      <div className="game-container">
        <textarea
          id="vomit-box"
          readOnly
          value={gameData ? JSON.stringify(gameData, null, 2) : 'Game data will appear here.'}
        />
        <audio
          id="bgm"
          src="/audio/Lookfar - Mineral Hall - 02 Petrified Wood.mp3"
          controls
          loop
        />
        <h1 className="timer">00:00</h1>

        {showWaitingRoom && (
          <div className="waiting-room" style={{ display: 'flex' }}>
            <div className="waiting-grid">
              {[1, 2, 3, 4].map((num) => (
                <div key={num} className="waiting-cell">
                  <div className="waiting-thumbnail">
                    <button id="player-join-but">Join</button>
                    <button id="add-robot-but">Bot</button>
                  </div>
                  <label className="waiting-name">P{num}</label>
                  <label className="waiting-ready-label">
                    Ready
                    <input type="checkbox" className="waiting-ready" />
                  </label>
                </div>
              ))}
            </div>
            <label className="start-label">Starting in 3...</label>
          </div>
        )}

        <div className="spectate-list">
          <label className="spectate-label">Spectate</label>
          <ul className="spectate-items">
            {[1, 2, 3, 4, 5].map((num) => (
              <li key={num}>P{num}</li>
            ))}
          </ul>
        </div>

        {showFloor3D && (
          <div className="floor-3d">
            <div className="parent-grid">
              <div className="section xy-section">
                <div className="grid-3d">
                  {xyCells.map((cellId) => {
                    const cellCharacter = characters.find(c => c.pos === cellId);
                    return (
                      <div key={cellId} className="cell">
                        {cellId}
                        {cellCharacter && (
                          <img
                            src={cellCharacter.token_image}
                            alt={cellCharacter.name}
                            className="token"
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="section ab-section">
                <div className="grid-3d">
                  {abCells.map((cellId) => {
                    const cellCharacter = characters.find(c => c.pos === cellId);
                    return (
                      <div key={cellId} className="cell">
                        {cellId}
                        {cellCharacter && (
                          <img
                            src={cellCharacter.token_image}
                            alt={cellCharacter.name}
                            className="token"
                          />
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
      <div className="right-menu">&gt;|</div>
      <div className="right-panel">
        <div ref={chatLogRef} id="chat-log" className="chat-log-container">
          {chatMessages.map((msg, index) => (
            <div key={index} className={`chat-message ${msg.isSystem ? 'system' : ''}`}>
              <div className="chat-message-header">
                <span className="chat-message-name">{msg.sender}</span>
                <span className="chat-message-time">{msg.time}</span>
              </div>
              <div className="chat-message-content">{msg.content}</div>
            </div>
          ))}
        </div>
        <div>
          <label>
            <input type="checkbox" id="all-checkbox" /> All
          </label>
          <label>
            <input type="checkbox" id="system-checkbox" /> System
          </label>
          <label>
            <input type="checkbox" id="chat-checkbox" /> Chat
          </label>
          <label>
            <input type="checkbox" id="story-checkbox" /> Story
          </label>
        </div>
        <div>
          <img
            src="/images/pikita_token.png"
            alt="character image"
            className="profile-image"
          />
          <label id="chat-char">{guestNumber !== 'noname' ? `Guest ${guestNumber}` : 'noname'}</label>
          <button onClick={() => sendMessage(chatInput) && setChatInput('')}>
            Send
          </button>
        </div>
        <textarea
          ref={chatInputRef}
          type="text"
          id="chat-input"
          placeholder="Type your message here..."
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={handleChatKeyDown}
        />
      </div>
    </div>
  );
}

export default GameRoom;

