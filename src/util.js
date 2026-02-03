// Configuration
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

export function getWebSocketUrl() {
    return `${WS_BASE_URL}/ws`;
}

export function getApiBaseUrl() {
    return API_BASE_URL;
}

// Helper functions for game_id from URL parameter
export function getGameId() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('game_id');
}

export function genGuestId() {
    const guestId = crypto.randomUUID();
    localStorage.setItem('guest_id', guestId);
    return guestId;
}

export function quickAuth(ws) {
    const user_info = localStorage.getItem('user_info');
    if (user_info) {
        const message = {
            action: 'authenticate_user',
            user_info: user_info
        };
        ws.send(JSON.stringify(message));
        return;
    }

    // If no user_info, try guest_id
    const guest_id = localStorage.getItem('guest_id');
    if (guest_id) {
        const message = {
            action: 'authenticate_user',
            guest_id: guest_id
        };
        ws.send(JSON.stringify(message));
        return;
    }
}

function formatTime(timeString) {
    if (!timeString) return '';
    try {
        const date = new Date(timeString);
        const ampm = date.getHours() >= 12 ? '오후' : '오전';
        const hours = String(date.getHours() % 12 || 12).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        //const seconds = String(date.getSeconds()).padStart(2, '0');
        return `${ampm} ${hours}:${minutes}`;
    } catch (e) {
        return timeString.substring(11, 19); // Fallback: extract HH:MM:SS from ISO string
    }
}

export function genChatMessage(chatMsg) {
    const sort = chatMsg.sort || "dialogue";
    let sender = chatMsg.sender;
    if (sort === "secret") sender += " 👁";
    if (sort === "error") sender += " ❌";
    return {
        sender,
        time: formatTime(chatMsg.time),
        content: chatMsg.content,
        sort,
        user_id: chatMsg.user_id || null
    };
}


// ========== 대화 렌더링 (페이지 지원) ==========
// ========== 전역 변수 (최소화) ==========
let vdSettings = { charAssets: {}, charSettings: {}, isOverlayHidden: false };
let typeInterval = null;
let autoTurnTimeout = null;
let currentEmotions = {};
let lastSpeaker = null;
let messageCounter = 0;
let positionCheckInterval = null;
let lastAdjustTime = 0;
const ADJUST_THROTTLE = 500;
let currentRenderId = 0;
let initialLastMessageId = null;

// [Logic] 엔진 초기화 상태
let isEngineReady = false;
let stabilizationTimer = null;
let failSafeTimer = null;

// [Debounce] 채팅 동기화
let emotionSyncTimeout = null;

// 페이지 넘김
let dialoguePages = [];
let currentPageIndex = 0;
let isTyping = false;
let currentFullText = "";
let lastRenderedData = null;
let resizeTimeout = null;
let dialogueElements = {
    root: null,
    standingLayer: null,
    uiLayer: null,
    dialogueBox: null,
    namePlate: null,
    textArea: null,
    nextArrow: null,
};



let dialogueCompleteCallback = null;
let dialogueCompleteRenderId = 0;

export function setDialogueElements(elements) {
    dialogueElements = {
        ...dialogueElements,
        ...elements,
    };
}

function getDialogueElements() {
    return dialogueElements;
}

// ========== 텍스트 페이지 나누기 로직 ==========
function paginateText(text, container) {
  if (!text) return [];

  const { root, dialogueBox } = getDialogueElements();
  if (!root || !dialogueBox) return [text];

  const pages = [];
  const tempDiv = document.createElement("div");

  const computedStyle = window.getComputedStyle(container);
  tempDiv.style.width = computedStyle.width;
  tempDiv.style.fontFamily = computedStyle.fontFamily;
  tempDiv.style.fontSize = computedStyle.fontSize;
  tempDiv.style.fontWeight = computedStyle.fontWeight;
  tempDiv.style.lineHeight = computedStyle.lineHeight;
  tempDiv.style.letterSpacing = computedStyle.letterSpacing;
  tempDiv.style.whiteSpace = "pre-wrap";
  tempDiv.style.wordBreak = "break-all";
  tempDiv.style.position = "absolute";
  tempDiv.style.visibility = "hidden";
  tempDiv.style.left = "-9999px";

  root.appendChild(tempDiv);

  const boxStyle = window.getComputedStyle(dialogueBox);
  let maxH = parseFloat(boxStyle.maxHeight) || parseFloat(boxStyle.height);
  const paddingY =
    parseFloat(boxStyle.paddingTop) + parseFloat(boxStyle.paddingBottom);
  const borderY =
    parseFloat(boxStyle.borderTopWidth) +
    parseFloat(boxStyle.borderBottomWidth);
  const availableHeight = maxH - paddingY - borderY - 2;

  let remainingText = text;

  while (remainingText.length > 0) {
    let low = 0;
    let high = remainingText.length;
    let bestFit = 0;

    while (low <= high) {
      const mid = Math.floor((low + high) / 2);
      tempDiv.innerText = remainingText.substring(0, mid);

      if (tempDiv.clientHeight <= availableHeight) {
        bestFit = mid;
        low = mid + 1;
      } else {
        high = mid - 1;
      }
    }

    if (bestFit === 0) bestFit = 1;

    pages.push(remainingText.substring(0, bestFit));
    remainingText = remainingText.substring(bestFit);
  }

  tempDiv.remove();
  return pages;
}

export function renderDialogue(speakerName, messageText, isDesc, isUnregistered, onComplete = null) {
    currentRenderId++;
    const thisRenderId = currentRenderId;
    dialogueCompleteCallback = onComplete;
    dialogueCompleteRenderId = thisRenderId;
    const {
      root,
      standingLayer,
      uiLayer,
      namePlate,
      textArea,
      nextArrow,
    } = getDialogueElements();

    if (vdSettings.isOverlayHidden) {
      lastRenderedData = { speakerName, messageText, isDesc, isUnregistered };
      if (onComplete) {
        const delay = parseInt(vdSettings.autoTurnDelay) || 2500;
        setTimeout(() => {
          if (dialogueCompleteRenderId === thisRenderId) {
            onComplete();
          }
        }, delay);
      }
      return;
    }

    if (!root || !standingLayer || !uiLayer || !namePlate || !textArea || !nextArrow) {
      lastRenderedData = { speakerName, messageText, isDesc, isUnregistered };
      if (onComplete) {
        const delay = parseInt(vdSettings.autoTurnDelay) || 2500;
        setTimeout(() => {
          if (dialogueCompleteRenderId === thisRenderId) {
            onComplete();
          }
        }, delay);
      }
      return;
    }
  
    clearInterval(typeInterval);
    clearTimeout(autoTurnTimeout);
    isTyping = false;
  
    lastRenderedData = { speakerName, messageText, isDesc, isUnregistered };
  
    root.style.display = "block";
    root.style.visibility = "visible";
    root.style.opacity = "0";
  
    let cleanText = messageText;
    cleanText = cleanText.replace(/^\d{1,2}:\d{2}\s?[AP]M[^:]+:\s*/gi, "");
    cleanText = cleanText.replace(/^\d{1,2}:\d{2}:\d{2}\s?[AP]M[^:]+:\s*/gi, "");
    cleanText = cleanText.replace(/^\d{1,2}:\d{2}\s?[^:]+:\s*/g, "");
  
    if (!uiLayer.hasAttribute("data-click-listener")) {
      uiLayer.addEventListener("click", handleDialogueClick);
      uiLayer.setAttribute("data-click-listener", "true");
    }
  
    // 이름표 처리
    if (isDesc) {
      namePlate.classList.add("hidden");
      namePlate.innerText = "";
      standingLayer.innerHTML = "";
    } else {
      namePlate.classList.remove("hidden");
      namePlate.innerText = speakerName;
  
      if (!isUnregistered) {
        const charData = vdSettings.charAssets[speakerName];
        if (charData) {
          const currentEmo =
            currentEmotions[speakerName] || Object.keys(charData)[0];
          const rawSrc = charData[currentEmo];
  
          resolveImage(rawSrc).then((imgSrc) => {
            if (thisRenderId !== currentRenderId) return;
  
            if (imgSrc) {
              standingLayer.innerHTML = `<img src="${imgSrc}" alt="${speakerName}">`;
  
              let globalScale = (vdSettings.standingScale || 100) / 100;
              let indScale = 1.0;
              if (
                vdSettings.charSettings &&
                vdSettings.charSettings[speakerName]
              ) {
                indScale =
                  (vdSettings.charSettings[speakerName].scale || 100) / 100;
              }
              const finalScale = globalScale * indScale;
              standingLayer.style.transform = `scale(${finalScale})`;
              standingLayer.style.transformOrigin = "bottom center";
            } else {
              standingLayer.innerHTML = "";
            }
          }).catch(error => {
            console.error("[VD Render] 이미지 로드 오류:", error);
            standingLayer.innerHTML = "";
          });
        } else {
          if (thisRenderId === currentRenderId) standingLayer.innerHTML = "";
        }
      } else {
        if (thisRenderId === currentRenderId) standingLayer.innerHTML = "";
      }
    }
  
    textArea.innerText = "";
    nextArrow.style.display = "none";
  
    const fontSize = vdSettings.fontSize || 18;
    textArea.style.fontSize = fontSize + "px";
  
    requestAnimationFrame(() => {
      try {
        dialoguePages = paginateText(cleanText, textArea);
        currentPageIndex = 0;
        if (dialoguePages.length > 0) typePage(0);
        root.style.opacity = "1";
        //adjustVNPosition(); // Position adjustment disabled for now
      } catch (error) {
        console.error("[VD Render] 페이지 나누기 오류:", error);
        textArea.innerText = cleanText;
        root.style.opacity = "1";
      }
    });
  }
  
  function typePage(pageIndex) {
    if (pageIndex >= dialoguePages.length) return;
  
    const { textArea, nextArrow } = getDialogueElements();
    if (!textArea || !nextArrow) return;
    const textToType = dialoguePages[pageIndex];
    currentFullText = textToType;
  
    textArea.innerText = "";
    nextArrow.style.display = "none";
    isTyping = true;
  
    const speed = parseInt(vdSettings.typeSpeed) || 50;
    let currentIndex = 0;
  
    clearInterval(typeInterval);
  
    typeInterval = setInterval(() => {
      try {
        if (currentIndex < textToType.length) {
          textArea.innerText += textToType[currentIndex];
          currentIndex++;
        } else {
          finishTyping();
        }
      } catch (error) {
        console.error("[VD Render] 타이핑 오류:", error);
        clearInterval(typeInterval);
        finishTyping();
      }
    }, speed);
  }
  
  function finishTyping() {
    clearInterval(typeInterval);
    clearTimeout(autoTurnTimeout);
    
    isTyping = false;
  
    const { textArea, nextArrow } = getDialogueElements();
    if (!textArea || !nextArrow) return;
    textArea.innerText = currentFullText;
  
    if (currentPageIndex < dialoguePages.length - 1) {
      nextArrow.style.display = "none";
  
      const delay = parseInt(vdSettings.autoTurnDelay) || 2500;
      autoTurnTimeout = setTimeout(() => {
        currentPageIndex++;
        typePage(currentPageIndex);
      }, delay);
    } else if (dialogueCompleteCallback && dialogueCompleteRenderId === currentRenderId) {
      const delay = parseInt(vdSettings.autoTurnDelay) || 2500;
      const cb = dialogueCompleteCallback;
      const cbRenderId = dialogueCompleteRenderId;
      dialogueCompleteCallback = null;
      autoTurnTimeout = setTimeout(() => {
        if (cbRenderId === currentRenderId) {
          cb();
        }
      }, delay);
    }
  }
  
  function handleDialogueClick() {
    if (isTyping) {
      finishTyping();
    } else {
      if (currentPageIndex < dialoguePages.length - 1) {
        clearTimeout(autoTurnTimeout);
        currentPageIndex++;
        typePage(currentPageIndex);
      }
    }
  }