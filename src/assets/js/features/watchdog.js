export function sendWatchdog() {
  fetch("/__heartbeat__", {
    method: "POST",
    cache: "no-store",
    keepalive: true
  }).catch(() => { });
}

export function initializeWatchdog() {
  window.addEventListener("pageshow", sendWatchdog);

  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) {
      sendWatchdog();
    }
  });

  window.addEventListener("focus", sendWatchdog);
}