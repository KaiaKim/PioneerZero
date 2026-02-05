import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useGame } from '../../hooks/useGame';
import { setDialogueElements } from '../../util';
import {
  DEFAULT_TAB_CONFIG,
  getChatTabSettings,
  setChatTabSettings,
  getChatType,
  setChatType,
  getChatUnreadByTabId,
  setChatUnreadByTabId,
} from '../../storage';

function loadTabSettingsFromStorage() {
  return getChatTabSettings();
}

function saveTabSettingsToStorage(rows) {
  setChatTabSettings(rows);
}

function messageBelongsToTab(msg, row) {
  const sort = msg.sort ?? 'dialogue';
  return (
    (row.system && sort === 'system') ||
    (row.dialogue && sort === 'dialogue') ||
    (row.command && (sort === 'secret' || sort === 'error')) ||
    (row.communication && sort === 'communication') ||
    (row.chitchat && sort === 'chitchat')
  );
}

function getMessagesForTabRow(row, chatMessages) {
  return chatMessages.filter((msg) => messageBelongsToTab(msg, row));
}

function ChatBox({ chatMessages, user, offsetCountdown, phaseCountdown, chatInputRef, chatInput, setChatInput, actions, tabConfig }) {
  const { gameId } = useParams();
  const { chatLogRef } = useGame();
  const tabs = tabConfig && tabConfig.length > 0 ? tabConfig : [...DEFAULT_TAB_CONFIG];
  const mainTabId = tabs[0]?.id;
  const [activeTab, setActiveTab] = useState(mainTabId);
  const [chatType, setChatTypeState] = useState(() => getChatType(gameId));
  const [unreadByTabId, setUnreadByTabId] = useState(() => getChatUnreadByTabId(gameId));
  const prevChatMessagesLengthRef = useRef(0);
  const prevGameIdForUnreadRef = useRef(gameId);

  useEffect(() => {
    const currentIds = new Set(tabs.map((t) => t.id));
    if (!currentIds.has(activeTab)) {
      setActiveTab(mainTabId);
    }
  }, [tabs, activeTab, mainTabId]);

  useEffect(() => {
    if (gameId == null) return;
    setChatTypeState(getChatType(gameId));
    setUnreadByTabId(getChatUnreadByTabId(gameId));
  }, [gameId]);

  useEffect(() => {
    if (prevGameIdForUnreadRef.current !== gameId) {
      prevGameIdForUnreadRef.current = gameId;
      return;
    }
    setChatUnreadByTabId(gameId, unreadByTabId);
  }, [unreadByTabId, gameId]);

  useEffect(() => {
    const prevLen = prevChatMessagesLengthRef.current;
    prevChatMessagesLengthRef.current = chatMessages.length;
    if (prevLen > 0 && chatMessages.length > prevLen) {
      const newMessages = chatMessages.slice(prevLen);
      setUnreadByTabId((prev) => {
        const next = { ...prev };
        newMessages.forEach((msg) => {
          tabs.forEach((tab) => {
            if (tab.id !== activeTab && messageBelongsToTab(msg, tab)) {
              next[tab.id] = true;
            }
          });
        });
        return next;
      });
    }
  }, [chatMessages, tabs, activeTab]);

  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
    setUnreadByTabId((prev) => ({ ...prev, [tabId]: false }));
  };

  // Handle chat input keydown
  const handleChatKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (actions.sendChat(chatInput, chatType)) {
        setChatInput('');
      }
    }
  }, [chatInput, chatType, actions, setChatInput]);

  const renderMessage = (msg, index) => {
    const isCurrentUser = user && msg.user_id && user.id === msg.user_id;
    return (
      <div key={index} className={`chat-message ${msg.sort === 'system' ? 'system' : ''} ${msg.sort === 'secret' ? 'secret' : ''} ${msg.sort === 'error' ? 'error' : ''} ${isCurrentUser ? 'own-message' : ''}`}>
        <div className="chat-message-header">
          <span className="chat-message-name">{msg.sender}</span>
          <span className="chat-message-time">{msg.time}</span>
        </div>
        <div className="chat-message-content">{msg.content}</div>
      </div>
    );
  };

  return (
    <div className="chat-area">
      <div ref={chatLogRef} id="chat-log" className="chat-log-container">
        {tabs.map((tab) => {
          const messages = getMessagesForTabRow(tab, chatMessages);
          return (
            <div
              key={tab.id}
              className={`chat-log-panel ${activeTab === tab.id ? 'active' : ''}`}
              style={{ display: activeTab === tab.id ? 'flex' : 'none' }}
            >
              {messages.map((msg, index) => renderMessage(msg, index))}
            </div>
          );
        })}
      </div>
      <div className="chat-tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`chat-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => handleTabClick(tab.id)}
            aria-label={unreadByTabId[tab.id] ? `${tab.tabName} (unread)` : tab.tabName}
          >
            <span>{tab.tabName}</span>
            {unreadByTabId[tab.id] && <span className="chat-tab-unread-dot" aria-hidden>*</span>}
          </button>
        ))}
      </div>
      <div className="chat-profile-row">
          <img
            src="/images/pikita_token.png"
            alt="character image"
            className="profile-image"
          />
          <label id="chat-char">{user ? user.name : 'noname'}</label>
          <select
            className="chat-type-select"
            value={chatType}
            onChange={(e) => {
              const value = e.target.value;
              setChatTypeState(value);
              setChatType(gameId, value);
            }}
            aria-label="Chat type"
          >
            <option value="dialogue">말하기</option>
            <option value="communication">통신</option>
            <option value="chitchat">사담</option>
          </select>
          <button onClick={() => actions.sendChat(chatInput, chatType)}>
            Send
          </button>
        </div>
        <textarea
          ref={chatInputRef}
          id="chat-input"
          placeholder="Type your message here..."
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={handleChatKeyDown}
        />
    </div>
  );
}

function ChatOverlay(){
  const rootRef = useRef(null);
  const standingLayerRef = useRef(null);
  const uiLayerRef = useRef(null);
  const dialogueBoxRef = useRef(null);
  const namePlateRef = useRef(null);
  const textAreaRef = useRef(null);
  const nextArrowRef = useRef(null);

  useEffect(() => {
    setDialogueElements({
      root: rootRef.current,
      standingLayer: standingLayerRef.current,
      uiLayer: uiLayerRef.current,
      dialogueBox: dialogueBoxRef.current,
      namePlate: namePlateRef.current,
      textArea: textAreaRef.current,
      nextArrow: nextArrowRef.current,
    });

    return () => {
      setDialogueElements({
        root: null,
        standingLayer: null,
        uiLayer: null,
        dialogueBox: null,
        namePlate: null,
        textArea: null,
        nextArrow: null,
      });
    };
  }, []);

  return (
    <div id="vn-container" ref={rootRef}>
        <div id="standing-layer" ref={standingLayerRef}></div>
        <div id="ui-layer" ref={uiLayerRef}>
            <div id="name-plate" ref={namePlateRef}></div>
            <div id="dialogue-box" ref={dialogueBoxRef}>
                <div id="text-area" ref={textAreaRef}></div>
                <div id="next-arrow" ref={nextArrowRef}></div>
            </div>
        </div>
    </div>
  )
}

const TAB_SETTINGS_HEADERS = ['', '탭이름', '시스템', '대화', '명령어', '통신', '도청', '사담'];
const TAB_SETTINGS_KEYS = ['system', 'dialogue', 'command', 'communication', 'spy', 'chitchat'];

function ChatSettings({ open, onClose, tabConfig, onApply }) {
  const [tabSettingsRows, setTabSettingsRows] = useState([...DEFAULT_TAB_CONFIG]);

  useEffect(() => {
    if (open && tabConfig && tabConfig.length > 0) {
      setTabSettingsRows(tabConfig.map((r) => ({ ...r })));
    } else if (open) {
      setTabSettingsRows([...DEFAULT_TAB_CONFIG]);
    }
  }, [open, tabConfig]);

  const removeRow = (id) => {
    setTabSettingsRows((prev) => prev.filter((r) => r.id !== id));
  };

  const addRow = () => {
    setTabSettingsRows((prev) => [
      ...prev,
      {
        id: Math.max(0, ...prev.map((r) => r.id)) + 1,
        tabName: '',
        system: false,
        dialogue: false,
        command: false,
        communication: false,
        spy: false,
        chitchat: false,
      },
    ]);
  };

  const setRowField = (id, field, value) => {
    setTabSettingsRows((prev) =>
      prev.map((r) => (r.id === id ? { ...r, [field]: value } : r))
    );
  };

  if (!open) return null;
  return (
    <div className="chat-settings-backdrop" onClick={onClose} role="presentation">
      <div className="chat-settings-modal" onClick={(e) => e.stopPropagation()}>
        <div className="chat-settings-tabs">
        <div className="chat-settings-header">
            <h3>채팅 탭</h3>
            <button type="button" className="chat-settings-default-btn" onClick={() => { setTabSettingsRows([...DEFAULT_TAB_CONFIG]); if (onApply) onApply([...DEFAULT_TAB_CONFIG]); }}>
              Default
            </button>
        </div>
          <table className="chat-settings-table">
            <thead>
              <tr>
                {TAB_SETTINGS_HEADERS.map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tabSettingsRows.map((row, index) => (
                <tr key={row.id}>
                  <td>
                    <button
                      type="button"
                      className="chat-settings-row-remove"
                      onClick={() => removeRow(row.id)}
                      disabled={index === 0}
                      aria-label="Remove row"
                    >
                      −
                    </button>
                  </td>
                  <td>
                    <input
                      type="text"
                      value={row.tabName}
                      onChange={(e) => setRowField(row.id, 'tabName', e.target.value)}
                      className="chat-settings-tab-name-input"
                    />
                  </td>
                  {TAB_SETTINGS_KEYS.map((key) => (
                    <td key={key}>
                      <input
                        type="checkbox"
                        checked={row[key]}
                        onChange={(e) => setRowField(row.id, key, e.target.checked)}
                        aria-label={key}
                      />
                    </td>
                  ))}
                </tr>
              ))}
              <tr>
                <td>
                  <button type="button" className="chat-settings-row-add" onClick={addRow} aria-label="Add row">+</button>
                </td>
                <td colSpan={7} />
              </tr>
            </tbody>
          </table>
        </div>

        <div className="chat-settings-footer">
          <button type="button" className="chat-settings-apply-btn" onClick={() => { if (onApply) onApply(tabSettingsRows); onClose(); }}>
            Apply
          </button>
        </div>

        <button type="button" className="chat-settings-close-btn" onClick={onClose}>X</button>
      </div>
    </div>
  );
}

export { ChatBox, ChatOverlay, ChatSettings, DEFAULT_TAB_CONFIG, loadTabSettingsFromStorage, saveTabSettingsToStorage };

