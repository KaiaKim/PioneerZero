import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { quickAuth, getWebSocketUrl, genChatMessage } from '../util';


export function useGame() {
  const { gameId } = useParams();
  let userInfo = JSON.parse(localStorage.getItem('user_info'));
  if (!userInfo) {
    userInfo = {
      name: 'temp',
      id: 'temp_id',
    };
  }
  const [vomitData, setVomitData] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [users, setUsers] = useState([]);
  const [players, setPlayers] = useState([]); // Array of player objects: {info, character, slot, team, occupy, pos}
  const [userName, setUserName] = useState(userInfo.name);
  const [offsetCountdown, setOffsetCountdown] = useState(null); // Offset countdown seconds (3, 2, 1, or null)
  const [combatStarted, setCombatStarted] = useState(null); // Flag to track if combat has started
  const [phaseCountdown, setPhaseCountdown] = useState(null); // Phase timer seconds or null
  const chatLogRef = useRef(null);
  const wsRef = useRef(null);
  const autoJoinAttemptedRef = useRef(false);
  const plListReceivedRef = useRef(false);
  const phaseCountdownRef = useRef(null);

  const connectGameWS = () => {
    const wsUrl = getWebSocketUrl();
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Game WebSocket connected');
      quickAuth(ws);
      joinGame();
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      let storedSlotKey = `player_slot_${gameId}`;
      let storedSlotNum = localStorage.getItem(storedSlotKey);
      let slotNum = storedSlotNum ? parseInt(storedSlotNum) : null;

      if (msg.type === "auth_success") {
        handleAuthSuccess(msg, slotNum);
      } else if (msg.type === "joined_game") {
        loadGame();
      } else if (msg.type === "join_failed") {
        console.error('Failed to join game:', msg.message);
      } else if (msg.type === "vomit_data") {
        setVomitData(JSON.stringify(msg, null, 2));
        setCharacters(msg.characters || []);
      } else if (msg.type === "users_list") {
        setUsers(msg.users || []);
      } else if (msg.type === "players_list") {
        handlePlayersList(msg.players);
      } else if (msg.type === "join_slot_failed") {
        console.error('Failed to join slot:', msg.message);
        alert('Failed to join slot: ' + msg.message);
        localStorage.removeItem(storedSlotKey); // Clear stored slot number if join failed
      } else if (msg.type === "leave_slot_failed") {
        console.error('Failed to leave slot:', msg.message);
        alert('Failed to leave slot: ' + msg.message);
      } else if (msg.type === "set_ready_failed") {
        console.error('Failed to set ready state:', msg.message);
        alert('Failed to set ready state: ' + msg.message);
      } else if (msg.type === "chat_history") {
        const messages = (msg.messages || []).map(genChatMessage);
        setChatMessages(messages);
      } else if (msg.type === "chat") {
        const newMessage = genChatMessage(msg);
        setChatMessages(prev => [...prev, newMessage]);
        
      } else if (msg.type === "combat_state") {
        console.log('Combat state received:', msg.combat_state);
        setCombatStarted(msg.combat_state?.in_combat || false);
      } else if (msg.type === "offset_timer") {
        if (msg.seconds > 0) {
          setOffsetCountdown(msg.seconds);
        } else {
          setOffsetCountdown(null);
        }
      } else if (msg.type === "combat_started") {
        console.log('Combat started!');
        setCombatStarted(true);
        setOffsetCountdown(null);
      } else if (msg.type === "phase_timer") {
        if (msg.seconds > 0) {
          phaseCountdownRef.current = msg.seconds;
          setPhaseCountdown(msg.seconds);
        } else {
          phaseCountdownRef.current = null;
          setPhaseCountdown(null);
        }
      } else if (msg.type === "no_game") {
        console.log('No active game found');
      }
    };

    ws.onerror = (error) => {
      console.error('Game WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Game WebSocket disconnected');
      wsRef.current = null;
    };
  };

  // Decorator function to handle common WebSocket message sending pattern
  const messageGameWS = (message) => {
    message.game_id = gameId; // Add game_id to the message
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  };

  const joinGame = () => {
    messageGameWS({
      action: 'join_room'
    });
  };

  const handleAuthSuccess = (msg, slotNum) => {
    setUserName(msg.user_info.name);
    localStorage.setItem('user_info', JSON.stringify(msg.user_info));
    // If players_list was already received, try auto-join now that we have user info
    if (plListReceivedRef.current && !autoJoinAttemptedRef.current && slotNum) {
      autoJoinAttemptedRef.current = true;
      setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          console.log(`Auto-joining slot ${slotNum} after authentication`);
          joinPlayerSlot(slotNum);
        }
      }, 500);
    }
  };

  const loadGame = () => {
    messageGameWS({
      action: 'load_room'
    });
  };

  const joinPlayerSlot = (slotNum) => {
    messageGameWS({
      action: 'join_player_slot',
      slot: slotNum,
    });
  };
  
  const addBotToSlot = (slotNum) => {
    messageGameWS({
      action: 'add_bot_to_slot',
      slot: slotNum
    });
  };

  const leavePlayerSlot = (slotNum) => {
    messageGameWS({
      action: 'leave_player_slot',
      slot: slotNum
    });
    // Remove slot number from localStorage when leaving
    const storedSlotKey = `player_slot_${gameId}`;
    localStorage.removeItem(storedSlotKey);
  };

  const setReady = (slotNum, ready) => {
    messageGameWS({
      action: 'set_ready',
      slot: slotNum,
      ready: ready
    });
  };

  const sendChat = (content) => {
    if (!content.trim()) return;
    messageGameWS({
      action: 'chat',
      sender: userName,
      content: content.trim()
    });
    return true; // TODO: if fail, return false > don't clear the input
  };

  // Handle players_list message
  const handlePlayersList = (playersList) => {
    setPlayers(playersList || []);
    plListReceivedRef.current = true;
    
    // Get current user info
    const currentUserId = userInfo.id;
    const players = playersList || [];
    
    // Compute stored slot key and number
    const storedSlotKey = `player_slot_${gameId}`;
    const storedSlotNum = localStorage.getItem(storedSlotKey);
    const slotNum = storedSlotNum ? parseInt(storedSlotNum) : null;
    
    // Update localStorage if user is in a slot (to keep it in sync)
    let userSlotNum = null;
    for (let i = 0; i < players.length; i++) {
      const player = players[i];
      if (player.info && player.info.id === currentUserId) {
        userSlotNum = i + 1; // Slot numbers are 1-based
        break;
      }
    }
    
    if (userSlotNum) {
      // User is in a slot, update localStorage
      localStorage.setItem(storedSlotKey, userSlotNum.toString());
    } else {
      // User is not in any slot, but only clear if we haven't attempted auto-join yet
      if (autoJoinAttemptedRef.current) {
        localStorage.removeItem(storedSlotKey);
      }
    }
    
    // Check if user should auto-join their previous slot after page refresh
    // Only attempt once per connection
    // Need to rejoin if:
    // 1. Slot is empty (status 0) or occupied by someone else
    // 2. Slot is connection-lost (status 2) - even if it's the same user, we need to rejoin to change status to occupied
    if (!autoJoinAttemptedRef.current && slotNum) {
      const slotIndex = slotNum - 1;
      const playerInSlot = players[slotIndex];
      const slotStatus = playerInSlot?.occupy || 0;          
      const isUserInSlot = playerInSlot.info && playerInSlot.info.id === currentUserId;
      const needsRejoin = !isUserInSlot || slotStatus === 2;
      if (needsRejoin) {
        autoJoinAttemptedRef.current = true;
        // Wait a bit for WebSocket to be ready, then try to rejoin
        setTimeout(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log(`Auto-joining slot ${slotNum} after page refresh (status: ${slotStatus})`);
            joinPlayerSlot(slotNum);
          }
        }, 500);
      } else {
        // User is already in the slot with occupied status, mark as attempted to prevent further checks
        autoJoinAttemptedRef.current = true;
      }
    }
  };

  useEffect(() => {
    // Auto-scroll chat to bottom when new messages arrive
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [chatMessages]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (phaseCountdownRef.current == null) {
        return;
      }
      if (phaseCountdownRef.current <= 0) {
        return;
      }
      const nextValue = phaseCountdownRef.current - 1;
      phaseCountdownRef.current = nextValue;
      setPhaseCountdown(nextValue);
    }, 1000);

    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    // Reset auto-join flag and players list flag when gameId changes
    autoJoinAttemptedRef.current = false;
    plListReceivedRef.current = false;
    connectGameWS();

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [gameId]);
  
  // Group all action functions together
  const actions = {
    sendChat,
    joinPlayerSlot,
    addBotToSlot,
    leavePlayerSlot,
    setReady,
  };

  return {
    // State
    vomitData,
    chatMessages,
    characters,
    users,
    players,
    userName,
    offsetCountdown,
    phaseCountdown,
    combatStarted,
    chatLogRef,
    // Actions grouped together
    actions
  };
}

