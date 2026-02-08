import React from 'react';
import { getUserInfo as getStoredUserInfo } from '../../storage';

function Slots({ players, joinPlayerSlot, addBotToSlot, leavePlayerSlot, setReady, currentUser, countdown }) {
  const getUserInfo = () => currentUser || getStoredUserInfo();

  const handleJoinClick = (slotIndex) => {
    joinPlayerSlot(slotIndex);
  };

  const handleAddBotClick = (slotIndex) => {
    addBotToSlot(slotIndex);
  };

  const handleLeaveClick = (slotIndex) => {
    leavePlayerSlot(slotIndex);
  };

  const getSlotStatus = (slotIndex) => {
    const player = players[slotIndex];
    return player?.occupy || 0; // 0=empty, 1=occupied, 2=connection-lost
  };

  const isSlotEmpty = (slotIndex) => {
    return getSlotStatus(slotIndex) === 0;
  };

  const isSlotConnectionLost = (slotIndex) => {
    return getSlotStatus(slotIndex) === 2;
  };

  const isCurrentUserInSlot = (slotIndex) => {
    const player = players[slotIndex];
    const userInfo = getUserInfo();
    if (!player || !player.info || !userInfo) return false;
    return player.info.id === userInfo.id;
  };

  const isBotInSlot = (slotIndex) => {
    const player = players[slotIndex];
    if (!player || !player.info) return false;
    return player.info.is_bot === true || (player.info.id && player.info.id.startsWith('bot_'));
  };

  const getCharName = (slotIndex) => {
    const player = players[slotIndex];
    if (!player) return '-';
    return player.character?.name || 'Guest';
  };

  const getPlayerReady = (slotIndex) => {
    const player = players[slotIndex];
    if (!player) return false;
    return player.ready === true;
  };

  const handleReadyChange = (slotIndex, event) => {
    const checked = event.target.checked;
    setReady(slotIndex, checked);
  };

  // 0-based slot indices
  const slotIndices = Array.from({ length: players.length || 4 }, (_, i) => i);
  
  const gridColumns = Math.floor((players.length || 4) / 2);

  return (
    <div className="waiting-area" style={{ display: 'flex' }}>
      <div className="waiting-grid" style={{ '--grid-columns': gridColumns }}>
        {slotIndices.map((slotIndex) => {
          const status = getSlotStatus(slotIndex);
          const isEmpty = isSlotEmpty(slotIndex);
          const isConnectionLost = isSlotConnectionLost(slotIndex);
          const isCurrentUser = isCurrentUserInSlot(slotIndex);
          const isBot = isBotInSlot(slotIndex);
          
          const player = players[slotIndex];
          const tokenImage = status === 1 && player?.character?.token_image 
            ? player.character.token_image 
            : null;
          
          const totalPlayers = players.length || 4;
          const teamClass = slotIndex < (totalPlayers / 2) ? 'teamBlue' : 'teamWhite';
          const displayNum = slotIndex + 1; // For "P1", "P2" labels

          return (
            <div key={slotIndex} className={`waiting-cell ${teamClass}`}>
              <div 
                className={`waiting-thumbnail ${
                  status === 1 ? 'occupied' : 
                  status === 2 ? 'connection-lost' : 
                  ''
                }`}
                style={tokenImage ? { '--token-image': `url(${tokenImage})` } : {}}
              >
                {isEmpty ? (
                  <div>
                    <button 
                      className="player-join-but"
                      onClick={() => handleJoinClick(slotIndex)}
                    >
                      Join
                    </button>
                    <button
                    className="add-bot-but"
                    onClick={() => handleAddBotClick(slotIndex)}
                    >Bot</button>
                  </div>
                ) : (
                  (isCurrentUser || isBot) && status === 1 && (
                    <button 
                      className="player-leave-but"
                      onClick={() => handleLeaveClick(slotIndex)}
                    >
                      X
                    </button>
                  )
                )}
                {isConnectionLost && (
                  <div className="connection-lost-indicator">
                    <span className="thunder-emoji">⚡</span>
                  </div>
                )}
              </div>
              <label className="waiting-name" id={`player-name-${displayNum}`}>
                {isEmpty ? `P${displayNum}` : getCharName(slotIndex)}
              </label>
              <label className="waiting-ready-label">
                Ready
                {isCurrentUser && !isBot && (status === 1 || status === 2) ? (
                  <input 
                    type="checkbox" 
                    className="waiting-ready" 
                    checked={getPlayerReady(slotIndex)}
                    onChange={(e) => handleReadyChange(slotIndex, e)}
                  />
                ) : !isEmpty ? (
                  <span>{isBot || getPlayerReady(slotIndex) ? '✓' : ''}</span>
                ) : null}
              </label>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default Slots;
