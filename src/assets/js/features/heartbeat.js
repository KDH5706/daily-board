export function sendHeartbeat() {
  fetch("/__heartbeat__", {
    method: "POST",
    cache: "no-store",
    keepalive: true
  }).catch(() => { });
}

export function initializeHeartbeat() {
  window.addEventListener("pageshow", sendHeartbeat);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      sendHeartbeat();
    }
  });

  window.addEventListener("focus", sendHeartbeat);
}