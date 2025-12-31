import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGuestId, genGuestId, authenticateGuest } from '../util';

export function useLobby() {
  const [sessions, setSessions] = useState([]);
  const [lobbyWs, setLobbyWs] = useState(null);
  const navigate = useNavigate();
  const wsRef = useRef(null);

  const connectLobbyWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    let guest_id = getGuestId() || genGuestId();

    ws.onopen = () => {
      console.log('Lobby WebSocket connected');
      authenticateGuest(guest_id, ws);
      listGames(ws);
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "game_created") {
        const gameId = msg.game_id;
        navigate(`/room/${gameId}`);
        listGames(ws);
      } else if (msg.type === "list_games") {
        setSessions(msg.session_ids || []);
      } else if (msg.type === "guest_assigned") {
        localStorage.setItem('guest_number', msg.guest_number);
        console.log(`You joined as Guest ${msg.guest_number}`);
      }
    };

    ws.onerror = (error) => {
      console.error('Lobby WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Lobby WebSocket disconnected');
      setLobbyWs(null);
      wsRef.current = null;
    };

    setLobbyWs(ws);
  };

  const listGames = (ws = null) => {
    const socket = ws || wsRef.current || lobbyWs;
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = {
        action: 'list_games'
      };
      socket.send(JSON.stringify(message));
    } else {
      console.error('Lobby WebSocket not connected');
      if (!wsRef.current) {
        connectLobbyWebSocket();
      }
    }
  };

  const createGame = () => {
    const socket = wsRef.current || lobbyWs;

    if (socket && socket.readyState === WebSocket.OPEN) {
      console.log('socket is connected');
      const message = {
        action: 'create_game'
      };
      socket.send(JSON.stringify(message));
    } else {
      console.error('Lobby WebSocket not connected');
      connectLobbyWebSocket();
    }
  };

  const killDB = () => {
    const socket = wsRef.current || lobbyWs;
    if (socket && socket.readyState === WebSocket.OPEN) {
      const message = {
        action: 'kill_db'
      };
      socket.send(JSON.stringify(message));
    } else {
      console.error('Lobby WebSocket not connected');
      connectLobbyWebSocket();
    }
  };

  const openGameRoom = (gameId) => {
    navigate(`/room/${gameId}`);
  };

  useEffect(() => {
    connectLobbyWebSocket();

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  return { sessions, createGame, killDB, openGameRoom };
}

