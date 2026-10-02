"use strict";

const element = (id) => document.getElementById(id);
const number = (value) => new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value);
const workoutChart = createWorkoutChart();

function status(id, message, error = false) {
  element(id).textContent = message;
  element(id).classList.toggle("error", error);
}

async function get(path, options = {}, timeoutMs = 40000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, { ...options, signal: controller.signal });
    if (!response.ok) {
      const error = new Error("API request failed");
      error.status = response.status;
      const body = await response.json().catch(() => null);
      if (typeof body?.detail === "string") error.detail = body.detail;
      throw error;
    }
    return response.status === 204 ? null : await response.json();
  } finally {
    clearTimeout(timer);
  }
}

async function loadSummary() {
  element("summary").hidden = true;
  status("summary-status", "운동 요약을 불러오는 중입니다.");
  try {
    const data = await get("/workouts/summary");
    if (!data.total_records) {
      status("summary-status", "아직 저장된 운동 기록이 없습니다.");
      return;
    }
    element("total").textContent = `${number(data.total_records)}일`;
    element("period").textContent = `기록 기간: ${data.start_date} ~ ${data.end_date}`;
    for (const [id, key] of [["average", "average_value"], ["minimum", "min_value"], ["maximum", "max_value"]]) {
      element(id).textContent = `${number(data[key])}분`;
    }
    element("summary").hidden = false;
    status("summary-status", "");
  } catch {
    status("summary-status", "요약을 불러오지 못했습니다. API 서버 연결을 확인한 뒤 새로고침해 주세요.", true);
  }
}

async function loadRecent() {
  element("recent-table").hidden = true;
  element("recent").replaceChildren();
  status("recent-status", "운동 기록을 불러오는 중입니다.");
  try {
    const records = await get("/workouts");
    const recent = [...records].sort((a, b) => b.date.localeCompare(a.date)).slice(0, 7);
    if (!recent.length) {
      status("recent-status", "아직 저장된 운동 기록이 없습니다.");
      return;
    }
    for (const record of recent) {
      const row = document.createElement("tr");
      for (const value of [record.date, `${number(record.value)}분`, record.memo]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      }
      element("recent").append(row);
    }
    element("recent-table").hidden = false;
    status("recent-status", "");
  } catch {
    status("recent-status", "운동 기록을 불러오지 못했습니다. API 서버 연결을 확인한 뒤 새로고침해 주세요.", true);
  }
}

let refreshQueue = Promise.resolve();
function refresh() {
  const update = async () => {
    element("refresh").disabled = true;
    try { await Promise.all([loadSummary(), loadRecent()]); }
    finally { element("refresh").disabled = false; }
  };
  // Serialize startup, manual refresh and post-save refresh to avoid duplicate rows.
  refreshQueue = refreshQueue.then(update, update);
  return refreshQueue;
}

element("date-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const date = element("date").value;
  if (!date) { status("date-status", "조회할 날짜를 선택해 주세요."); return; }
  element("search").disabled = true;
  element("date").disabled = true;
  element("date-result").hidden = true;
  element("date-result").replaceChildren();
  status("date-status", "해당 날짜의 기록을 불러오는 중입니다.");
  try {
    const record = await get(`/workouts/${encodeURIComponent(date)}`);
    for (const [label, value] of [["날짜", record.date], ["운동시간", `${number(record.value)}분`], ["메모", record.memo]]) {
      const term = document.createElement("dt");
      const detail = document.createElement("dd");
      term.textContent = label;
      detail.textContent = value;
      element("date-result").append(term, detail);
    }
    element("date-result").hidden = false;
    status("date-status", "기록을 조회했습니다.");
  } catch (error) {
    status("date-status", error.status === 404 ? "해당 날짜의 운동 기록이 없습니다." : "기록을 조회하지 못했습니다. API 서버 연결을 확인한 뒤 다시 시도해 주세요.", error.status !== 404);
  } finally {
    element("search").disabled = false;
    element("date").disabled = false;
  }
});
let saving = false;
const today = new Date();
element("entry-date").value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
element("create-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (saving) return;
  if (!element("create-form").reportValidity()) {
    status("save-status", "날짜와 운동시간 입력값을 확인해 주세요.", true);
    return;
  }
  const value = Number(element("entry-value").value);
  const memo = element("entry-memo").value.trim();
  if (!Number.isInteger(value) || value < 0 || value > 1440 || memo.length > 500) {
    status("save-status", "운동시간은 0~1440의 정수, 메모는 500자 이내로 입력해 주세요.", true);
    return;
  }
  saving = true;
  element("save").disabled = true;
  element("save").textContent = "저장 중...";
  element("create-fields").disabled = true;
  status("save-status", "운동 기록을 저장하는 중입니다.");
  try {
    await get("/workouts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date: element("entry-date").value, value, memo }),
    });
    element("create-form").reset();
    status("save-status", "운동 기록이 저장되었습니다.");
    await refresh();
  } catch (error) {
    let message;
    if (error.status === 409) message = "해당 날짜의 운동 기록이 이미 존재합니다.";
    else if (error.status === 422 || error.status === 400) message = "날짜, 운동시간(0~1440 정수), 메모(500자 이내)를 확인해 주세요.";
    else if (error.status) message = "서버 오류로 저장 여부를 확인하지 못했습니다. 날짜별 기록을 조회한 뒤 다시 시도해 주세요.";
    else message = "API 연결 실패로 저장 여부를 확인하지 못했습니다. 연결을 확인하고 날짜별 기록을 조회해 주세요.";
    status("save-status", message, true);
  } finally {
    saving = false;
    element("save").disabled = false;
    element("save").textContent = "운동 기록 저장";
    element("create-fields").disabled = false;
  }
});
element("refresh").addEventListener("click", refresh);
refresh();
