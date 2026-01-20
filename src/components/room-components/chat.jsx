import React, { useCallback, useEffect, useRef } from 'react';
import { useGame } from '../../hooks/useGame';
import { setDialogueElements } from '../../util';

function ChatBox({ chatMessages, user, offsetCountdown, phaseCountdown, chatInputRef, chatInput, setChatInput, actions }) {
  const { chatLogRef } = useGame();

  // Handle chat input keydown
  const handleChatKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (actions.sendChat(chatInput)) {
        setChatInput('');
      }
    }
  }, [chatInput, actions, setChatInput]);

  return (
    <div className="chat-area">
      <div ref={chatLogRef} id="chat-log" className="chat-log-container">
          {chatMessages.map((msg, index) => {
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
          })}
        </div>
        <div>
          <label>
            <input type="checkbox" id="all-checkbox" /> All
          </label>
          <label>
            <input type="checkbox" id="system-checkbox" /> System
          </label>
          <label>
            <input type="checkbox" id="chat-checkbox" /> Chat
          </label>
          <label>
            <input type="checkbox" id="story-checkbox" /> Story
          </label>
        </div>
        <div>
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

export { ChatBox, ChatOverlay };

