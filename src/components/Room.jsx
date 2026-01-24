import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useGame } from '../hooks/useGame';
import Auth from './auth';
import Slots from './room-components/slots';
import Floor from './room-components/floor';
import {ChatBox, ChatOverlay} from './room-components/chat';
import MP3 from './room-components/mp3';
import UserList from './room-components/userList';
import Loading from './room-components/loading';
import ActionQueue from './room-components/que';
import '../../style/global.css';
import '../../style/room.css';
import '../../style/room_components.css';
import '../../style/chat.css';


function Room() {
  const { vomitData, chatMessages, characters, users, players, actions, offsetCountdown, combatStarted, phaseCountdown } = useGame();
  const { user } = useAuth();
  const [chatInput, setChatInput] = useState('');
  const chatInputRef = useRef(null);
  
  // Show/hide areas based on combat state
  const showLoading = combatStarted === null;
  const showSlots = combatStarted === false;
  const showFloor = combatStarted === true;

  return (
    <div className="room">
      <div className="left-menu">
        <Auth/>
      </div>
      <div className="left-panel">
        <textarea id="vomit-box" readOnly value={vomitData ?? ''}/>
        <MP3/>
        <UserList users={users} />
        {showLoading && <Loading/>}
        {showSlots && <Slots players={players} addBotToSlot={actions.addBotToSlot} joinPlayerSlot={actions.joinPlayerSlot} leavePlayerSlot={actions.leavePlayerSlot} setReady={actions.setReady} currentUser={user}/>}
        {showFloor && <Floor characters={characters} />}

        <ChatOverlay/>
      </div>
      <div className="right-menu">&gt;|</div>
      <div className="right-panel">
        <ChatBox chatMessages={chatMessages} user={user} offsetCountdown={offsetCountdown} phaseCountdown={phaseCountdown} chatInputRef={chatInputRef} chatInput={chatInput} setChatInput={setChatInput} actions={actions} />
      </div>
      <ActionQueue/>

    </div>
  );
}

export default Room;