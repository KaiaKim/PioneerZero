import React, { useEffect, useRef, useState } from "react";

const ActionQueue = () => {
  const containerRef = useRef(null);
  const dragState = useRef({ active: false, offsetX: 0, offsetY: 0 });
  const [isDragging, setIsDragging] = useState(false);
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

  return (
    <div
      className={`action-queue ${isDragging ? "is-dragging" : "draggable"}`}
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
        <select>
          <option value="melee_attack">근거리 공격</option>
          <option value="ranged_attack">원거리 공격</option>
          <option value="wait">대기</option>
        </select>
        <label>공격대상:</label>
        <input type="text" placeholder="예: Y1" />
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
      <div><label>우선도:</label></div>
      <div><label>공격력:</label></div>
      <div><label>효과:</label></div>
    </div>
  );
};

export default ActionQueue;
