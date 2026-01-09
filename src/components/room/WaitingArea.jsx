import React from 'react';

function WaitingArea({ players, joinPlayerSlot, addBotToSlot, leavePlayerSlot, setReady, currentUser }) {
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

  const handleAddBotClick = (slotNum) => {
    addBotToSlot(slotNum);
  };

  const handleLeaveClick = (slotNum) => {
    leavePlayerSlot(slotNum);
  };

  const getSlotStatus = (slotNum) => {
    const slotIndex = slotNum - 1;
    const player = players[slotIndex];
    return player?.occupy || 0; // 0=empty, 1=occupied, 2=connection-lost
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
    if (!player || !player.info || !userInfo) return false;
    return player.info.id === userInfo.id;
  };

  const isBotInSlot = (slotNum) => {
    const slotIndex = slotNum - 1;
    const player = players[slotIndex];
    if (!player || !player.info) return false;
    return player.info.is_bot === true || (player.info.id && player.info.id.startsWith('bot_'));
  };

  const getCharName = (slotNum) => {
    const slotIndex = slotNum - 1;
    const player = players[slotIndex];
    if (!player) return '-';
    return player.character?.name || 'Guest';
  };

  const getPlayerReady = (slotNum) => {
    const slotIndex = slotNum - 1;
    const player = players[slotIndex];
    if (!player) return false;
    return player.ready === true;
  };

  const handleReadyChange = (slotNum, event) => {
    const checked = event.target.checked;
    setReady(slotNum, checked);
  };

  // Generate slot numbers dynamically based on players array length (4-8)
  const slotNumbers = Array.from({ length: players.length || 4 }, (_, i) => i + 1);

  return (
    <div className="waiting-area" style={{ display: 'flex' }}>
      <div className="waiting-grid">
        {slotNumbers.map((num) => {
          const status = getSlotStatus(num);
          const isEmpty = isSlotEmpty(num);
          const isConnectionLost = isSlotConnectionLost(num);
          const isCurrentUser = isCurrentUserInSlot(num);
          const isBot = isBotInSlot(num);
          
          const slotIndex = num - 1;
          const player = players[slotIndex];
          const tokenImage = status === 1 && player?.character?.token_image 
            ? player.character.token_image 
            : null;

          return (
            <div key={num} className="waiting-cell">
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
                      onClick={() => handleJoinClick(num)}
                    >
                      Join
                    </button>
                    <button
                    className="add-bot-but"
                    onClick={() => handleAddBotClick(num)}
                    >Bot</button>
                  </div>
                ) : (
                  (isCurrentUser || isBot) && status === 1 && (
                    <button 
                      className="player-leave-but"
                      onClick={() => handleLeaveClick(num)}
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
              <label className="waiting-name" id={`player-name-${num}`}>
                {isEmpty ? `P${num}` : getCharName(num)}
              </label>
              <label className="waiting-ready-label">
                Ready
                {isCurrentUser && !isBot && (status === 1 || status === 2) ? (
                  <input 
                    type="checkbox" 
                    className="waiting-ready" 
                    checked={getPlayerReady(num)}
                    onChange={(e) => handleReadyChange(num, e)}
                  />
                ) : !isEmpty ? (
                  // Show checkmark for bots (always ready) or other players if they're ready
                  <span>{isBot || getPlayerReady(num) ? '✓' : ''}</span>
                ) : null}
              </label>
            </div>
          );
        })}
      </div>
      <label className="start-label">Starting in 3...</label>
    </div>
  );
}

export default WaitingArea;

