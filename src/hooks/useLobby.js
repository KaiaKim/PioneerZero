import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { quickAuth, getWebSocketUrl } from '../util';

export function useLobby() {
  const [sessions, setSessions] = useState([]);
  const navigate = useNavigate();
  const wsRef = useRef(null);

  const connectLobbyWS = () => {
    const wsUrl = getWebSocketUrl();
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Lobby WebSocket connected');
      quickAuth(ws);
      listGames();
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "game_created") {
        const gameId = msg.game_id;
        navigate(`/room/${gameId}`);
        listGames();
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

  // Decorator function to handle common WebSocket message sending pattern
  const messageLobbyWS = (message) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  };

  const listGames = () => {
    messageLobbyWS({
      action: 'list_games'
    });
  };

  const createGame = (playerNum = 4) => {
    messageLobbyWS({
      action: 'create_game',
      player_num: playerNum
    });
  };

  const killDB = () => {
    messageLobbyWS({
      action: 'kill_db'
    });
  };

  const openGameRoom = (gameId) => {
    navigate(`/room/${gameId}`);
  };

  useEffect(() => {
    connectLobbyWS();

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  return { sessions, createGame, killDB, openGameRoom };
}

