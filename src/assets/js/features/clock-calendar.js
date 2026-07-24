import { WEEKDAYS_FULL, WEEKDAYS_SHORT } from "../config.js";
import { padTwoDigits } from "../utils/date.js";

let renderedDateKey = "";

export function updateClock() {
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const date = now.getDate();
  const weekday = now.getDay();

  document.getElementById("dateText").textContent = `${month + 1}월 ${date}일`;
  document.getElementById("weekdayText").textContent = WEEKDAYS_FULL[weekday];
  document.getElementById("hourMinute").textContent = `${padTwoDigits(now.getHours())}:${padTwoDigits(now.getMinutes())}`;
  document.getElementById("seconds").textContent = padTwoDigits(now.getSeconds());

  const dateKey = `${year}-${month}-${date}`;
  if (renderedDateKey !== dateKey) {
    renderCalendar(now);
    renderedDateKey = dateKey;
  }
}

function renderCalendar(now) {
  const year = now.getFullYear();
  const month = now.getMonth();
  const today = now.getDate();

  document.querySelectorAll("[data-calendar-title]").forEach((title) => {
    title.textContent = `${year}년 ${month + 1}월`;
  });

  const firstWeekday = new Date(year, month, 1).getDay();
  const lastDate = new Date(year, month + 1, 0).getDate();
  const previousLastDate = new Date(year, month, 0).getDate();
  const cells = [];

  for (let index = firstWeekday - 1; index >= 0; index--) cells.push({ date: previousLastDate - index, outside: true });
  for (let day = 1; day <= lastDate; day++) cells.push({ date: day, outside: false });
  for (let nextDate = 1; cells.length < 42; nextDate++) cells.push({ date: nextDate, outside: true });

  document.querySelectorAll("[data-calendar]").forEach((calendar) => {
    calendar.replaceChildren();
    WEEKDAYS_SHORT.forEach((name, index) => {
      const label = document.createElement("div");
      label.className = "weekday-label";
      if (index === 0) label.classList.add("sun");
      if (index === 6) label.classList.add("sat");
      label.textContent = name;
      calendar.appendChild(label);
    });

    cells.forEach((cell, index) => {
      const element = document.createElement("div");
      const column = index % 7;
      element.className = "day";
      element.textContent = cell.date;
      if (column === 0) element.classList.add("sun");
      if (column === 6) element.classList.add("sat");
      if (cell.outside) element.classList.add("outside");
      if (!cell.outside && cell.date === today) {
        element.classList.add("today");
        element.setAttribute("aria-current", "date");
      }
      calendar.appendChild(element);
    });
  });
}
