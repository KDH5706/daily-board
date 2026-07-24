import { DEFAULT_LOCATION, SUN_API_URL, THEME_MODES, THEME_STORAGE_KEY } from "../config.js";
import { localDateKey } from "../utils/date.js";

let sunriseTime = null;
let sunsetTime = null;
let sunDataDateKey = "";
let themeMode = "light";

function getCurrentPosition() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(DEFAULT_LOCATION);
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => resolve({ latitude: coords.latitude, longitude: coords.longitude }),
      () => resolve(DEFAULT_LOCATION),
      { enableHighAccuracy: false, timeout: 8000, maximumAge: 12 * 60 * 60 * 1000 }
    );
  });
}
export async function loadSunTimes() {
  const todayKey = localDateKey();

  try {
    const { latitude, longitude } = await getCurrentPosition();

    const params = new URLSearchParams({
      lat: String(latitude),
      lng: String(longitude),
      date: todayKey,
      formatted: "0",
    });

    const response = await fetch(`${SUN_API_URL}?${params}`, {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    const civilBegin = data.results?.civil_twilight_begin;
    const civilEnd = data.results?.civil_twilight_end;

    if (data.status !== "OK" || !civilBegin || !civilEnd) {
      throw new Error("Invalid civil twilight response");
    }

    sunriseTime = new Date(civilBegin);
    sunsetTime = new Date(civilEnd);
    sunDataDateKey = todayKey;
  } catch (error) {
    console.warn(
      "시민박명 API 호출 실패. 기본 시간으로 전환합니다.",
      error,
    );

    const now = new Date();

    sunriseTime = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
      5,
      30,
      0,
    );

    sunsetTime = new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
      20,
      0,
      0,
    );

    sunDataDateKey = todayKey;
  }

  applyThemeBySun();
}

function setDarkTheme(isDark) {
  document.documentElement.classList.toggle("dark", isDark);
  document.documentElement.style.colorScheme = isDark ? "dark" : "light";
}

function applyThemeBySun() {
  if (themeMode !== "auto" || !sunriseTime || !sunsetTime) return;
  const now = new Date();
  setDarkTheme(now < sunriseTime || now >= sunsetTime);
}

function updateThemeControls() {
  document.querySelectorAll("[data-theme-mode]").forEach((button) => {
    const selected = button.dataset.themeMode === themeMode;
    button.setAttribute("aria-checked", String(selected));
    button.tabIndex = selected ? 0 : -1;
  });
}

function applyThemeMode() {
  if (themeMode === "dark") setDarkTheme(true);
  else if (themeMode === "light") setDarkTheme(false);
  else if (sunriseTime && sunsetTime) applyThemeBySun();
  else setDarkTheme(false);
  updateThemeControls();
}

function setThemeMode(mode) {
  if (!THEME_MODES.has(mode)) return;
  themeMode = mode;
  localStorage.setItem(THEME_STORAGE_KEY, mode);
  applyThemeMode();
  if (mode === "auto" && sunDataDateKey !== localDateKey()) loadSunTimes();
}

export function initializeThemeControls() {
  const savedMode = localStorage.getItem(THEME_STORAGE_KEY);
  themeMode = THEME_MODES.has(savedMode) ? savedMode : "light";
  const buttons = [...document.querySelectorAll("[data-theme-mode]")];
  buttons.forEach((button, index) => {
    button.addEventListener("click", () => setThemeMode(button.dataset.themeMode));
    button.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      let nextIndex = index;
      if (event.key === "ArrowLeft") nextIndex = (index - 1 + buttons.length) % buttons.length;
      if (event.key === "ArrowRight") nextIndex = (index + 1) % buttons.length;
      if (event.key === "Home") nextIndex = 0;
      if (event.key === "End") nextIndex = buttons.length - 1;
      const nextButton = buttons[nextIndex];
      setThemeMode(nextButton.dataset.themeMode);
      nextButton.focus();
    });
  });
  applyThemeMode();
}

export function updateSunTheme() {
  if (themeMode !== "auto") return;
  if (sunDataDateKey !== localDateKey()) return void loadSunTimes();
  applyThemeBySun();
}
