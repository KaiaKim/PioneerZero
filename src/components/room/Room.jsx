import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../hooks/useAuth';
import { useGame } from '../../hooks/useGame';
import Auth from '../auth';
import WaitingArea from './WaitingArea';
import FloorArea from './FloorArea';
import '../../../style/global.css';
import '../../../style/room.css';

function Room() {
  const { gameData, chatMessages, characters, users, players, actions, chatLogRef } = useGame();
  const { user, googleLogin, googleLogout } = useAuth();
  const [chatInput, setChatInput] = useState('');
  const [showFloorArea, setShowFloorArea] = useState(false);
  const [showWaitingArea, setShowWaitingArea] = useState(true);
  const chatInputRef = useRef(null);

  // Handle chat input keydown
  const handleChatKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (actions.sendChat(chatInput)) {
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
        <Auth />
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

        {showWaitingArea && <WaitingArea players={players} addBotToSlot={actions.addBotToSlot} joinPlayerSlot={actions.joinPlayerSlot} leavePlayerSlot={actions.leavePlayerSlot} setReady={actions.setReady} currentUser={user} />}

        <div className="user-list">
          <label className="user-label">접속자 목록 ↓</label>
          <ul className="user-items">
            {users.map((userItem) => (
              <li key={userItem.id}>{userItem.name || userItem.email || 'Guest'}</li>
            ))}
          </ul>
        </div>

        {showFloorArea && <FloorArea characters={characters} />}
      </div>
      <div className="right-menu">&gt;|</div>
      <div className="right-panel">
        <div ref={chatLogRef} id="chat-log" className="chat-log-container">
          {chatMessages.map((msg, index) => {
            const isCurrentUser = user && msg.user_id && user.id === msg.user_id;
            return (
              <div key={index} className={`chat-message ${msg.isSystem ? 'system' : ''} ${isCurrentUser ? 'own-message' : ''}`}>
                <div className="chat-message-header">
                  <span className="chat-message-name">{msg.sender}</span>
                  <span className="chat-message-time">{msg.time}</span>
                </div>
                <div className="chat-message-content">{msg.content}</div>
              </div>
            );
          })}
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
          <label id="chat-char">{user ? user.name : 'noname'}</label>
          <button onClick={() => actions.sendChat(chatInput)}>
            Send
          </button>
        </div>
        <textarea
          ref={chatInputRef}
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

export default Room;