import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useGame } from '../hooks/useGame';
import Auth from './auth';
import '../../style/global.css';
import '../../style/room.css';

function GameRoom() {
  const { gameData, chatMessages, characters, users, players, playerStatus, sendMessage, joinPlayerSlot, leavePlayerSlot, chatLogRef } = useGame();
  const { user, googleLogin, googleLogout } = useAuth();
  const [chatInput, setChatInput] = useState('');
  const [showFloor3D, setShowFloor3D] = useState(false);
  const [showWaitingRoom, setShowWaitingRoom] = useState(true);
  const chatInputRef = useRef(null);

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

        {showWaitingRoom && <WaitingRoom players={players} playerStatus={playerStatus} joinPlayerSlot={joinPlayerSlot} leavePlayerSlot={leavePlayerSlot} currentUser={user} />}

        <div className="user-list">
          <label className="user-label">접속자 목록 ↓</label>
          <ul className="user-items">
            {users.map((user) => (
              <li key={user.id}>{user.name || user.email || 'Guest'}</li>
            ))}
          </ul>
        </div>

        {showFloor3D && <Floor3D characters={characters} />}
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



function WaitingRoom({ players, playerStatus, joinPlayerSlot, leavePlayerSlot, currentUser }) {
  // Get user info from currentUser or localStorage as fallback
  const getUserInfo = () => {
    if (currentUser) return currentUser;
    const storedUser = localStorage.getItem('user_info');
    if (storedUser) {
      try {
        return JSON.parse(storedUser);
      } catch (e) {
        return null;
      }
    }
    return null;
  };

  const handleJoinClick = (slotNum) => {
    joinPlayerSlot(slotNum);
  };

  const handleLeaveClick = (slotNum) => {
    leavePlayerSlot(slotNum);
  };

  const getSlotStatus = (slotNum) => {
    const slotIndex = slotNum - 1;
    return playerStatus[slotIndex] || 0; // 0=empty, 1=occupied, 2=connection-lost
  };

  const isSlotEmpty = (slotNum) => {
    return getSlotStatus(slotNum) === 0;
  };

  const isSlotConnectionLost = (slotNum) => {
    return getSlotStatus(slotNum) === 2;
  };

  const isCurrentUserInSlot = (slotNum) => {
    const slotIndex = slotNum - 1;
    const player = players[slotIndex];
    const userInfo = getUserInfo();
    if (!player || !userInfo) return false;
    return player.id === userInfo.id;
  };

  const getPlayerName = (slotNum) => {
    const slotIndex = slotNum - 1;
    const player = players[slotIndex];
    if (!player) return '-';
    return player.name || player.email || 'Guest';
  };

  return (
    <div className="waiting-room" style={{ display: 'flex' }}>
      <div className="waiting-grid">
        {[1, 2, 3, 4].map((num) => {
          const status = getSlotStatus(num);
          const isEmpty = isSlotEmpty(num);
          const isConnectionLost = isSlotConnectionLost(num);
          const isCurrentUser = isCurrentUserInSlot(num);
          
          return (
            <div key={num} className="waiting-cell">
              <div 
                className={`waiting-thumbnail ${
                  status === 1 ? 'occupied' : 
                  status === 2 ? 'connection-lost' : 
                  ''
                }`}
              >
                {isEmpty ? (
                  <div>
                    <button 
                      className="player-join-but"
                      onClick={() => handleJoinClick(num)}
                    >
                      Join
                    </button>
                    <button className="add-robot-but">Bot</button>
                  </div>
                ) : (
                  isCurrentUser && status === 1 && (
                    <button 
                      className="player-leave-but"
                      onClick={() => handleLeaveClick(num)}
                    >
                      Leave
                    </button>
                  )
                )}
                {isConnectionLost && (
                  <div className="connection-lost-indicator">
                    <span className="thunder-emoji">⚡</span>
                  </div>
                )}
              </div>
              <label className="waiting-name" id={`player-name-${num}`}>
                {isEmpty ? '-' : getPlayerName(num)}
              </label>
              <label className="waiting-ready-label">
                Ready
                <input 
                  type="checkbox" 
                  className="waiting-ready" 
                  disabled={isEmpty || isConnectionLost} 
                />
              </label>
            </div>
          );
        })}
      </div>
      <label className="start-label">Starting in 3...</label>
    </div>
  );
}

function Floor3D({ characters }) {
  const xyCells = ['Y1', 'Y2', 'Y3', 'Y4', 'X1', 'X2', 'X3', 'X4'];
  const abCells = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4'];

  return (
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
  );
}