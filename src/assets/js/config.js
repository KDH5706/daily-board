export const WEEKDAYS_FULL = [
  "일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"
];

export const WEEKDAYS_SHORT = ["일", "월", "화", "수", "목", "금", "토"];

export const DEFAULT_LOCATION = { latitude: 37.5665, longitude: 126.9780 };
export const SUN_API_URL = "https://api.sunrise-sunset.org/json";

export const THEME_STORAGE_KEY = "dailyBoardThemeMode";
export const THEME_MODES = new Set(["light", "dark", "auto"]);
export const AUTO_TAB_STORAGE_KEY = "dailyBoardAutoTabEnabled";

export const AUTO_TAB_INTERVAL_MS = 10 * 1000;
export const WATCHDOG_INTERVAL_MS = 2000;
export const FUEL_REFRESH_INTERVAL_MS = 60 * 60 * 1000;
