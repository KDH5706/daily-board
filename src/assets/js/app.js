import { FUEL_REFRESH_INTERVAL_MS, HEARTBEAT_INTERVAL_MS } from "./config.js";
import { initializeAutostart } from "./features/autostart.js";
import { updateClock } from "./features/clock-calendar.js";
import { initializeFuel, refreshFuelData } from "./features/fuel.js";
import { initializeFullscreenButton } from "./features/fullscreen.js";
import { initializeHeartbeat, sendHeartbeat } from "./features/heartbeat.js";
import { initializeTabs } from "./features/tabs.js";
import { initializeThemeControls, loadSunTimes, updateSunTheme } from "./features/theme.js";
import { initializeShutdownButton } from "./features/shutdown.js";

const DESIGN_WIDTH = 1920;
const DESIGN_HEIGHT = 1280;
let fuelRefreshTimer = null;

function resizeBoard() {
  const board = document.getElementById("dailyBoard");
  if (!board) return;

  const scale = Math.min(
    window.innerWidth / DESIGN_WIDTH,
    window.innerHeight / DESIGN_HEIGHT
  );

  const scaledWidth = DESIGN_WIDTH * scale;
  const scaledHeight = DESIGN_HEIGHT * scale;

  const offsetX = (window.innerWidth - scaledWidth) / 2;
  const offsetY = (window.innerHeight - scaledHeight) / 2;

  board.style.transform =
    `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
}

function restartFuelRefreshTimer() {
  window.clearTimeout(fuelRefreshTimer);

  fuelRefreshTimer = window.setTimeout(async () => {
    await refreshFuelData();
    restartFuelRefreshTimer();
  }, FUEL_REFRESH_INTERVAL_MS);
}


function initializeApp() {
  initializeAutostart();
  initializeThemeControls();
  initializeFullscreenButton();
  initializeTabs();
  initializeFuel();
  initializeHeartbeat();
  initializeShutdownButton();

  window.addEventListener("dailyboard:fuelmanualrefresh",  restartFuelRefreshTimer);
  
  updateClock();
  loadSunTimes();
  refreshFuelData().finally(restartFuelRefreshTimer);
  sendHeartbeat();

  resizeBoard();
  window.addEventListener("resize", resizeBoard);
  document.addEventListener("fullscreenchange", resizeBoard);
  
  setInterval(updateClock, 1000);
  setInterval(updateSunTheme, 60 * 1000);
  setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);
}

initializeApp();
