import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { getGuestId, genGuestId, authenticateGuest } from '../util';

export function useGame() {
  const { gameId } = useParams();
  const [gameWs, setGameWs] = useState(null);
  const [gameData, setGameData] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [characters, setCharacters] = useState([]);
  const [guestNumber, setGuestNumber] = useState(localStorage.getItem('guest_number') || 'noname');
  const chatLogRef = useRef(null);
  const wsRef = useRef(null);

  const connectGameWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    let guest_id = getGuestId() || genGuestId();

    ws.onopen = () => {
      console.log('Game WebSocket connected');
      authenticateGuest(guest_id, ws);

      if (gameId) {
        joinGame(ws, gameId);
      }
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "guest_assigned") {
        localStorage.setItem('guest_number', msg.guest_number);
        setGuestNumber(msg.guest_number);
        console.log(`You joined as Guest ${msg.guest_number}`);
      } else if (msg.type === "joined_game") {
        loadGame(ws);
      } else if (msg.type === "join_failed") {
        console.error('Failed to join game:', msg.message);
      } else if (msg.type === "vomit_data") {
        console.log('Game data received');
        setGameData(msg);
        setCharacters(msg.characters || []);
      } else if (msg.type === "chat_history") {
        const messages = (msg.messages || []).map(chatMsg => ({
          sender: chatMsg.sort === "user" ? (chatMsg.sender || "noname") : "System",
          time: chatMsg.time,
          content: chatMsg.content,
          isSystem: chatMsg.sort === "system"
        }));
        setChatMessages(messages);
      } else if (msg.type === "chat") {
        const newMessage = {
          sender: msg.sort === "user" ? (msg.sender || "noname") : "System",
          time: msg.sort === "system" ? new Date().toLocaleTimeString() : msg.time,
          content: msg.content,
          isSystem: msg.sort === "system"
        };
        setChatMessages(prev => [...prev, newMessage]);
      } else if (msg.type === "no_game") {
        console.log('No active game found');
      }
    };

    ws.onerror = (error) => {
      console.error('Game WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Game WebSocket disconnected');
      setGameWs(null);
      wsRef.current = null;
    };

    setGameWs(ws);
  };

  const joinGame = (ws = null, id = gameId) => {
    const socket = ws || wsRef.current || gameWs;
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
    const socket = ws || wsRef.current || gameWs;
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
      sender: `Guest ${guestNumber}`,
      content: content.trim(),
      game_id: gameId
    };

    const socket = wsRef.current || gameWs;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(message));
      return true;
    } else {
      console.error('Game WebSocket not connected. Message not sent.');
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
    guestNumber,
    sendMessage,
    chatLogRef
  };
}

