import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getGuestId, genGuestId, authenticateGuest } from '../util';

export function useLobby() {
  const [sessions, setSessions] = useState([]);
  const navigate = useNavigate();
  const wsRef = useRef(null);

  const connectLobbyWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;


    ws.onopen = () => {
      console.log('Lobby WebSocket connected');
      const guest_id = getGuestId();
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
      }
    };

    ws.onerror = (error) => {
      console.error('Lobby WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('Lobby WebSocket disconnected');
      wsRef.current = null;
    };
  };

  const listGames = (ws = null) => {
    const socket = ws || wsRef.current;
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
    const socket = wsRef.current;

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
    const socket = wsRef.current;
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

