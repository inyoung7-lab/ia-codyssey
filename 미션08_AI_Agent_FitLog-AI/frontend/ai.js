"use strict";

let analyzing = false;
element("analyze").addEventListener("click", async () => {
  if (analyzing) return;
  analyzing = true;
  element("analyze").disabled = true;
  element("analyze").textContent = "분석 중...";
  element("ai-result").hidden = true;
  status("ai-status", "운동 기록을 분석하고 있습니다. 잠시 기다려 주세요.");
  try {
    const data = await get("/workouts/ai-analysis", { cache: "no-store" }, 90000);
    const fields = [["ai-summary", "summary"], ["ai-strength", "strength"], ["ai-improvement", "improvement"], ["ai-next", "next_workout"]];
    if (!['ollama', 'rules'].includes(data.provider) || !data.period || !data.statistics || fields.some(([, key]) => typeof data.ai_feedback?.[key] !== "string")) {
      throw new Error("Invalid analysis response");
    }
    fields.forEach(([id, key]) => { element(id).textContent = data.ai_feedback[key]; });
    const stats = data.statistics;
    element("ai-statistics").textContent = `${data.period.start_date} ~ ${data.period.end_date} · 운동 ${stats.workout_days}일 · 휴식 ${stats.rest_days}일 · 총 ${number(stats.total_minutes)}분 · 기록일 평균 ${number(stats.average_minutes)}분`;
    element("ai-result").hidden = false;
    element("ai-provider").textContent = data.provider === 'ollama' ? '로컬 AI 분석' : '안전한 규칙 기반 분석';
    status("ai-status", "분석이 완료되었습니다.");
  } catch (error) {
    status("ai-status", error.detail || (error.name === "AbortError" ? "분석 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요." : "AI 분석을 불러오지 못했습니다. 연결 상태를 확인한 뒤 다시 시도해 주세요."), true);
  } finally {
    analyzing = false;
    element("analyze").disabled = false;
    element("analyze").textContent = "AI 분석하기";
  }
});
