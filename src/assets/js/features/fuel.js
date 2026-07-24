import { AUTO_TAB_INTERVAL_MS } from "../config.js";

const fuelRefreshButton = document.getElementById("fuelRefreshButton");
const fuelStatus = document.getElementById("fuelStatus");
const fuelList = document.getElementById("fuelList");
const fuelGroupButtons = [...document.querySelectorAll("[data-fuel-group]")];
const fuelScrollDownButton = document.getElementById("fuelScrollDownButton");
const fuelScrollTopButton = document.getElementById("fuelScrollTopButton");

const FUEL_TAB_INDEX = 2;
const FUEL_GROUP_SWITCH_INTERVAL_MS = AUTO_TAB_INTERVAL_MS / 2;
const FUEL_SCROLL_SPEED = 520;

let fuelScrollAnimationFrame = null;
let fuelScrollLastTime = 0;


let fuelData = { favorites: [], highway: [] };
let activeFuelGroup = "favorites";
let isFuelRefreshing = false;
let fuelGroupSwitchTimer = null;

function setActiveFuelGroup(group) {
  if (!["favorites", "highway"].includes(group)) return;

  activeFuelGroup = group;

  fuelGroupButtons.forEach((button) => {
    button.setAttribute(
      "aria-selected",
      String(button.dataset.fuelGroup === activeFuelGroup)
    );
  });

  renderFuelStations();
}

function stopFuelGroupAutoSwitch() {
  window.clearTimeout(fuelGroupSwitchTimer);
  fuelGroupSwitchTimer = null;
}

function startFuelGroupAutoSwitch() {
  stopFuelGroupAutoSwitch();

  // 유가 탭에 진입하면 항상 즐겨찾기부터 표시
  setActiveFuelGroup("favorites");

  fuelGroupSwitchTimer = window.setTimeout(() => {
    setActiveFuelGroup("highway");
    fuelGroupSwitchTimer = null;
  }, FUEL_GROUP_SWITCH_INTERVAL_MS);
}

function handleMainTabChange(event) {
  const { activeTabIndex, autoTabEnabled } = event.detail;

  if (autoTabEnabled && activeTabIndex === FUEL_TAB_INDEX) {
    startFuelGroupAutoSwitch();
  } else {
    stopFuelGroupAutoSwitch();
  }
}


function formatFuelPrice(price) {
  return Number.isFinite(price) ? `${price.toLocaleString("ko-KR")}원` : "정보 없음";
}

function getCheapestFuelPrices(stations) {
  return ["B027", "D047"].reduce((result, code) => {
    const validPrices = stations.map((station) => station.prices?.[code]?.price).filter(Number.isFinite);
    result[code] = validPrices.length ? Math.min(...validPrices) : null;
    return result;
  }, {});
}

function renderFuelStations() {
  const stations = fuelData[activeFuelGroup] || [];
  const cheapestPrices = getCheapestFuelPrices(stations);
  fuelList.replaceChildren();

  if (!stations.length) {
    const empty = document.createElement("div");
    empty.className = "fuel-empty";
    empty.textContent = "등록된 주유소가 없거나 아직 데이터를 불러오지 않았습니다.";
    fuelList.appendChild(empty);
    requestAnimationFrame(updateFuelScrollButtons);
    return;
  }

  stations.forEach((station) => {
    const card = document.createElement("article");
    card.className = "fuel-card";

    const stationRow = document.createElement("div");
    stationRow.className = "fuel-station-row";
    stationRow.innerHTML = '<span class="fuel-station-name"></span><span class="fuel-station-id"></span>';
    stationRow.querySelector(".fuel-station-name").textContent = station.name || station.id;
    stationRow.querySelector(".fuel-station-id").textContent = station.id;
    card.appendChild(stationRow);

    if (station.error) {
      const error = document.createElement("div");
      error.className = "fuel-error";
      error.textContent = "정보를 불러오지 못했습니다.";
      card.appendChild(error);
    } else {
      const prices = document.createElement("div");
      prices.className = "fuel-prices";
      [["B027", "휘발유"], ["D047", "경유"]].forEach(([code, label]) => {
        const item = document.createElement("div");
        item.className = "fuel-price";
        const value = station.prices?.[code]?.price;
        const isCheapest = Number.isFinite(value) && value === cheapestPrices[code];
        item.classList.toggle("is-cheapest", isCheapest);
        item.innerHTML = '<span class="fuel-product"></span><strong class="fuel-value"></strong>';
        item.querySelector(".fuel-product").textContent = label;
        const valueElement = item.querySelector(".fuel-value");
        valueElement.textContent = formatFuelPrice(value);
        if (isCheapest) {
          const groupLabel = activeFuelGroup === "favorites" ? "즐겨찾기" : "고속도로";
          item.title = `${groupLabel} ${label} 최저가`;
          valueElement.setAttribute("aria-label", `${groupLabel} ${label} 최저가 ${formatFuelPrice(value)}`);
        }
        prices.appendChild(item);
      });
      card.appendChild(prices);
    }
    fuelList.appendChild(card);
  });

  requestAnimationFrame(updateFuelScrollButtons);
}

export async function refreshFuelData() {
  if (isFuelRefreshing) return;
  isFuelRefreshing = true;
  fuelRefreshButton.disabled = true;
  fuelStatus.textContent = "오피넷에서 가격을 불러오는 중입니다…";
  try {
    const response = await fetch("/__opinet__", { cache: "no-store" });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || `HTTP ${response.status}`);
    fuelData = data.groups || { favorites: [], highway: [] };
    const updated = data.updatedAt ? new Date(data.updatedAt) : new Date();
    fuelStatus.textContent = `마지막 갱신: ${updated.toLocaleString("ko-KR")}`;
    renderFuelStations();
    return true;
  } catch (error) {
    console.error("오피넷 가격 갱신 실패", error);
    fuelStatus.textContent = `갱신 실패: ${error.message}`;
    return false;
  } finally {
    isFuelRefreshing = false;
    fuelRefreshButton.disabled = false;
  }
}
function canScrollFuelList() {
  return fuelList.scrollHeight > fuelList.clientHeight + 1;
}

function updateFuelScrollButtons() {
  const hasOverflow = canScrollFuelList();
  const isAtTop = fuelList.scrollTop <= 1;
  const isAtBottom =
    fuelList.scrollTop + fuelList.clientHeight >=
    fuelList.scrollHeight - 1;

  fuelScrollDownButton.hidden = !hasOverflow;
  fuelScrollTopButton.hidden = !hasOverflow;

  fuelScrollDownButton.disabled = !hasOverflow || isAtBottom;
  fuelScrollTopButton.disabled = !hasOverflow || isAtTop;
}

function stopFuelScrollDown() {
  if (fuelScrollAnimationFrame !== null) {
    cancelAnimationFrame(fuelScrollAnimationFrame);
    fuelScrollAnimationFrame = null;
  }

  fuelScrollLastTime = 0;
}

function scrollFuelListDown(timestamp) {
  if (!fuelScrollLastTime) {
    fuelScrollLastTime = timestamp;
  }

  const elapsedSeconds =
    Math.min(timestamp - fuelScrollLastTime, 50) / 1000;

  fuelScrollLastTime = timestamp;
  fuelList.scrollTop += FUEL_SCROLL_SPEED * elapsedSeconds;

  const reachedBottom =
    fuelList.scrollTop + fuelList.clientHeight >=
    fuelList.scrollHeight - 1;

  if (reachedBottom) {
    stopFuelScrollDown();
    updateFuelScrollButtons();
    return;
  }

  fuelScrollAnimationFrame =
    requestAnimationFrame(scrollFuelListDown);
}

function startFuelScrollDown(event) {
  if (!canScrollFuelList()) return;

  event.preventDefault();
  stopFuelScrollDown();

  fuelScrollAnimationFrame =
    requestAnimationFrame(scrollFuelListDown);
}

function scrollFuelListToTop() {
  stopFuelScrollDown();

  fuelList.scrollTo({
    top: 0,
    behavior: "smooth"
  });
}

async function handleManualFuelRefresh() {
  const success = await refreshFuelData();

  if (!success) return;

  window.dispatchEvent(
    new CustomEvent("dailyboard:fuelmanualrefresh")
  );
}

export function initializeFuel() {
  fuelGroupButtons.forEach((button) => {
    button.addEventListener("click", () => {
      stopFuelGroupAutoSwitch();
      setActiveFuelGroup(button.dataset.fuelGroup);
    });
  });

  fuelRefreshButton.addEventListener("click", handleManualFuelRefresh);

  fuelScrollDownButton.addEventListener(
    "pointerdown",
    startFuelScrollDown
  );

  fuelScrollDownButton.addEventListener(
    "pointerup",
    stopFuelScrollDown
  );

  fuelScrollDownButton.addEventListener(
    "pointercancel",
    stopFuelScrollDown
  );

  fuelScrollDownButton.addEventListener(
    "pointerleave",
    stopFuelScrollDown
  );

  fuelScrollDownButton.addEventListener(
    "lostpointercapture",
    stopFuelScrollDown
  );

  fuelScrollTopButton.addEventListener(
    "click",
    scrollFuelListToTop
  );

  fuelList.addEventListener(
    "scroll",
    updateFuelScrollButtons,
    { passive: true }
  );

  window.addEventListener(
    "resize",
    updateFuelScrollButtons
  );

  window.addEventListener(
    "dailyboard:tabchange",
    handleMainTabChange
  );

  updateFuelScrollButtons();
}
