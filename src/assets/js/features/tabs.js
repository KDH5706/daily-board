import { AUTO_TAB_INTERVAL_MS, AUTO_TAB_STORAGE_KEY } from "../config.js";

const tabViewport = document.getElementById("tabViewport");
const tabTrack = document.getElementById("tabTrack");
const tabPages = [...tabTrack.querySelectorAll(".tab-page")];
const autoTabToggle = document.getElementById("autoTabToggle");

const FIRST_REAL_TAB_INDEX = 1;
const LAST_REAL_TAB_INDEX = 3;
const LEFT_FAKE_TAB_INDEX = 0;
const RIGHT_FAKE_TAB_INDEX = 4;
const SWIPE_DISTANCE_THRESHOLD = 70;
const SWIPE_RATIO_THRESHOLD = 0.12;
const TAB_ANIMATION_MS = 520;

let activeTabIndex = FIRST_REAL_TAB_INDEX;
let gestureStartY = 0;
let gestureCurrentY = 0;
let gesturePointerId = null;
let isDraggingTab = false;
let isTabAnimating = false;
let tabAnimationTimer = null;
let autoTabEnabled = false;
let autoTabTimer = null;

function updateAutoTabToggle() {
  autoTabToggle.setAttribute("aria-checked", String(autoTabEnabled));
}

function moveToNextRealTab() {
  if (!autoTabEnabled || isDraggingTab || isTabAnimating) return;
  moveToTab(activeTabIndex + 1, true);
}

function restartAutoTabTimer() {
  window.clearInterval(autoTabTimer);
  autoTabTimer = autoTabEnabled ? window.setInterval(moveToNextRealTab, AUTO_TAB_INTERVAL_MS) : null;
}

function setAutoTabEnabled(enabled) {
  autoTabEnabled = Boolean(enabled);
  localStorage.setItem(AUTO_TAB_STORAGE_KEY, String(autoTabEnabled));
  updateAutoTabToggle();
  restartAutoTabTimer();
  updateActiveTabState();
}

function updateActiveTabState() {
  tabPages.forEach((page, index) =>{
    page.classList.toggle("is-active", index === activeTabIndex)
  });

  window.getSelection()?.removeAllRanges();

  window.dispatchEvent(
    new CustomEvent("dailyboard:tabchange", {
      detail: {
        activeTabIndex,
        autoTabEnabled
      }
    })
  );
}

function tabHeight() {
  return tabViewport.clientHeight || window.innerHeight;
}

function setTrackPosition(index, animated = true) {
  tabTrack.classList.toggle("is-dragging", !animated);
  tabTrack.style.transform = `translate3d(0, ${-index * tabHeight()}px, 0)`;
}

function normalizeFakeTab() {
  if (activeTabIndex === LEFT_FAKE_TAB_INDEX) {
    activeTabIndex = LAST_REAL_TAB_INDEX;
    setTrackPosition(activeTabIndex, false);
  } else if (activeTabIndex === RIGHT_FAKE_TAB_INDEX) {
    activeTabIndex = FIRST_REAL_TAB_INDEX;
    setTrackPosition(activeTabIndex, false);
  }
  updateActiveTabState();
}

function moveToTab(index, animated = true) {
  if (animated && isTabAnimating) return;
  activeTabIndex = Math.max(LEFT_FAKE_TAB_INDEX, Math.min(index, RIGHT_FAKE_TAB_INDEX));
  updateActiveTabState();
  setTrackPosition(activeTabIndex, animated);
  if (!animated) return void (isTabAnimating = false);
  isTabAnimating = true;
  window.clearTimeout(tabAnimationTimer);
  tabAnimationTimer = window.setTimeout(() => {
    normalizeFakeTab();
    isTabAnimating = false;
  }, TAB_ANIMATION_MS);
}

function beginTabGesture(event) {
  if (isTabAnimating || (event.pointerType === "mouse" && event.button !== 0)) return;
  gesturePointerId = event.pointerId;
  gestureStartY = gestureCurrentY = event.clientY;
  isDraggingTab = true;
  tabViewport.classList.add("is-dragging");
  tabTrack.classList.add("is-dragging");
  tabViewport.setPointerCapture?.(event.pointerId);
}

function updateTabGesture(event) {
  if (!isDraggingTab || event.pointerId !== gesturePointerId) return;
  gestureCurrentY = event.clientY;
  const deltaY = gestureCurrentY - gestureStartY;
  tabTrack.style.transform = `translate3d(0, ${-activeTabIndex * tabHeight() + deltaY}px, 0)`;
}

function releaseTabPointerCapture(pointerId) {
  if (pointerId == null) return;
  try {
    if (tabViewport.hasPointerCapture?.(pointerId)) tabViewport.releasePointerCapture(pointerId);
  } catch (error) {
    console.warn("포인터 캡처 해제 실패", error);
  }
}

function cleanupPointerState(pointerId = null) {
  releaseTabPointerCapture(pointerId ?? gesturePointerId);
  isDraggingTab = false;
  gesturePointerId = null;
  tabViewport.classList.remove("is-dragging");
  tabTrack.classList.remove("is-dragging");
  window.getSelection()?.removeAllRanges();
}

function endTabGesture(event) {
  if (!isDraggingTab || event.pointerId !== gesturePointerId) {
    cleanupPointerState(event.pointerId);
    return;
  }
  const deltaY = gestureCurrentY - gestureStartY;
  const threshold = Math.max(SWIPE_DISTANCE_THRESHOLD, tabHeight() * SWIPE_RATIO_THRESHOLD);
  let nextIndex = activeTabIndex;
  if (deltaY <= -threshold) nextIndex++;
  else if (deltaY >= threshold) nextIndex--;
  cleanupPointerState(event.pointerId);
  moveToTab(nextIndex, true);
}

export function initializeTabs() {
  autoTabEnabled = localStorage.getItem(AUTO_TAB_STORAGE_KEY) === "true";
  updateAutoTabToggle();
  restartAutoTabTimer();
  autoTabToggle.addEventListener("click", () => setAutoTabEnabled(!autoTabEnabled));

  tabViewport.addEventListener("pointerdown", beginTabGesture);
  tabViewport.addEventListener("pointermove", updateTabGesture);
  tabViewport.addEventListener("pointerup", endTabGesture);
  tabViewport.addEventListener("pointercancel", (event) => {
    cleanupPointerState(event.pointerId);
    setTrackPosition(activeTabIndex, true);
  });
  tabViewport.addEventListener("lostpointercapture", () => cleanupPointerState());
  window.addEventListener("resize", () => setTrackPosition(activeTabIndex, false));

  setTrackPosition(FIRST_REAL_TAB_INDEX, false);
  updateActiveTabState();
}
