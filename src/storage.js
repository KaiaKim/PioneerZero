/**
 * Centralized localStorage module.
 * All keys, value types, and get/set/remove go through this module.
 *
 * Schema:
 * - user_info          – object { id?, name?, ... } (from auth); default null
 * - guest_id           – string (UUID); default null
 * - chatTabSettings    – array of tab config rows; default DEFAULT_TAB_CONFIG
 * - chatType_{gameId}  – string 'dialogue'|'communication'|'chitchat'; default 'dialogue'
 * - chatUnreadByTabId_{gameId} – object { [tabId: number]: boolean }; default {}
 * - player_slot_{gameId} – string (slot number); default null
 * - actionQueuePosition – object { x: number, y: number } | null; default null
 */

const USER_INFO_KEY = 'user_info';
const GUEST_ID_KEY = 'guest_id';
const CHAT_TAB_SETTINGS_KEY = 'chatTabSettings';
const CHAT_TYPE_KEY_PREFIX = 'chatType_';
const CHAT_UNREAD_KEY_PREFIX = 'chatUnreadByTabId_';
const PLAYER_SLOT_KEY_PREFIX = 'player_slot_';
const ACTION_QUEUE_POSITION_KEY = 'actionQueuePosition';

const VALID_CHAT_TYPES = ['dialogue', 'communication', 'chitchat'];

export const DEFAULT_TAB_CONFIG = [
  { id: 1, tabName: '메인', system: true, dialogue: true, command: true, communication: false, spy: false, chitchat: false },
  { id: 2, tabName: '팀', system: false, dialogue: false, command: false, communication: true, spy: true, chitchat: false },
  { id: 3, tabName: '사담', system: false, dialogue: false, command: false, communication: false, spy: false, chitchat: true },
];

function safeGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSet(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

function safeRemove(key) {
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

// --- user_info ---
export function getUserInfo() {
  const raw = safeGet(USER_INFO_KEY);
  if (raw == null) return null;
  try {
    const parsed = JSON.parse(raw);
    return typeof parsed === 'object' && parsed !== null ? parsed : null;
  } catch {
    return null;
  }
}

export function setUserInfo(value) {
  if (value == null) {
    safeRemove(USER_INFO_KEY);
    return;
  }
  safeSet(USER_INFO_KEY, JSON.stringify(value));
}

export function removeUserInfo() {
  safeRemove(USER_INFO_KEY);
}

// --- guest_id ---
export function getGuestId() {
  return safeGet(GUEST_ID_KEY);
}

export function setGuestId(value) {
  if (value == null) safeRemove(GUEST_ID_KEY);
  else safeSet(GUEST_ID_KEY, value);
}

// --- chatTabSettings ---
export function getChatTabSettings() {
  const raw = safeGet(CHAT_TAB_SETTINGS_KEY);
  if (raw == null) return [...DEFAULT_TAB_CONFIG];
  try {
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed) || parsed.length === 0) return [...DEFAULT_TAB_CONFIG];
    const hasMain = parsed.some((r) => r && r.tabName === '메인');
    if (!hasMain) return [...DEFAULT_TAB_CONFIG];
    return parsed;
  } catch {
    return [...DEFAULT_TAB_CONFIG];
  }
}

export function setChatTabSettings(value) {
  const hasMain = value && value.some((r) => r && r.tabName === '메인');
  const toSave = hasMain ? value : [...DEFAULT_TAB_CONFIG];
  safeSet(CHAT_TAB_SETTINGS_KEY, JSON.stringify(toSave));
}

// --- chatType (per gameId) ---
function getChatTypeKey(gameId) {
  return CHAT_TYPE_KEY_PREFIX + (gameId || 'default');
}

export function getChatType(gameId) {
  const v = safeGet(getChatTypeKey(gameId));
  return VALID_CHAT_TYPES.includes(v) ? v : 'dialogue';
}

export function setChatType(gameId, value) {
  safeSet(getChatTypeKey(gameId), value);
}

// --- chatUnreadByTabId (per gameId) ---
function getChatUnreadKey(gameId) {
  return CHAT_UNREAD_KEY_PREFIX + (gameId || 'default');
}

export function getChatUnreadByTabId(gameId) {
  const raw = safeGet(getChatUnreadKey(gameId));
  if (raw == null) return {};
  try {
    const parsed = JSON.parse(raw);
    return typeof parsed === 'object' && parsed !== null ? parsed : {};
  } catch {
    return {};
  }
}

export function setChatUnreadByTabId(gameId, value) {
  safeSet(getChatUnreadKey(gameId), JSON.stringify(value));
}

// --- player_slot (per gameId) ---
function getPlayerSlotKey(gameId) {
  return PLAYER_SLOT_KEY_PREFIX + gameId;
}

export function getPlayerSlot(gameId) {
  const v = safeGet(getPlayerSlotKey(gameId));
  return v != null && v !== '' ? v : null;
}

export function setPlayerSlot(gameId, value) {
  const key = getPlayerSlotKey(gameId);
  if (value == null || value === '') safeRemove(key);
  else safeSet(key, String(value));
}

export function removePlayerSlot(gameId) {
  safeRemove(getPlayerSlotKey(gameId));
}

// --- actionQueuePosition ---
export function getActionQueuePosition() {
  const raw = safeGet(ACTION_QUEUE_POSITION_KEY);
  if (raw == null) return null;
  try {
    const parsed = JSON.parse(raw);
    if (parsed != null && typeof parsed.x === 'number' && typeof parsed.y === 'number') {
      return { x: parsed.x, y: parsed.y };
    }
  } catch {
    // ignore
  }
  return null;
}

export function setActionQueuePosition(value) {
  if (value == null) safeRemove(ACTION_QUEUE_POSITION_KEY);
  else safeSet(ACTION_QUEUE_POSITION_KEY, JSON.stringify(value));
}
