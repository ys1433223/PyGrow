// Global pet state & mode triggers via custom DOM events.
// Any component can import { triggerPetState, setPetMode, addPetMessage } and call it without setup.

const STATE_EVENT = 'pet:state'
const MODE_EVENT = 'pet:mode'
const MSG_EVENT = 'pet:message'

/** Trigger a pet animation state. Duration ms or null for persistent. */
export function triggerPetState(stateName, duration = null) {
  window.dispatchEvent(new CustomEvent(STATE_EVENT, {
    detail: { state: stateName, duration },
  }))
}

/** Set pet visibility/interaction mode: 'active' | 'simplified' | 'silent' | 'hidden' */
export function setPetMode(mode) {
  window.dispatchEvent(new CustomEvent(MODE_EVENT, { detail: { mode } }))
}

/**
 * Add a message to the pet message center and optionally trigger message state.
 * @param {Object} msg - { title, body, category: 'system'|'community'|'task'|'promotion'|'adventure'|'farm' }
 */
export function addPetMessage(msg) {
  window.dispatchEvent(new CustomEvent(MSG_EVENT, {
    detail: {
      id: Date.now(),
      title: msg.title || '',
      body: msg.body || '',
      category: msg.category || 'system',
      ts: Date.now(),
      read: false,
    },
  }))
}

export function listenPetState(handler) {
  const cb = (e) => handler(e.detail.state, e.detail.duration)
  window.addEventListener(STATE_EVENT, cb)
  return () => window.removeEventListener(STATE_EVENT, cb)
}

export function listenPetMode(handler) {
  const cb = (e) => handler(e.detail.mode)
  window.addEventListener(MODE_EVENT, cb)
  return () => window.removeEventListener(MODE_EVENT, cb)
}

export function listenPetMessage(handler) {
  const cb = (e) => handler(e.detail)
  window.addEventListener(MSG_EVENT, cb)
  return () => window.removeEventListener(MSG_EVENT, cb)
}

// ---- Adventure animation coordination ----
const ADVENTURE_START_EVENT = 'pet:adventure-start'
const ADVENTURE_END_EVENT = 'pet:adventure-end'

/** Tell pet to fly to center, scale up, and show happy GIF */
export function triggerPetAdventureStart() {
  window.dispatchEvent(new CustomEvent(ADVENTURE_START_EVENT))
}

/** Tell pet to return to original position and idle state */
export function triggerPetAdventureEnd() {
  window.dispatchEvent(new CustomEvent(ADVENTURE_END_EVENT))
}

export function listenPetAdventureStart(handler) {
  const cb = () => handler()
  window.addEventListener(ADVENTURE_START_EVENT, cb)
  return () => window.removeEventListener(ADVENTURE_START_EVENT, cb)
}

export function listenPetAdventureEnd(handler) {
  const cb = () => handler()
  window.addEventListener(ADVENTURE_END_EVENT, cb)
  return () => window.removeEventListener(ADVENTURE_END_EVENT, cb)
}
