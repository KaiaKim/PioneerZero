import React, { useEffect, useMemo, useRef, useState } from "react";
import { getActionQueuePosition, setActionQueuePosition } from "../../storage";

const ActionQueue = ({
  players = [],
  actionSubmissionStatus = [],
  declaredAttack = null,
  offsetCountdown = null,
  phaseCountdown = null,
}) => {
  const containerRef = useRef(null);
  const attackTypeSelectRef = useRef(null);
  const attackTargetInputRef = useRef(null);
  const dragState = useRef({ active: false, offsetX: 0, offsetY: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [showGlow, setShowGlow] = useState(false);
  const [position, setPosition] = useState(() => {
    if (typeof window === "undefined") return null;
    return getActionQueuePosition();
  });

  useEffect(() => {
    if (!position || typeof window === "undefined") return;
    setActionQueuePosition(position);
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

  const submissionBySlotIndex = useMemo(() => {
    const map = new Map();
    for (const entry of actionSubmissionStatus || []) {
      const idx = entry?.slot_idx ?? entry?.slot;
      if (entry && typeof idx === "number") {
        map.set(idx, entry.submitted === true);
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
      const slotIndex = player?.index ?? player?.slot ?? index;
      return submissionBySlotIndex.get(slotIndex) === true ? count + 1 : count;
    }, 0);
  }, [players, playerCount, submissionBySlotIndex]);

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
        <label>대상:</label>
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
        <label>대상:</label>
        <input type="text" placeholder="자신"/>
      </div>
      <div>
        <label className="action-queue-priority">우선도:0</label>
        <label className="action-queue-attack-power"> 공격력:0</label>
        <label className="action-queue-effect">효과:</label>
      </div>
      <div className="action-queue-footer">
        <div className="action-queue-status">제출현황: {submittedCount}/{playerCount}</div>

        <div className="timer"> 제한시간:
          {offsetCountdown && (
            <div id="offset-countdown" className="offset-countdown-spinner" aria-label="Waiting">
              {/* Dev: numeric countdown — {offsetCountdown} */}
              <span className="hourglass-icon" aria-hidden="true">⌛</span>
            </div>
          )}
          {phaseCountdown && (
          <div id="phase-countdown">{String(phaseCountdown).padStart(2, '0')}</div>
          )}
        </div>

        <div className="action-queue-quick-progress"> 빠른진행:
          <input className="action-queue-quick-progress-checkbox" type="checkbox" />
        </div>
      </div>

    </div>
  );
};

export default ActionQueue;
