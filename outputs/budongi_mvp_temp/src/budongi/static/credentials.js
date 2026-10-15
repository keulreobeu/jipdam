"use strict";

(() => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
  const message = document.getElementById("message");
  const folderList = document.getElementById("folder-list");
  const credentialList = document.getElementById("credential-list");
  const folderSelect = document.getElementById("credential-folder");
  const keyInput = document.getElementById("api-key");
  const saveButton = document.getElementById("save-key");
  const dialog = document.getElementById("edit-dialog");
  let state = { folders: [], credentials: [], secure_storage_ready: false };
  const gmsSelect = document.getElementById("gms-credential");
  const gmsButton = document.getElementById("gms-check");
  const gmsResult = document.getElementById("gms-result");
  let gmsPending = false;
  let gmsRevision = 0;
  let gmsBudget = { policy: { enabled: false }, accounted_credits: 0, accounted_tokens: 0, held_credits: 0 };
  let gmsQuote = null;
  let quoteRevision = 0;
  const policyFields = {
    reserve_credits: "gms-reserve", max_total_credits: "gms-total-credits", max_total_tokens: "gms-total-tokens",
    max_input_tokens: "gms-max-input", max_output_tokens: "gms-max-output",
    expected_output_tokens: "gms-expected-output", max_call_credits: "gms-call-credits",
    max_count_credits: "gms-count-credits",
  };

  function clearQuote() {
    quoteRevision += 1;
    gmsQuote = null;
    document.getElementById("gms-execute").disabled = true;
    document.getElementById("gms-quote-result").textContent = "새 견적을 요청하세요.";
    document.getElementById("gms-work-result").textContent = "";
  }

  function renderPolicy() {
    const cumulative = gmsBudget.policy.budget_mode !== "reserve_only";
    document.getElementById("gms-budget-mode").value = gmsBudget.policy.budget_mode || "cumulative";
    for (const id of ["gms-total-credits", "gms-total-tokens", "gms-call-credits"]) {
      document.getElementById(id).disabled = !cumulative;
    }
    const workLimit = document.getElementById("gms-work-limit");
    const maxOutput = Number(gmsBudget.policy.max_output_tokens || 64);
    workLimit.max = String(maxOutput);
    workLimit.value = String(Math.min(Number(workLimit.value) || maxOutput, maxOutput));
    for (const [field, id] of Object.entries(policyFields)) {
      document.getElementById(id).value = gmsBudget.policy[field] ?? 0;
    }
    document.getElementById("gms-enabled").checked = Boolean(gmsBudget.policy.enabled);
    const ledgerLabel = cumulative ? "이 앱의 누적 사용·예약" : "사용 기록 · 누적 차단 기준 아님";
    document.getElementById("gms-ledger").textContent = `${ledgerLabel} ${gmsBudget.accounted_credits.toLocaleString("ko-KR")}크레딧 / ${gmsBudget.accounted_tokens.toLocaleString("ko-KR")}토큰 · 보류 ${gmsBudget.held_credits.toLocaleString("ko-KR")}크레딧`;
  }

  async function refreshBudget() {
    gmsBudget = await request("/api/gms/state");
    renderPolicy();
    renderGMS();
  }

  function showBalance(balance) {
    const output = document.getElementById("gms-balance-result");
    if (!balance) { output.textContent = "최신 잔액을 확인하지 못했습니다. 다시 조회하세요."; return; }
    output.textContent = `잔여 ${balance.remain_credit.toLocaleString("ko-KR")} · 사용 ${balance.used_credit.toLocaleString("ko-KR")} · 전체 ${balance.total_credit.toLocaleString("ko-KR")}크레딧 | 만료 ${new Date(balance.expired_date).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })} KST${balance.expired ? " (만료됨)" : ""} | 조회 ${new Date(balance.checked_at).toLocaleTimeString("ko-KR", { timeZone: "Asia/Seoul" })}`;
  }

  function clearGMSResult() {
    gmsRevision += 1;
    gmsResult.textContent = "아직 확인하지 않았습니다. 선택한 키로 연결을 확인하세요.";
    gmsResult.className = "message";
    document.getElementById("gms-balance-result").textContent = "잔액을 조회하지 않았습니다.";
    clearQuote();
  }

  function renderGMS() {
    const previous = gmsSelect.value;
    gmsSelect.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "GMS 키를 직접 선택하세요";
    gmsSelect.append(placeholder);
    for (const key of state.credentials) {
      const option = document.createElement("option");
      option.value = key.id;
      option.textContent = `${key.alias} · ${key.folder_name}`;
      gmsSelect.append(option);
    }
    const selected = previous || gmsBudget.policy.credential_id || "";
    gmsSelect.value = state.credentials.some((key) => key.id === selected) ? selected : "";
    gmsSelect.disabled = gmsPending || !state.secure_storage_ready;
    gmsButton.disabled = gmsPending || !state.secure_storage_ready || !gmsSelect.value ||
      !gmsBudget.policy.enabled || gmsSelect.value !== gmsBudget.policy.credential_id;
    document.getElementById("gms-balance").disabled = gmsPending || !state.secure_storage_ready || !gmsSelect.value;
    document.getElementById("gms-execute").disabled = gmsPending || !gmsQuote;
  }

  function showMessage(text, kind = "") {
    message.textContent = text;
    message.className = `message ${kind}`;
  }

  async function request(path, options = {}) {
    const headers = new Headers(options.headers || {});
    headers.set("Accept", "application/json");
    if (options.method && options.method !== "GET") {
      headers.set("Content-Type", "application/json");
      headers.set("X-Jipdam-CSRF", csrfToken);
    }
    let response;
    try {
      response = await fetch(path, {
        ...options, headers, credentials: "same-origin", cache: "no-store", redirect: "error",
      });
    } catch (_error) {
      throw new Error("로컬 보관함 서버에 연결할 수 없습니다.");
    }
    if (response.status === 204) return null;
    let result;
    try {
      result = await response.json();
    } catch (_error) {
      throw new Error("서버 응답을 확인할 수 없습니다.");
    }
    if (!response.ok) throw new Error(result.error || "요청을 처리할 수 없습니다.");
    return result;
  }

  function appendTextCell(row, value, className = "") {
    const cell = document.createElement("td");
    if (className) cell.className = className;
    cell.textContent = value;
    row.append(cell);
    return cell;
  }

  function renderFolders() {
    folderList.replaceChildren();
    folderSelect.replaceChildren();
    if (state.folders.length === 0) {
      const empty = document.createElement("li");
      empty.className = "folder-empty";
      empty.textContent = "아직 폴더가 없습니다.";
      folderList.append(empty);
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "폴더를 먼저 추가하세요";
      folderSelect.append(option);
      return;
    }
    for (const folder of state.folders) {
      const item = document.createElement("li");
      item.className = "folder-item";
      const name = document.createElement("span");
      name.className = "folder-name";
      name.textContent = folder.name;
      const count = document.createElement("span");
      count.className = "folder-count";
      count.textContent = `${folder.credential_count}개`;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "text-button danger-text";
      remove.textContent = "폴더와 키 삭제";
      remove.addEventListener("click", () => deleteFolder(folder));
      item.append(name, count, remove);
      folderList.append(item);

      const option = document.createElement("option");
      option.value = folder.id;
      option.textContent = folder.name;
      folderSelect.append(option);
    }
  }

  function renderCredentials() {
    credentialList.replaceChildren();
    document.getElementById("key-count").textContent = `${state.credentials.length}개`;
    document.getElementById("empty-state").hidden = state.credentials.length > 0;
    for (const credential of state.credentials) {
      const row = document.createElement("tr");
      appendTextCell(row, credential.alias, "alias-cell");
      appendTextCell(row, credential.folder_name);
      appendTextCell(row, credential.masked, "masked-cell");
      const actions = document.createElement("td");
      actions.className = "actions-cell";
      const edit = document.createElement("button");
      edit.type = "button";
      edit.className = "text-button";
      edit.textContent = "수정";
      edit.addEventListener("click", () => openEdit(credential));
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "text-button danger-text";
      remove.textContent = "삭제";
      remove.addEventListener("click", () => deleteCredential(credential));
      actions.append(edit, remove);
      row.append(actions);
      credentialList.append(row);
    }
  }

  function renderStorageStatus() {
    const badge = document.getElementById("secure-badge");
    const notice = document.getElementById("storage-notice");
    const ready = Boolean(state.secure_storage_ready);
    badge.textContent = ready ? "Windows 보안 저장소 사용 가능" : "안전한 저장소 확인 필요";
    badge.className = `badge ${ready ? "badge-ready" : "badge-error"}`;
    notice.hidden = ready;
    notice.textContent = state.secure_storage_message || "Windows 자격 증명 저장소를 사용할 수 없어 키 저장과 복호화가 중단됩니다.";
    keyInput.disabled = !ready;
    saveButton.disabled = !ready || state.folders.length === 0;
  }

  function render() {
    renderFolders();
    renderCredentials();
    renderStorageStatus();
    renderGMS();
  }

  async function refresh() {
    clearGMSResult();
    state = await request("/api/state");
    await refreshBudget();
    render();
  }

  async function deleteFolder(folder) {
    const count = Number(folder.credential_count) || 0;
    const accepted = window.confirm(
      `‘${folder.name}’ 폴더를 삭제할까요? 포함된 API 키 ${count}개도 함께 삭제됩니다. 이 작업은 되돌릴 수 없습니다.`,
    );
    if (!accepted) return;
    clearGMSResult();
    try {
      await request(`/api/folders/${encodeURIComponent(folder.id)}`, {
        method: "DELETE", body: JSON.stringify({
          confirm: true,
          credential_ids: state.credentials.filter((key) => key.folder_id === folder.id).map((key) => key.id),
        }),
      });
      await refresh();
      showMessage("폴더와 포함된 키를 삭제했습니다.", "success-text");
    } catch (error) {
      showMessage(error.message, "error-text");
      // A different tab may have changed the folder since the confirmation.
      await refresh().catch(() => {});
    }
  }

  async function deleteCredential(credential) {
    if (!window.confirm(`‘${credential.alias}’ API 키를 삭제할까요?`)) return;
    clearGMSResult();
    try {
      await request(`/api/credentials/${encodeURIComponent(credential.id)}`, { method: "DELETE", body: "{}" });
      await refresh();
      showMessage("API 키를 삭제했습니다.", "success-text");
    } catch (error) {
      showMessage(error.message, "error-text");
    }
  }

  function openEdit(credential) {
    document.getElementById("edit-id").value = credential.id;
    const editFolder = document.getElementById("edit-folder");
    editFolder.replaceChildren();
    for (const folder of state.folders) {
      const option = document.createElement("option");
      option.value = folder.id;
      option.textContent = folder.name;
      editFolder.append(option);
    }
    editFolder.value = credential.folder_id;
    document.getElementById("edit-alias").value = credential.alias;
    document.getElementById("edit-api-key").value = "";
    dialog.showModal();
    document.getElementById("edit-alias").focus();
  }

  dialog.addEventListener("close", () => {
    document.getElementById("edit-api-key").value = "";
  });

  document.getElementById("folder-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("folder-name");
    const name = input.value;
    input.value = "";
    try {
      await request("/api/folders", { method: "POST", body: JSON.stringify({ name }) });
      await refresh();
      showMessage("폴더를 추가했습니다.", "success-text");
    } catch (error) {
      showMessage(error.message, "error-text");
    }
  });

  document.getElementById("credential-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const secret = keyInput.value;
    const payload = {
      folder_id: folderSelect.value,
      alias: document.getElementById("credential-alias").value,
      api_key: secret,
    };
    keyInput.value = "";
    try {
      await request("/api/credentials", { method: "POST", body: JSON.stringify(payload) });
      document.getElementById("credential-alias").value = "";
      await refresh();
      showMessage("API 키를 암호화해 저장했습니다. 외부 API는 호출하지 않았습니다.", "success-text");
    } catch (error) {
      showMessage(error.message, "error-text");
    }
  });

  document.getElementById("edit-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = document.getElementById("edit-id").value;
    const folderId = document.getElementById("edit-folder").value;
    const alias = document.getElementById("edit-alias").value;
    const secretInput = document.getElementById("edit-api-key");
    const secret = secretInput.value;
    const payload = { folder_id: folderId, alias };
    if (secret) payload.api_key = secret;
    secretInput.value = "";
    clearGMSResult();
    try {
      await request(`/api/credentials/${encodeURIComponent(id)}`, {
        method: "PATCH", body: JSON.stringify(payload),
      });
      dialog.close();
      await refresh();
      showMessage("별칭·폴더와 보관함 정보를 변경했습니다.", "success-text");
    } catch (error) {
      showMessage(error.message, "error-text");
    }
  });

  document.getElementById("cancel-edit").addEventListener("click", () => {
    document.getElementById("edit-api-key").value = "";
    dialog.close();
  });

  gmsSelect.addEventListener("change", () => {
    clearGMSResult();
    renderGMS();
  });

  document.getElementById("gms-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (gmsPending || !gmsSelect.value) return;
    const credentialId = gmsSelect.value;
    const revision = gmsRevision;
    gmsPending = true;
    renderGMS();
    gmsResult.textContent = "GMS 연결 확인 중… 시험 요청은 자동 재시도하지 않습니다.";
    try {
      const result = await request("/api/gms/check", {
        method: "POST", body: JSON.stringify({ credential_id: credentialId, confirm: true }),
      });
      if (revision !== gmsRevision) return;
      let details = "";
      if (result.usage && result.estimated_credits !== null) {
        details = ` 입력 ${result.usage.input_tokens} / 출력 ${result.usage.output_tokens}토큰 · 예상 ${result.estimated_credits.toLocaleString("ko-KR")}크레딧 사용.`;
      } else {
        details = " 사용량·비용은 확인되지 않았습니다.";
      }
      gmsResult.textContent = result.message + details;
      gmsResult.className = `message ${result.status === "available" ? "success-text" : "error-text"}`;
      showBalance(result.balance);
      await refreshBudget();
    } catch (error) {
      if (revision === gmsRevision) {
        gmsResult.textContent = error.message;
        gmsResult.className = "message error-text";
      }
    } finally {
      gmsPending = false;
      renderGMS();
    }
  });

  document.getElementById("gms-balance").addEventListener("click", async () => {
    if (gmsPending || !gmsSelect.value) return;
    const revision = gmsRevision;
    const credentialId = gmsSelect.value;
    gmsPending = true;
    renderGMS();
    try {
      const result = await request("/api/gms/balance", { method: "POST", body: JSON.stringify({ credential_id: credentialId }) });
      if (revision === gmsRevision) showBalance(result);
    } catch (error) {
      if (revision === gmsRevision) document.getElementById("gms-balance-result").textContent = error.message;
    } finally {
      gmsPending = false;
      renderGMS();
    }
  });

  document.getElementById("gms-policy-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (gmsPending || !gmsSelect.value) return;
    const values = { credential_id: gmsSelect.value, enabled: document.getElementById("gms-enabled").checked,
      budget_mode: document.getElementById("gms-budget-mode").value };
    for (const [field, id] of Object.entries(policyFields)) values[field] = Number(document.getElementById(id).value);
    clearQuote();
    try {
      gmsBudget = await request("/api/gms/policy", { method: "POST", body: JSON.stringify(values) });
      renderPolicy();
      renderGMS();
      document.getElementById("gms-policy-result").textContent = "한도를 저장했습니다. 누적 사용량은 유지됩니다. 모델 생성은 하지 않았습니다.";
    } catch (error) {
      document.getElementById("gms-policy-result").textContent = error.message;
    }
  });

  document.getElementById("gms-work-form").addEventListener("input", clearQuote);
  document.getElementById("gms-policy-form").addEventListener("input", clearQuote);
  document.getElementById("gms-work-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (gmsPending) return;
    if (gmsSelect.value !== gmsBudget.policy.credential_id) {
      showMessage("작업에 사용할 키를 선택하고 그 키의 한도를 먼저 저장하세요.", "error-text"); return;
    }
    clearQuote();
    const revision = quoteRevision;
    gmsPending = true;
    renderGMS();
    document.getElementById("gms-quote-result").textContent = "실잔액과 전체 입력 토큰을 확인하는 중…";
    try {
      const quote = await request("/api/gms/quote", {
        method: "POST", body: JSON.stringify({task_id: document.getElementById("gms-task-id").value,
          objective: document.getElementById("gms-objective").value, context: document.getElementById("gms-context").value,
          difficulty: document.getElementById("gms-difficulty").value,
          max_output_tokens: Number(document.getElementById("gms-work-limit").value)}),
      });
      if (revision !== quoteRevision) return;
      gmsQuote = quote;
      document.getElementById("gms-quote-result").textContent = `${quote.model} · 입력/출력 ${quote.input_rate}/${quote.output_rate}크레딧/토큰 | 입력 ${quote.input_tokens} · 예상 출력 ${quote.expected_output_tokens} · 최대 출력 ${quote.max_output_tokens}토큰 | 카운트 조회 ${quote.count_credits}크레딧 | 조회 포함 예상 ${quote.estimated_credits} · 최대 ${quote.maximum_credits}크레딧 (생성 예약 ${quote.generation_maximum_credits}) | 120초 유효`;
      showBalance(quote.balance);
      await refreshBudget();
    } catch (error) {
      if (revision === quoteRevision) document.getElementById("gms-quote-result").textContent = error.message;
    } finally {
      gmsPending = false;
      renderGMS();
    }
  });

  document.getElementById("gms-execute").addEventListener("click", async () => {
    if (gmsPending || !gmsQuote) return;
    const quote = gmsQuote;
    const revision = quoteRevision;
    gmsQuote = null;
    gmsPending = true;
    renderGMS();
    try {
      const result = await request("/api/gms/execute", { method: "POST", body: JSON.stringify({quote_id: quote.quote_id, confirm: true}) });
      if (revision === quoteRevision) {
        document.getElementById("gms-work-result").textContent = result.text || result.message;
        document.getElementById("gms-quote-result").textContent = `${result.message} ${result.usage ? `실사용 입력 ${result.usage.input_tokens} / 출력 ${result.usage.output_tokens}토큰 · ${result.estimated_credits}크레딧` : "사용량 미확인 · 최대 비용 보류"}`;
        showBalance(result.balance);
      }
      await refreshBudget();
    } catch (error) {
      document.getElementById("gms-work-result").textContent = error.message;
    } finally {
      gmsPending = false;
      renderGMS();
    }
  });

  refresh().catch((error) => showMessage(error.message, "error-text"));
})();
