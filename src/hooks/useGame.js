import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { quickAuth, getWebSocketUrl, genChatMessage, renderDialogue } from '../util';
import { getUserInfo, setUserInfo, getPlayerSlot, setPlayerSlot, removePlayerSlot } from '../storage';

export function useGame() {
  const { gameId } = useParams();
  let userInfo = getUserInfo();
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
  const [actionSubmissionStatus, setActionSubmissionStatus] = useState([]);
  const [declaredAttack, setDeclaredAttack] = useState(null); // Current user's declared attack info
  const [offsetCountdown, setOffsetCountdown] = useState(null); // Offset countdown seconds (3, 2, 1, or null)
  const [combatStarted, setCombatStarted] = useState(null); // Flag to track if combat has started
  const [phaseCountdown, setPhaseCountdown] = useState(null); // Phase timer seconds or null
  const chatLogRef = useRef(null);
  const wsRef = useRef(null);
  const autoJoinAttemptedRef = useRef(false);
  const plListReceivedRef = useRef(false);
  const phaseCountdownRef = useRef(null);
  const playersRef = useRef([]);
  const chatQue = useRef([]);
  const isOverlayBusy = useRef(false);

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
      const storedSlotIndex = getPlayerSlot(gameId);
      const slotIndex = storedSlotIndex != null && storedSlotIndex !== '' ? parseInt(storedSlotIndex, 10) : null;

      if (msg.type === "auth_success") {
        handleAuthSuccess(msg, slotIndex);
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
        removePlayerSlot(gameId);
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
        if (msg.sort === "user" || msg.sort === "system") {
          enqueueChatOverlay({
            sender: newMessage.sender,
            content: newMessage.content
          });
        }
      } else if (msg.type === "combat_state") {
        console.log('Combat state received:', msg.combat_state);
        setCombatStarted(msg.combat_state?.in_combat || false);
        setActionSubmissionStatus(msg.combat_state?.submitted || []);
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
      } else if (msg.type === "action_submission_update") {
        setActionSubmissionStatus(msg.submitted || []);
      } else if (msg.type === "declared_attack") {
        // Check if this declared attack is for the current user
        const currentUserId = userInfo.id;
        const attackInfo = msg.attack_info;
        if (attackInfo && typeof attackInfo.slot_idx === 'number') {
          // Find if this slot belongs to the current user
          const currentPlayers = playersRef.current || [];
          const playerInSlot = currentPlayers.find(p => (p?.index ?? p?.slot) === attackInfo.slot_idx);
          if (playerInSlot?.info?.id === currentUserId) {
            setDeclaredAttack(attackInfo);
          }
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

  const handleAuthSuccess = (msg, slotIndex) => {
    setUserName(msg.user_info.name);
    setUserInfo(msg.user_info);
    // If players_list was already received, try auto-join now that we have user info
    if (plListReceivedRef.current && !autoJoinAttemptedRef.current && slotIndex != null) {
      autoJoinAttemptedRef.current = true;
      setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          console.log(`Auto-joining slot index ${slotIndex} after authentication`);
          joinPlayerSlot(slotIndex);
        }
      }, 500);
    }
  };

  const enqueueChatOverlay = (chatMessage) => {
    chatQue.current.push(chatMessage);
    processChatQueue();
  };

  const processChatQueue = () => {
    if (isOverlayBusy.current) {
      return;
    }
    const nextMessage = chatQue.current.shift();
    if (!nextMessage) {
      return;
    }
    isOverlayBusy.current = true;
    renderDialogue(nextMessage.sender, nextMessage.content, false, true, () => {
      isOverlayBusy.current = false;
      processChatQueue();
    });
  };

  const loadGame = () => {
    messageGameWS({
      action: 'load_room'
    });
  };

  const joinPlayerSlot = (slotIndex) => {
    messageGameWS({
      action: 'join_player_slot',
      slotIndex: slotIndex,
    });
  };
  
  const addBotToSlot = (slotIndex) => {
    messageGameWS({
      action: 'add_bot_to_slot',
      slotIndex: slotIndex
    });
  };

  const leavePlayerSlot = (slotIndex) => {
    messageGameWS({
      action: 'leave_player_slot',
      slotIndex: slotIndex
    });
    removePlayerSlot(gameId);
  };

  const setReady = (slotIndex, ready) => {
    messageGameWS({
      action: 'set_ready',
      slotIndex: slotIndex,
      ready: ready
    });
  };

  const sendChat = (content, chatType) => {
    if (!content.trim()) return;
    messageGameWS({
      action: 'chat',
      sender: userName,
      content: content.trim(),
      chat_type: chatType
    });
    return true; // TODO: if fail, return false > don't clear the input
  };

  // Handle players_list message
  const handlePlayersList = (playersList) => {
    const playersArray = playersList || [];
    setPlayers(playersArray);
    playersRef.current = playersArray;
    plListReceivedRef.current = true;
    
    // Get current user info
    const currentUserId = userInfo.id;
    const players = playersList || [];
    
    const storedSlotIndex = getPlayerSlot(gameId);
    const slotIndex = storedSlotIndex != null && storedSlotIndex !== '' ? parseInt(storedSlotIndex, 10) : null;

    let userSlotIndex = null;
    for (let i = 0; i < players.length; i++) {
      const player = players[i];
      if (player.info && player.info.id === currentUserId) {
        userSlotIndex = i;
        break;
      }
    }

    if (userSlotIndex != null) {
      setPlayerSlot(gameId, String(userSlotIndex));
    } else {
      if (autoJoinAttemptedRef.current) {
        removePlayerSlot(gameId);
      }
    }
    
    // Check if user should auto-join their previous slot after page refresh
    // Only attempt once per connection
    // Need to rejoin if:
    // 1. Slot is empty (status 0) or occupied by someone else
    // 2. Slot is connection-lost (status 2) - even if it's the same user, we need to rejoin to change status to occupied
    if (!autoJoinAttemptedRef.current && slotIndex != null) {
      const playerInSlot = players[slotIndex];
      const slotStatus = playerInSlot?.occupy || 0;          
      const isUserInSlot = playerInSlot?.info && playerInSlot.info.id === currentUserId;
      const needsRejoin = !isUserInSlot || slotStatus === 2;
      if (needsRejoin) {
        autoJoinAttemptedRef.current = true;
        // Wait a bit for WebSocket to be ready, then try to rejoin
        setTimeout(() => {
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            console.log(`Auto-joining slot index ${slotIndex} after page refresh (status: ${slotStatus})`);
            joinPlayerSlot(slotIndex);
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
    actionSubmissionStatus,
    declaredAttack,
    chatLogRef,
    // Actions grouped together
    actions
  };
}

