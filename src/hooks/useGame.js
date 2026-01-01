import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { quickAuth } from '../util';

export function useGame() {
  const { gameId } = useParams();
  const [gameData, setGameData] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [users, setUsers] = useState([]);
  const [players, setPlayers] = useState([null, null, null, null]); // 4 slots
  const [userName, setUserName] = useState(() => {
    const userInfo = localStorage.getItem('user_info');
    if (userInfo) {
      try {
        const user = JSON.parse(userInfo);
        return user.name || user.email || 'Guest';
      } catch (e) {
        return 'Guest';
      }
    }
    return 'Guest';
  });
  const chatLogRef = useRef(null);
  const wsRef = useRef(null);

  const connectGameWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;


    ws.onopen = () => {
      console.log('Game WebSocket connected');

      quickAuth(ws);

      if (gameId) {
        joinGame(ws, gameId);
      }
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "auth_success" && msg.user_info) {
        const name = msg.user_info.name || msg.user_info.email || 'Guest';
        setUserName(name);
        localStorage.setItem('user_info', JSON.stringify(msg.user_info));
      } else if (msg.type === "joined_game") {
        loadGame(ws);
      } else if (msg.type === "join_failed") {
        console.error('Failed to join game:', msg.message);
      } else if (msg.type === "vomit_data") {
        console.log('Game data received');
        setGameData(msg);
        setCharacters(msg.characters || []);
      } else if (msg.type === "chat_history") {
        const userInfo = JSON.parse(localStorage.getItem('user_info') || 'null');
        const currentUserId = userInfo?.id || null;
        const messages = (msg.messages || []).map(chatMsg => ({
          sender: chatMsg.sort === "user" ? (chatMsg.sender || "noname") : "System",
          time: chatMsg.time,
          content: chatMsg.content,
          isSystem: chatMsg.sort === "system",
          user_id: chatMsg.user_id || null
        }));
        setChatMessages(messages);
      } else if (msg.type === "chat") {
        const newMessage = {
          sender: msg.sort === "user" ? (msg.sender || "noname") : "System",
          time: msg.sort === "system" ? new Date().toLocaleTimeString() : msg.time,
          content: msg.content,
          isSystem: msg.sort === "system",
          user_id: msg.user_id || null
        };
        setChatMessages(prev => [...prev, newMessage]);
      } else if (msg.type === "users_list") {
        console.log('Users list received:', msg.users);
        setUsers(msg.users || []);
      } else if (msg.type === "players_list") {
        console.log('Players list received:', msg.players);
        setPlayers(msg.players || [null, null, null, null]);
      } else if (msg.type === "join_slot_failed") {
        console.error('Failed to join slot:', msg.message);
        alert('Failed to join slot: ' + msg.message);
      } else if (msg.type === "leave_slot_failed") {
        console.error('Failed to leave slot:', msg.message);
        alert('Failed to leave slot: ' + msg.message);
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

  const joinGame = (ws = null, id = gameId) => {
    const socket = ws || wsRef.current;
    const game_id = id || gameId;
    if (socket && socket.readyState === WebSocket.OPEN && game_id) {
      const message = {
        action: 'join_game',
        game_id: game_id
      };
      socket.send(JSON.stringify(message));
    }
  };

  const loadGame = (ws = null) => {
    const socket = ws || wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN && gameId) {
      const message = {
        action: 'load_game',
        game_id: gameId
      };
      socket.send(JSON.stringify(message));
    }
  };

  const sendMessage = (content) => {
    if (!content.trim()) return;
    if (!gameId) {
      console.error('No game_id found. Cannot send message.');
      return;
    }
    const message = {
      action: 'chat',
      sender: userName,
      content: content.trim(),
      game_id: gameId
    };

    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      return true;
    } else {
      console.error('Game WebSocket not connected. Message not sent.');
      return false;
    }
  };

  const joinPlayerSlot = (slotNum) => {
    if (!gameId) {
      console.error('No game_id found. Cannot join slot.');
      return;
    }
    const message = {
      action: 'join_player_slot',
      slot_num: slotNum,
      game_id: gameId
    };

    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      return true;
    } else {
      console.error('Game WebSocket not connected. Cannot join slot.');
      return false;
    }
  };

  const leavePlayerSlot = (slotNum) => {
    if (!gameId) {
      console.error('No game_id found. Cannot leave slot.');
      return;
    }
    const message = {
      action: 'leave_player_slot',
      slot_num: slotNum,
      game_id: gameId
    };

    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      return true;
    } else {
      console.error('Game WebSocket not connected. Cannot leave slot.');
      return false;
    }
  };

  // Auto-scroll chat to bottom when new messages arrive
  useEffect(() => {
    if (chatLogRef.current) {
      chatLogRef.current.scrollTop = chatLogRef.current.scrollHeight;
    }
  }, [chatMessages]);

  useEffect(() => {
    connectGameWebSocket();

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [gameId]);

  return {
    gameData,
    chatMessages,
    characters,
    users,
    players,
    userName,
    sendMessage,
    joinPlayerSlot,
    leavePlayerSlot,
    chatLogRef
  };
}

