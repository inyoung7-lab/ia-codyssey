"use strict";

let dataRecords = [], dataPage = 0, editingDataId = null;
let dataSaving = false, dataLoading = false, dataRefreshPromise = null;
const DATA_PAGE_SIZE = 10;

function dataControls() {
  const busy = dataSaving || dataLoading;
  element("data-fields").disabled = busy;
  element("csv-download").disabled = busy || !dataRecords.length;
  element("data-refresh").disabled = busy;
  element("data-prev").disabled = busy || dataPage === 0;
  element("data-next").disabled = busy || (dataPage + 1) * DATA_PAGE_SIZE >= dataRecords.length;
  element("data-rows").querySelectorAll("button").forEach(button => { button.disabled = busy; });
}

function resetDataForm() {
  editingDataId = null;
  element("data-form").reset();
  element("data-date").readOnly = false;
  element("data-form-title").textContent = "새 기록 추가";
  element("data-save").textContent = "기록 추가";
  element("data-cancel").hidden = true;
}

function editData(record) {
  if (dataSaving || dataLoading) return;
  editingDataId = record.id;
  element("data-date").value = record.date;
  element("data-date").readOnly = true;
  element("data-value").value = record.value;
  element("data-memo").value = record.memo;
  element("data-form-title").textContent = `${record.date} 기록 수정`;
  element("data-save").textContent = "수정 저장";
  element("data-cancel").hidden = false;
  status("data-save-status", "날짜는 유지하고 운동시간과 메모를 수정하세요.");
  element("data-value").focus();
}

function renderDataRows() {
  dataPage = Math.min(dataPage, Math.max(0, Math.ceil(dataRecords.length / DATA_PAGE_SIZE) - 1));
  element("data-rows").replaceChildren();
  element("data-table").hidden = !dataRecords.length;
  for (const record of dataRecords.slice(dataPage * DATA_PAGE_SIZE, (dataPage + 1) * DATA_PAGE_SIZE)) {
    const row = document.createElement("tr");
    for (const value of [record.date, number(record.value), record.memo]) {
      const cell = document.createElement("td"); cell.textContent = value; row.append(cell);
    }
    const actions = document.createElement("td"); actions.className = "row-actions";
    for (const [label, handler] of [["수정", () => editData(record)], ["삭제", () => deleteData(record)]]) {
      const button = document.createElement("button"); button.type = "button"; button.textContent = label;
      button.setAttribute("aria-label", `${record.date} 기록 ${label}`);
      button.addEventListener("click", handler); actions.append(button);
    }
    row.append(actions); element("data-rows").append(row);
  }
  element("data-page").textContent = dataRecords.length ? `${dataPage + 1} / ${Math.ceil(dataRecords.length / DATA_PAGE_SIZE)} · ${dataRecords.length}개` : "0개 기록";
  dataControls();
}

async function loadDataSummary() {
  element("data-summary").hidden = true;
  status("data-summary-status", "데이터 요약을 불러오는 중입니다.");
  try {
    const summary = await get("/api/data/summary");
    if (!summary.count) { status("data-summary-status", "저장된 기록이 없습니다. 첫 운동을 기록해보세요."); return; }
    element("data-period").textContent = `${summary.period.start} ~ ${summary.period.end}`;
    element("data-count").textContent = `${number(summary.count)}개`;
    element("data-total").textContent = `${number(summary.metrics.total)}분`;
    element("data-average").textContent = `${number(summary.metrics.average)}분`;
    element("data-extremes").textContent = `${number(summary.metrics.min)} / ${number(summary.metrics.max)}분`;
    const insight = summary.insights;
    element("insight-workout").textContent = `${number(insight.workout_days)}일`;
    element("insight-rest").textContent = `${number(insight.rest_days)}일`;
    element("insight-average").textContent = insight.workout_day_average === null ? "해당 없음" : `${number(insight.workout_day_average)}분`;
    element("insight-streak").textContent = `${number(insight.longest_workout_streak)}일`;
    const t = summary.trend, signed = value => `${value > 0 ? "+" : ""}${number(value)}`;
    element("data-trend").textContent = `최근 7일 ${number(t.recent_total)}분 · 이전 7일 ${number(t.previous_total)}분 · 변화 ${signed(t.absolute_change)}분 (${t.percent_change === null ? "이전 합계 0분으로 변화율 계산 불가" : signed(t.percent_change) + "%"}) · ${({increase:"증가", decrease:"감소", stable:"유지", no_data:"데이터 없음"})[t.direction] || "추세 확인 불가"}`;
    element("data-summary").hidden = false;
    status("data-summary-status", "");
  } catch {
    status("data-summary-status", "요약을 불러오지 못했습니다. 데이터 새로고침으로 다시 확인해 주세요.", true);
  }
}

async function loadDataRecords() {
  workoutChart.setState("그래프를 불러오는 중입니다.");
  status("data-list-status", "운동 기록을 불러오는 중입니다.");
  element("data-table").hidden = true;
  try {
    const records = await get("/api/data");
    if (!Array.isArray(records)) throw new Error("Invalid records");
    dataRecords = [...records].sort((a,b) => b.date.localeCompare(a.date));
    workoutChart.setRecords(records);
    renderDataRows();
    status("data-list-status", records.length ? "" : "아직 저장된 운동 기록이 없습니다.");
  } catch {
    dataRecords = []; renderDataRows();
    workoutChart.setState("그래프를 불러오지 못했습니다. 데이터 새로고침으로 다시 확인해 주세요.", true);
    status("data-list-status", "기록을 불러오지 못했습니다. API 연결을 확인해 주세요.", true);
  }
}

function refreshData() {
  if (dataRefreshPromise) return dataRefreshPromise;
  dataLoading = true; dataControls();
  dataRefreshPromise = Promise.all([loadDataSummary(), loadDataRecords()]).finally(() => {
    dataLoading = false; dataRefreshPromise = null; dataControls();
  });
  return dataRefreshPromise;
}

function dataError(error) {
  if (error.status === 409) return "해당 날짜의 운동 기록이 이미 있습니다.";
  if (error.status === 422) return "날짜, 운동시간(0~1440 정수), 메모(500자 이내)를 확인해 주세요.";
  if (error.status === 404) return "해당 기록이 없습니다. 데이터 새로고침으로 확인해 주세요.";
  return "요청 완료 여부를 확인하지 못했습니다. 연결을 확인하고 데이터를 새로고침한 뒤 다시 시도해 주세요.";
}

element("data-form").addEventListener("submit", async event => {
  event.preventDefault();
  if (dataSaving || dataLoading || !element("data-form").reportValidity()) return;
  const raw = element("data-value").value, value = Number(raw), memo = element("data-memo").value.trim();
  if (!raw.trim() || !Number.isInteger(value) || value < 0 || value > 1440 || memo.length > 500) {
    status("data-save-status", "운동시간과 메모 입력값을 확인해 주세요.", true); return;
  }
  const id = editingDataId;
  const body = {date: id || element("data-date").value, value, memo};
  dataSaving = true; dataControls(); element("data-save").textContent = "저장 중...";
  status("data-save-status", "운동 기록을 저장하고 있습니다.");
  try {
    await get(id ? `/api/data/${encodeURIComponent(id)}` : "/api/data", {method: id ? "PUT" : "POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)});
    resetDataForm(); status("data-save-status", "운동 기록이 저장되었습니다.");
    await refreshData();
  } catch (error) { status("data-save-status", dataError(error), true); }
  finally { dataSaving = false; element("data-save").textContent = editingDataId ? "수정 저장" : "기록 추가"; dataControls(); }
});

async function deleteData(record) {
  if (dataSaving || dataLoading || !window.confirm(`${record.date} 운동 기록을 삭제할까요? 이 작업은 되돌릴 수 없습니다.`)) return;
  dataSaving = true; dataControls(); status("data-save-status", "기록을 삭제하고 있습니다.");
  try {
    await get(`/api/data/${encodeURIComponent(record.id)}`, {method:"DELETE"});
    if (editingDataId === record.id) resetDataForm();
    status("data-save-status", "운동 기록이 삭제되었습니다."); await refreshData();
  } catch (error) { status("data-save-status", dataError(error), true); }
  finally { dataSaving = false; dataControls(); }
}

element("data-cancel").addEventListener("click", () => { if (!dataSaving) { resetDataForm(); status("data-save-status", "수정을 취소했습니다."); } });
element("data-prev").addEventListener("click", () => { if (!dataSaving && !dataLoading && dataPage > 0) { dataPage--; renderDataRows(); } });
element("data-next").addEventListener("click", () => { if (!dataSaving && !dataLoading && (dataPage+1)*DATA_PAGE_SIZE < dataRecords.length) { dataPage++; renderDataRows(); } });
element("data-refresh").addEventListener("click", () => { if (!dataSaving) return refreshData(); });
refreshData();
