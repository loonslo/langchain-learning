import { ApiError, chat, getAccessToken, health, saveAccessToken, submitFeedback } from "./api.js";
import "./style.css";

const state = {
  sessionId: `web-${Math.random().toString(36).slice(2, 8)}`,
  traceId: "",
  busy: false,
};

const $ = (selector) => document.querySelector(selector);
const messages = $("#messages");
const form = $("#chat-form");
const question = $("#question");
const sendButton = $("#send-button");
const accessToken = $("#access-token");

function scrollChat() {
  messages.scrollTop = messages.scrollHeight;
}

function showToast(text, kind = "") {
  const toast = $("#toast");
  toast.textContent = text;
  toast.className = `toast visible ${kind}`;
  window.setTimeout(() => { toast.className = "toast"; }, 2800);
}

function addMessage(role, text, options = {}) {
  const item = document.createElement("article");
  item.className = `message ${role}${options.loading ? " loading" : ""}`;
  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.textContent = role === "user" ? "ME" : "N";
  const body = document.createElement("div");
  body.className = "message-body";
  const meta = document.createElement("div");
  meta.className = "message-meta";
  meta.textContent = role === "user" ? "你 · 刚刚" : "Nova · 刚刚";
  const bubble = document.createElement("div");
  bubble.className = "message-bubble";
  if (options.loading) {
    bubble.innerHTML = '<span class="loading-dots"><i></i><i></i><i></i></span>';
  } else {
    bubble.textContent = text;
  }
  body.append(meta, bubble);
  if (options.sources?.length) {
    const sources = document.createElement("div");
    sources.className = "message-sources";
    options.sources.forEach((source) => {
      const chip = document.createElement("span");
      chip.className = "source-chip";
      chip.textContent = source;
      sources.appendChild(chip);
    });
    body.appendChild(sources);
  }
  if (options.ticketId) {
    const ticket = document.createElement("div");
    ticket.className = "ticket-chip";
    ticket.textContent = `已创建人工工单 · ${options.ticketId}`;
    body.appendChild(ticket);
  }
  item.append(avatar, body);
  messages.appendChild(item);
  scrollChat();
  return item;
}

function renderWelcome() {
  messages.replaceChildren();
  addMessage("assistant", "你好，我是 Nova 客服助手。\n\n我会先从 Day78 知识库检索证据，再回答退款、配送、发票等问题。右侧可以连接 JWT、填写订单号，并查看本次回答的来源。", {
    sources: ["customer_faq.md", "refund.md", "shipping.md"],
  });
}

function setBusy(busy) {
  state.busy = busy;
  sendButton.disabled = busy;
  question.disabled = busy;
  sendButton.querySelector("span").textContent = busy ? "处理中" : "发送";
}

function setConnectionStatus(online, label) {
  const pill = $("#connection-pill");
  pill.classList.toggle("offline", !online);
  pill.querySelector("span:last-child").textContent = label;
  $("#side-status-text").textContent = online ? "Day78 在线" : "后端未连接";
  $("#side-status-dot").classList.toggle("offline", !online);
}

function setTokenState(token = getAccessToken()) {
  const stateBox = $("#token-state");
  const connected = Boolean(token);
  stateBox.classList.toggle("connected", connected);
  stateBox.querySelector("span:last-child").textContent = connected ? "已保存身份 token" : "尚未连接身份";
  if (connected && !accessToken.value) accessToken.value = token;
}

function updateEvidence(data) {
  $("#evidence-empty").hidden = true;
  $("#evidence-content").hidden = false;
  const sources = $("#evidence-list");
  sources.replaceChildren();
  $("#evidence-message").textContent = data.sources?.length ? "回答已关联知识库证据" : "未返回知识库来源，可能已转人工";
  $("#answer-type").textContent = data.sources?.includes("order-system") ? "ORDER TOOL RESULT" : "KNOWLEDGE ANSWER";
  (data.sources || []).forEach((source) => {
    const item = document.createElement("div");
    item.className = "evidence-source";
    item.textContent = source;
    sources.appendChild(item);
  });
  const ticketRow = $("#ticket-row");
  ticketRow.hidden = !data.ticket_id;
  if (data.ticket_id) $("#ticket-id").textContent = data.ticket_id;
  $("#feedback-row").hidden = false;
}

function resetEvidence() {
  $("#evidence-empty").hidden = false;
  $("#evidence-content").hidden = true;
  $("#feedback-row").hidden = true;
}

async function sendQuestion() {
  if (state.busy) return;
  const value = question.value.trim();
  if (!value) return question.focus();
  if (!getAccessToken()) {
    showToast("请先在右侧连接 Day78 JWT", "warning");
    $("#connection-panel").scrollIntoView({ behavior: "smooth" });
    accessToken.focus();
    return;
  }

  question.value = "";
  question.style.height = "auto";
  addMessage("user", value);
  const loading = addMessage("assistant", "", { loading: true });
  setBusy(true);
  state.traceId = `${state.sessionId}-${Date.now()}`;
  try {
    const data = await chat({
      question: value,
      sessionId: state.sessionId,
      orderId: $("#order-id").value.trim(),
      idempotencyKey: state.traceId,
    });
    loading.remove();
    addMessage("assistant", data.answer || "暂时没有得到回答。", { sources: data.sources || [], ticketId: data.ticket_id });
    updateEvidence(data);
  } catch (error) {
    loading.remove();
    if (error instanceof ApiError && error.status === 401) {
      saveAccessToken("");
      setTokenState("");
      addMessage("assistant", "Day78 API 拒绝了当前身份 token。请重新生成 token，并在右侧连接设置中粘贴。 ");
      showToast("JWT 无效或已过期", "warning");
    } else {
      addMessage("assistant", error.message || "请求失败，请检查后端日志。");
      showToast(error.message || "请求失败", "error");
    }
    resetEvidence();
  } finally {
    setBusy(false);
    question.focus();
  }
}

async function checkBackend() {
  try {
    await health();
    setConnectionStatus(true, "Day78 在线");
  } catch (error) {
    setConnectionStatus(false, error instanceof ApiError ? error.message : "等待后端");
  }
}

async function saveToken() {
  const token = saveAccessToken(accessToken.value);
  setTokenState(token);
  if (!token) return showToast("请输入 JWT token", "warning");
  await checkBackend();
  showToast("身份 token 已保存", "success");
}

function newSession() {
  state.sessionId = `web-${Math.random().toString(36).slice(2, 8)}`;
  $("#session-id").textContent = state.sessionId;
  $("#order-id").value = "";
  resetEvidence();
  renderWelcome();
}

form.addEventListener("submit", (event) => { event.preventDefault(); sendQuestion(); });
question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendQuestion(); }
});
question.addEventListener("input", () => {
  question.style.height = "auto";
  question.style.height = `${Math.min(question.scrollHeight, 120)}px`;
});
$("#save-token").addEventListener("click", saveToken);
$("#clear-token").addEventListener("click", () => { saveAccessToken(""); accessToken.value = ""; setTokenState(""); showToast("身份 token 已清除"); });
$("#new-session").addEventListener("click", newSession);
$("#clear-order").addEventListener("click", () => { $("#order-id").value = ""; $("#order-id").focus(); });
document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => {
  question.value = button.dataset.prompt;
  question.dispatchEvent(new Event("input"));
  question.focus();
}));
document.querySelectorAll("[data-scroll]").forEach((button) => button.addEventListener("click", () => $("#" + button.dataset.scroll).scrollIntoView({ behavior: "smooth" })));
$("#feedback-row").addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-rating]");
  if (!button || !state.traceId) return;
  try {
    await submitFeedback({ traceId: state.traceId, rating: Number(button.dataset.rating), reason: button.dataset.rating === "1" ? "回答有帮助" : "需要人工复核" });
    $("#feedback-row").classList.add("submitted");
    showToast("反馈已进入 Day78 审查队列", "success");
  } catch (error) {
    showToast(error.message || "反馈提交失败", "error");
  }
});

$("#session-id").textContent = state.sessionId;
setTokenState();
renderWelcome();
checkBackend();
