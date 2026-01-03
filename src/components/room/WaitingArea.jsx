import React from 'react';

function WaitingArea({ players, joinPlayerSlot, addBotToSlot, leavePlayerSlot, currentUser }) {
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
    console.log('DEBUG: WaitingArea isCurrentUserInSlot',player, userInfo);
    if (!player || !player.info || !userInfo) return false;
    return player.info.id === userInfo.id;
  };

  const getPlayerName = (slotNum) => {
    const slotIndex = slotNum - 1;
    const player = players[slotIndex];
    if (!player) return '-';
    return player.info.name || 'Guest';
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
                    <button
                    className="add-bot-but"
                    onClick={() => handleAddBotClick(num)}
                    >Bot</button>
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
                {isEmpty ? `P${num}` : getPlayerName(num)}
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

export default WaitingArea;

