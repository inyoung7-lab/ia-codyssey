"use strict";
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const button = document.getElementById("theme-toggle");
  button.setAttribute("aria-pressed", String(theme === "dark"));
  button.textContent = theme === "dark" ? "다크 모드 켜짐 · 밝게 전환" : "다크 모드 꺼짐 · 어둡게 전환";
  window.dispatchEvent(new Event("fitlog-theme-change"));
}
let initialTheme;
try { initialTheme = localStorage.getItem("fitlog-theme"); } catch { /* Private browsing may block storage. */ }
if (!["light", "dark"].includes(initialTheme)) initialTheme = window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
applyTheme(initialTheme);
document.getElementById("theme-toggle").addEventListener("click", () => {
  const theme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  applyTheme(theme);
  try { localStorage.setItem("fitlog-theme", theme); } catch { /* Theme still works for this page. */ }
});
