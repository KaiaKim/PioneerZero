import React, { useEffect, useMemo, useRef, useState } from "react";

const ActionQueue = ({ players = [], actionSubmissionStatus = [], declaredAttack = null }) => {
  const containerRef = useRef(null);
  const attackTypeSelectRef = useRef(null);
  const attackTargetInputRef = useRef(null);
  const dragState = useRef({ active: false, offsetX: 0, offsetY: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [showGlow, setShowGlow] = useState(false);
  const [position, setPosition] = useState(() => {
    if (typeof window === "undefined") {
      return null;
    }
    try {
      const raw = window.localStorage.getItem("actionQueuePosition");
      if (!raw) {
        return null;
      }
      const parsed = JSON.parse(raw);
      if (typeof parsed?.x === "number" && typeof parsed?.y === "number") {
        return { x: parsed.x, y: parsed.y };
      }
    } catch (error) {
      return null;
    }
    return null;
  });

  useEffect(() => {
    if (!position || typeof window === "undefined") {
      return;
    }
    try {
      window.localStorage.setItem("actionQueuePosition", JSON.stringify(position));
    } catch (error) {
      return;
    }
  }, [position]);

  useEffect(() => {
    const handlePointerMove = (event) => {
      if (!dragState.current.active) {
        return;
      }
      const container = containerRef.current;
      const width = container?.offsetWidth ?? 0;
      const height = container?.offsetHeight ?? 0;
      const maxX = Math.max(0, window.innerWidth - width);
      const maxY = Math.max(0, window.innerHeight - height);
      const nextX = event.clientX - dragState.current.offsetX;
      const nextY = event.clientY - dragState.current.offsetY;
      const clampedX = Math.min(Math.max(0, nextX), maxX);
      const clampedY = Math.min(Math.max(0, nextY), maxY);
      setPosition({ x: clampedX, y: clampedY });
    };

    const handlePointerUp = (event) => {
      if (!dragState.current.active) {
        return;
      }
      dragState.current.active = false;
      setIsDragging(false);
      const container = containerRef.current;
      container?.releasePointerCapture?.(event.pointerId);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
    return () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };
  }, []);

  const submissionBySlot = useMemo(() => {
    const map = new Map();
    for (const entry of actionSubmissionStatus || []) {
      if (entry && typeof entry.slot === "number") {
        map.set(entry.slot, entry.submitted === true);
      }
    }
    return map;
  }, [actionSubmissionStatus]);

  const handlePointerDown = (event) => {
    if (event.button !== 0) {
      return;
    }
    if (
      event.target instanceof Element &&
      event.target.closest("input, select, textarea, button, label, option")
    ) {
      return;
    }
    const container = containerRef.current;
    if (!container) {
      return;
    }
    const rect = container.getBoundingClientRect();
    dragState.current.active = true;
    dragState.current.offsetX = event.clientX - rect.left;
    dragState.current.offsetY = event.clientY - rect.top;
    setIsDragging(true);
    container.setPointerCapture?.(event.pointerId);
    event.preventDefault();
  };

  // Update form fields when declaredAttack changes
  useEffect(() => {
    if (declaredAttack && attackTypeSelectRef.current && attackTargetInputRef.current) {
      const actionType = declaredAttack.action_type || declaredAttack.type;
      if (actionType && ["근거리공격", "원거리공격", "대기"].includes(actionType)) {
        attackTypeSelectRef.current.value = actionType;
      }
      if (declaredAttack.target) {
        attackTargetInputRef.current.value = declaredAttack.target;
      }
      
      // Trigger glow animation
      setShowGlow(true);
      const timer = setTimeout(() => {
        setShowGlow(false);
      }, 600); // Match animation duration
      
      return () => clearTimeout(timer);
    }
  }, [declaredAttack]);

  const playerCount = players.length;
  const submittedCount = useMemo(() => {
    if (!playerCount) {
      return 0;
    }
    return players.reduce((count, player, index) => {
      const slot = player?.slot ?? index + 1;
      return submissionBySlot.get(slot) === true ? count + 1 : count;
    }, 0);
  }, [players, playerCount, submissionBySlot]);

  return (
    <div
      className={`action-queue ${isDragging ? "is-dragging" : "draggable"} ${showGlow ? "glow-animation" : ""}`}
      ref={containerRef}
      onPointerDown={handlePointerDown}
      style={
        position
          ? {
              left: `${position.x}px`,
              top: `${position.y}px`,
              right: "auto",
            }
          : undefined
      }
    >
      <h3>Action Queue</h3>
      <div>
        <label>공격:</label>
        <select ref={attackTypeSelectRef} className="action-queue-attack-type">
          <option value="근거리공격">근거리 공격</option>
          <option value="원거리공격">원거리 공격</option>
          <option value="대기">대기</option>
        </select>
        <label>공격대상:</label>
        <input ref={attackTargetInputRef} className="action-queue-attack-target" type="text" placeholder="예: Y1" />
      </div>
      <div>
        <label>스킬:</label>
        <select>
          <option value="skill1">스킬1</option>
          <option value="skill2">스킬2</option>
          <option value="skill3">스킬3</option>
          <option value="skill4">스킬4</option>
        </select>
        <label>스킬 대상:</label>
        <input type="text" placeholder="자신"/>
      </div>
      <div><label className="action-queue-priority">우선도:0</label><label className="action-queue-attack-power"> 공격력:0</label></div>
      <div><label className="action-queue-effect">효과:</label></div>
      {playerCount > 0 && (
        <div className="action-queue-status">
          제출현황: {submittedCount}/{playerCount}
        </div>
      )}
      <label>빠른진행:</label>
      <input type="checkbox" />

    </div>
  );
};

export default ActionQueue;
