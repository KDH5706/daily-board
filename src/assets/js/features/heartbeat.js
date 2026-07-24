export function sendHeartbeat() {
  fetch("/__heartbeat__", { method: "POST", cache: "no-store", keepalive: true }).catch(() => {});
}

export function notifyPageClosed() {
  navigator.sendBeacon("/__closed__");
}

export function initializeHeartbeat() {
  window.addEventListener("pagehide", notifyPageClosed);
}
