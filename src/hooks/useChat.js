
// ========== 대화 렌더링 (페이지 지원) ==========
function renderDialogue(speakerName, messageText, isDesc, isUnregistered) {
    if (vdSettings.isOverlayHidden) {
      lastRenderedData = { speakerName, messageText, isDesc, isUnregistered };
      return;
    }
  
    clearInterval(typeInterval);
    clearTimeout(autoTurnTimeout);
    isTyping = false;
  
    lastRenderedData = { speakerName, messageText, isDesc, isUnregistered };
  
    root.style.display = "block";
    root.style.visibility = "visible";
    root.style.opacity = "0";
  
    currentRenderId++;
    const thisRenderId = currentRenderId;
  
    let cleanText = messageText;
    cleanText = cleanText.replace(/^\d{1,2}:\d{2}\s?[AP]M[^:]+:\s*/gi, "");
    cleanText = cleanText.replace(/^\d{1,2}:\d{2}:\d{2}\s?[AP]M[^:]+:\s*/gi, "");
    cleanText = cleanText.replace(/^\d{1,2}:\d{2}\s?[^:]+:\s*/g, "");
  
    const standingLayer = shadow.getElementById("standing-layer");
    const namePlate = shadow.getElementById("name-plate");
    const textArea = shadow.getElementById("text-area");
    const nextArrow = shadow.getElementById("next-arrow");
    const uiLayer = shadow.getElementById("ui-layer");
  
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
        adjustVNPosition();
      } catch (error) {
        console.error("[VD Render] 페이지 나누기 오류:", error);
        textArea.innerText = cleanText;
        root.style.opacity = "1";
      }
    });
  }
  
  function typePage(pageIndex) {
    if (pageIndex >= dialoguePages.length) return;
  
    const textArea = shadow.getElementById("text-area");
    const nextArrow = shadow.getElementById("next-arrow");
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
  
    const textArea = shadow.getElementById("text-area");
    textArea.innerText = currentFullText;
  
    const nextArrow = shadow.getElementById("next-arrow");
    if (currentPageIndex < dialoguePages.length - 1) {
      nextArrow.style.display = "none";
  
      const delay = parseInt(vdSettings.autoTurnDelay) || 2500;
      autoTurnTimeout = setTimeout(() => {
        currentPageIndex++;
        typePage(currentPageIndex);
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