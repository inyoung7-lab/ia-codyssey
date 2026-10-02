"use strict";

let currentConversationId = null, chatBusy = false, historyRequest = 0;

function chatControls() {
  for (const id of ["chat-send", "chat-input", "chat-new"]) element(id).disabled = chatBusy;
  element("history-list").querySelectorAll("button").forEach(button => { button.disabled = chatBusy; });
  element("chat-send").textContent = chatBusy ? "처리 중..." : "전송";
}

function addChatMessage(role, content, state = "") {
  const item = document.createElement("article"); item.className = `chat-message ${role}`;
  const label = document.createElement("h3"); label.textContent = role === "user" ? "나" : "AI 운동 비서";
  const text = document.createElement("p"); text.textContent = content;
  const note = document.createElement("small"); note.textContent = state;
  item.append(label, text, note); element("chat-messages").append(item);
  element("chat-empty").hidden = true;
  element("chat-messages").scrollTop = element("chat-messages").scrollHeight;
  return note;
}

async function loadConversations() {
  const request = ++historyRequest;
  element("history-refresh").disabled = true;
  status("history-status", "대화 목록을 불러오는 중입니다.");
  try {
    const rows = await get("/api/conversations");
    if (request !== historyRequest) return;
    element("history-list").replaceChildren();
    for (const row of rows) {
      const item = document.createElement("li"), button = document.createElement("button"), time = document.createElement("span");
      button.type = "button"; button.textContent = row.title;
      button.setAttribute("aria-pressed", String(row.id === currentConversationId));
      time.textContent = new Date(row.updated_at).toLocaleString("ko-KR");
      button.addEventListener("click", () => openConversation(row.id));
      item.append(button, time); element("history-list").append(item);
    }
    status("history-status", rows.length ? "" : "저장된 대화가 없습니다. 첫 질문을 보내보세요.");
    chatControls();
  } catch {
    if (request === historyRequest) status("history-status", "대화 목록을 불러오지 못했습니다. 목록 새로고침을 눌러 주세요.", true);
  } finally { if (request === historyRequest) element("history-refresh").disabled = false; }
}

async function openConversation(id) {
  if (chatBusy) return;
  chatBusy = true; chatControls(); status("chat-status", "대화를 불러오는 중입니다.");
  try {
    const data = await get(`/api/conversations/${encodeURIComponent(id)}`);
    if (data.id !== id || !Array.isArray(data.messages) || data.messages.some(m => !["user","assistant"].includes(m.role) || typeof m.content !== "string")) throw new Error("Invalid conversation");
    currentConversationId = data.id;
    element("chat-messages").replaceChildren(); element("chat-empty").hidden = !!data.messages.length;
    data.messages.forEach(m => addChatMessage(m.role, m.content));
    element("chat-input").value = ""; element("chat-context").textContent = "불러온 대화를 이어서 질문할 수 있습니다. 과거 답변은 당시 기록 기준입니다.";
    status("chat-status", "대화를 불러왔습니다.");
    await loadConversations();
  } catch (error) {
    status("chat-status", error.status === 404 ? "해당 대화가 없습니다. 목록을 새로고침해 주세요." : "대화를 불러오지 못했습니다. 연결을 확인해 주세요.", true);
  } finally { chatBusy = false; chatControls(); }
}

element("chat-new").addEventListener("click", () => {
  if (chatBusy) return;
  currentConversationId = null; element("chat-messages").replaceChildren();
  element("chat-empty").hidden = false; element("chat-input").value = ""; element("chat-context").textContent = "";
  element("history-list").querySelectorAll("button").forEach(button => button.setAttribute("aria-pressed", "false"));
  status("chat-status", "새 대화를 시작합니다. 이전 대화는 삭제되지 않습니다."); element("chat-input").focus();
});

function chatError(error) {
  if (error.status === 404) return "대화가 없습니다. 새 대화로 시작해 주세요.";
  if (error.status === 422) return "질문을 1~4000자로 입력해 주세요.";
  if (error.status === 409) return "대화 한도에 도달했습니다. 새 대화를 시작해 주세요.";
  if (error.status === 429) return "AI 사용 한도 또는 요청 빈도를 확인한 뒤 다시 시도해 주세요.";
  if (error.status === 503) return "서버 설정 또는 대화 저장 문제로 완료 여부를 확인하지 못했습니다. 이전 대화 목록을 확인한 뒤 다시 시도해 주세요.";
  if (error.status === 504 || error.name === "AbortError") return "AI 응답 시간이 초과되었습니다. 저장됐을 수 있으니 대화 목록을 먼저 확인해 주세요.";
  if (error.status) return "AI 답변을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.";
  return "서버 연결을 확인해 주세요. 요청이 저장됐을 수 있으니 이전 대화 목록을 먼저 확인해 주세요.";
}

element("chat-form").addEventListener("submit", async event => {
  event.preventDefault(); if (chatBusy) return;
  const message = element("chat-input").value.trim();
  if (!message || message.length > 4000) { status("chat-status", "질문을 1~4000자로 입력해 주세요.", true); return; }
  chatBusy = true; chatControls();
  const note = addChatMessage("user", message, "답변 대기 중");
  status("chat-status", "AI가 운동 기록을 분석하고 있습니다...");
  try {
    const result = await get("/api/chat", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message, conversation_id:currentConversationId})}, 120000);
    if (typeof result.answer !== "string" || !result.answer.trim() || !/^[0-9a-f]{32}$/.test(result.conversation_id) || result.provider !== "codyssey-openai-compatible" || result.model !== "gpt-5-mini" || !result.summary) throw new Error("Invalid chat response");
    currentConversationId = result.conversation_id; note.textContent = "저장됨";
    addChatMessage("assistant", result.answer); element("chat-input").value = "";
    const summary = result.summary;
    element("chat-context").textContent = summary.count ? `답변 기준: ${summary.period.start} ~ ${summary.period.end} · ${number(summary.count)}개 기록` : "저장된 운동 기록 없이 생성된 답변입니다.";
    status("chat-status", "답변과 대화가 저장되었습니다."); await loadConversations();
  } catch (error) {
    note.textContent = "저장 여부 미확인 · 질문은 입력창에 보관했습니다.";
    status("chat-status", chatError(error), true);
  } finally { chatBusy = false; chatControls(); }
});
element("history-refresh").addEventListener("click", loadConversations);
loadConversations();
