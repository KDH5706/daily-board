const fullscreenButton = document.getElementById("fullscreenButton");
const fullscreenButtonText = document.getElementById("fullscreenButtonText");

function isFullscreenSupported() {
  return typeof document.documentElement.requestFullscreen === "function";
}

function updateFullscreenButton() {
  const isFullscreen = Boolean(document.fullscreenElement);
  fullscreenButton.setAttribute("aria-pressed", String(isFullscreen));
  fullscreenButton.title = isFullscreen ? "전체화면 종료" : "전체화면으로 전환";
  fullscreenButtonText.textContent = isFullscreen ? "전체화면 종료" : "전체화면";
}

async function toggleFullscreen() {
  if (!isFullscreenSupported()) return;
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await document.documentElement.requestFullscreen();
  } catch (error) {
    console.error("전체화면 전환 실패", error);
    alert("전체화면으로 전환하지 못했습니다.");
  }
}

export function initializeFullscreenButton() {
  fullscreenButton.disabled = !isFullscreenSupported();
  updateFullscreenButton();
  fullscreenButton.addEventListener("click", toggleFullscreen);
  document.addEventListener("fullscreenchange", updateFullscreenButton);
}
