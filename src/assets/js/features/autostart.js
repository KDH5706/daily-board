const autostartToggle = document.getElementById("autostartToggle");

function updateAutostartToggle(enabled) {
  autostartToggle.setAttribute("aria-checked", String(enabled));
}

async function loadAutostartState() {
  autostartToggle.disabled = true;
  try {
    const response = await fetch("/__autostart__", { method: "GET", cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    updateAutostartToggle(Boolean(data.enabled));
  } catch (error) {
    console.warn("자동 실행 상태를 확인하지 못했습니다.", error);
    updateAutostartToggle(false);
  } finally {
    autostartToggle.disabled = false;
  }
}

async function setAutostartEnabled(enabled) {
  autostartToggle.disabled = true;
  try {
    const response = await fetch("/__autostart__", {
      method: "POST",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled })
    });
    const data = await response.json();
    if (!response.ok || !data.success) throw new Error(data.error || `HTTP ${response.status}`);
    updateAutostartToggle(Boolean(data.enabled));
  } catch (error) {
    console.error("자동 실행 설정을 변경하지 못했습니다.", error);
    alert("Windows 자동 실행 설정을 변경하지 못했습니다.");
    await loadAutostartState();
  } finally {
    autostartToggle.disabled = false;
  }
}

export function initializeAutostart() {
  autostartToggle.addEventListener("click", () => {
    const current = autostartToggle.getAttribute("aria-checked") === "true";
    setAutostartEnabled(!current);
  });
  loadAutostartState();
}
