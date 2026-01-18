import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useGame } from '../hooks/useGame';
import Auth from './auth';
import Slots from './room_components/Slots';
import Floor from './room_components/Floor';
import Chat from './room_components/Chat';
import MP3 from './room_components/MP3';
import UserList from './room_components/UserList';
import Loading from './room_components/Loading';
import '../../style/global.css';
import '../../style/room.css';
import '../../style/room_components.css';


function Room() {
  const { vomitData, chatMessages, characters, users, players, actions, offsetCountdown, combatStarted, phaseCountdown } = useGame();
  const { user } = useAuth();
  const [chatInput, setChatInput] = useState('');
  const [vomitText, setVomitText] = useState('Game data will appear here.');
  const chatInputRef = useRef(null);
  
  // Show/hide areas based on combat state
  const showLoading = combatStarted === null;
  const showSlots = combatStarted === false;
  const showFloor = combatStarted === true;

  useEffect(() => {
    const nextText = vomitData ? JSON.stringify(vomitData, null, 2) : 'Game data will appear here.';
    setVomitText(nextText);
  }, [vomitData]);

  return (
    <div className="room">
      <div className="left-menu">
        <Auth/>
      </div>
      <div className="left-panel">
        <textarea id="vomit-box" readOnly value={vomitText}/>
        <MP3/>
        <UserList users={users} />
        {showLoading && <Loading/>}
        {showSlots && <Slots players={players} addBotToSlot={actions.addBotToSlot} joinPlayerSlot={actions.joinPlayerSlot} leavePlayerSlot={actions.leavePlayerSlot} setReady={actions.setReady} currentUser={user}/>}
        {showFloor && <Floor characters={characters} />}
      </div>
      <div className="right-menu">&gt;|</div>
      <div className="right-panel">
        <Chat chatMessages={chatMessages} user={user} offsetCountdown={offsetCountdown} phaseCountdown={phaseCountdown} chatInputRef={chatInputRef} chatInput={chatInput} setChatInput={setChatInput} actions={actions} />
      </div>
    </div>
  );
}

export default Room;