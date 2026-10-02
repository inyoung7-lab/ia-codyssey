"use strict";

// UTC calendar days avoid timezone and daylight-saving shifts.
function workoutDay(date) { return Date.parse(`${date}T00:00:00Z`); }

function selectWorkoutRange(records, range) {
  const sorted = [...records].sort((a, b) => a.date.localeCompare(b.date));
  if (!sorted.length || range === "all") return sorted;
  const cutoff = workoutDay(sorted[sorted.length - 1].date) - (Number(range) - 1) * 86400000;
  return sorted.filter(record => workoutDay(record.date) >= cutoff);
}

function createWorkoutChart() {
  const canvas = document.getElementById("workout-chart");
  const range = document.getElementById("chart-range");
  const content = document.getElementById("chart-content");
  const message = document.getElementById("chart-status");
  const detail = document.getElementById("chart-detail");
  let records = [], visible = [], points = [], selected = -1;

  function draw() {
    if (content.hidden || !visible.length) return;
    const width = canvas.getBoundingClientRect().width;
    const height = canvas.getBoundingClientRect().height;
    if (!width || !height) return;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    const dark = document.documentElement.getAttribute("data-theme") === "dark";
    const ctx = canvas.getContext("2d");
    if (!ctx) { setState("이 브라우저에서는 그래프를 표시할 수 없습니다.", true); return; }
    ctx.scale(ratio, ratio);
    const left = 44, right = width - 16, top = 30, bottom = height - 46;
    const maximum = Math.max(10, Math.ceil(Math.max(...visible.map(r => r.value)) / 20) * 20);
    const first = workoutDay(visible[0].date), last = workoutDay(visible[visible.length - 1].date);
    points = visible.map(record => ({
      x: first === last ? (left + right) / 2 : left + (workoutDay(record.date) - first) / (last - first) * (right - left),
      y: bottom - record.value / maximum * (bottom - top), record,
    }));
    ctx.font = "12px system-ui";
    ctx.fillStyle = dark ? "#bdcec5" : "#5c6e65";
    ctx.fillText("운동시간(분)", left, 16);
    for (let i = 0; i <= 4; i++) {
      const y = bottom - i / 4 * (bottom - top);
      ctx.strokeStyle = dark ? "#455a50" : "#e1e9e3"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(left, y); ctx.lineTo(right, y); ctx.stroke();
      ctx.textAlign = "right"; ctx.fillText(String(maximum * i / 4), left - 8, y + 4);
    }
    const labels = Math.min(visible.length, width < 450 ? 3 : 5);
    for (let i = 0; i < labels; i++) {
      const index = labels === 1 ? 0 : Math.round(i * (points.length - 1) / (labels - 1));
      ctx.textAlign = i === 0 ? "left" : i === labels - 1 ? "right" : "center";
      ctx.fillText(points[index].record.date.slice(5), points[index].x, bottom + 20);
    }
    ctx.textAlign = "right"; ctx.fillText("날짜", right, height - 4);
    ctx.strokeStyle = dark ? "#83dbad" : "#196c49"; ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y));
    ctx.stroke();
    points.forEach((p, i) => {
      ctx.fillStyle = i === selected ? (dark ? "#ffc285" : "#b56220") : (dark ? "#83dbad" : "#196c49");
      ctx.beginPath(); ctx.arc(p.x, p.y, i === selected ? 5 : 2.5, 0, Math.PI * 2); ctx.fill();
    });
    ctx.textAlign = "left";
  }

  function render() {
    visible = selectWorkoutRange(records, range.value);
    selected = -1;
    content.hidden = !visible.length;
    message.textContent = visible.length ? "" : "표시할 운동 기록이 없습니다.";
    message.classList.toggle("error", false);
    if (!visible.length) return;
    const label = range.value === "all" ? "전체" : `최근 ${range.value}일`;
    document.getElementById("chart-period").textContent = `${label} · ${visible[0].date} ~ ${visible[visible.length - 1].date} · ${visible.length}개 기록`;
    detail.textContent = "그래프 위에 마우스를 올리거나 터치하면 날짜와 운동시간을 확인할 수 있습니다.";
    draw();
  }

  function setState(text, error = false) {
    records = []; visible = []; points = []; selected = -1;
    content.hidden = true;
    message.textContent = text;
    message.classList.toggle("error", error);
    range.disabled = true;
  }

  function highlight(index) {
    selected = index;
    detail.textContent = `${visible[index].date} · 운동시간 ${visible[index].value}분`;
    draw();
  }
  canvas.addEventListener("pointermove", event => {
    if (!points.length) return;
    const x = event.clientX - canvas.getBoundingClientRect().left;
    let nearest = 0;
    points.forEach((point, i) => { if (Math.abs(point.x - x) < Math.abs(points[nearest].x - x)) nearest = i; });
    highlight(nearest);
  });
  canvas.addEventListener("keydown", event => {
    if (!visible.length || !["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    highlight(Math.max(0, Math.min(visible.length - 1, selected + (event.key === "ArrowRight" ? 1 : -1))));
  });
  range.addEventListener("change", render);
  new ResizeObserver(draw).observe(canvas.parentElement);
  window.addEventListener("fitlog-theme-change", draw);
  return { setState, setRecords(data) { records = data; range.disabled = false; render(); } };
}
