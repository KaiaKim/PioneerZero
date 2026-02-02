import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useGame } from '../../hooks/useGame';
import { setDialogueElements } from '../../util';

const CHAT_TAB_SETTINGS_KEY = 'chatTabSettings';

const DEFAULT_TAB_CONFIG = [
  { id: 1, tabName: '메인', system: true, rp: true, command: true, ourTeam: false, theirTeam: false, chitchat: false },
  { id: 2, tabName: '팀', system: false, rp: false, command: false, ourTeam: true, theirTeam: true, chitchat: false },
  { id: 3, tabName: '잡담', system: false, rp: false, command: false, ourTeam: false, theirTeam: false, chitchat: true },
];

function loadTabSettingsFromStorage() {
  try {
    const raw = localStorage.getItem(CHAT_TAB_SETTINGS_KEY);
    if (raw == null) return [...DEFAULT_TAB_CONFIG];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length === 0) return [...DEFAULT_TAB_CONFIG];
    const hasMain = parsed.some((r) => r.tabName === '메인');
    if (!hasMain) return [...DEFAULT_TAB_CONFIG];
    return parsed;
  } catch {
    return [...DEFAULT_TAB_CONFIG];
  }
}

function saveTabSettingsToStorage(rows) {
  try {
    const hasMain = rows.some((r) => r.tabName === '메인');
    const toSave = hasMain ? rows : [...DEFAULT_TAB_CONFIG];
    localStorage.setItem(CHAT_TAB_SETTINGS_KEY, JSON.stringify(toSave));
  } catch {
    // ignore
  }
}

function getMessagesForTabRow(row, chatMessages) {
  return chatMessages.filter(
    (msg) =>
      (row.system && msg.isSystem) ||
      (row.rp && !msg.isSystem) ||
      (row.command && (msg.isSecret || msg.isError))
  );
}

function ChatBox({ chatMessages, user, offsetCountdown, phaseCountdown, chatInputRef, chatInput, setChatInput, actions, tabConfig }) {
  const { chatLogRef } = useGame();
  const tabs = tabConfig && tabConfig.length > 0 ? tabConfig : [...DEFAULT_TAB_CONFIG];
  const mainTabId = tabs[0]?.id;
  const [activeTab, setActiveTab] = useState(mainTabId);

  useEffect(() => {
    const currentIds = new Set(tabs.map((t) => t.id));
    if (!currentIds.has(activeTab)) {
      setActiveTab(mainTabId);
    }
  }, [tabs, activeTab, mainTabId]);

  // Handle chat input keydown
  const handleChatKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (actions.sendChat(chatInput)) {
        setChatInput('');
      }
    }
  }, [chatInput, actions, setChatInput]);

  const renderMessage = (msg, index) => {
    const isCurrentUser = user && msg.user_id && user.id === msg.user_id;
    return (
      <div key={index} className={`chat-message ${msg.isSystem ? 'system' : ''} ${msg.isSecret ? 'secret' : ''} ${msg.isError ? 'error' : ''} ${isCurrentUser ? 'own-message' : ''}`}>
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
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.tabName}
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
          <div className="timer">
            <div id="offset-countdown">{offsetCountdown ?? ''}</div>
            <div id="phase-countdown">{phaseCountdown ?? ''}</div>
          </div>
          <button onClick={() => actions.sendChat(chatInput)}>
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

const TAB_SETTINGS_HEADERS = ['()', '탭이름', '시스템', 'RP', '커맨드', '우리 팀', '상대 팀', '잡담'];
const TAB_SETTINGS_KEYS = ['system', 'rp', 'command', 'ourTeam', 'theirTeam', 'chitchat'];

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
        rp: false,
        command: false,
        ourTeam: false,
        theirTeam: false,
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
          <h3>채팅 탭</h3>
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

