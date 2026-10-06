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
      appendTextCell(row, credential.provider_name);
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
  }

  async function refresh() {
    state = await request("/api/state");
    render();
  }

  async function deleteFolder(folder) {
    const count = Number(folder.credential_count) || 0;
    const accepted = window.confirm(
      `‘${folder.name}’ 폴더를 삭제할까요? 포함된 API 키 ${count}개도 함께 삭제됩니다. 이 작업은 되돌릴 수 없습니다.`,
    );
    if (!accepted) return;
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
    document.getElementById("edit-provider-id").value = credential.provider_id;
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
      provider_id: document.getElementById("provider-id").value,
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
    const providerId = document.getElementById("edit-provider-id").value;
    const alias = document.getElementById("edit-alias").value;
    const secretInput = document.getElementById("edit-api-key");
    const secret = secretInput.value;
    const payload = { provider_id: providerId, alias };
    if (secret) payload.api_key = secret;
    secretInput.value = "";
    try {
      await request(`/api/credentials/${encodeURIComponent(id)}`, {
        method: "PATCH", body: JSON.stringify(payload),
      });
      dialog.close();
      await refresh();
      showMessage("연결 API와 보관함 정보를 변경했습니다.", "success-text");
    } catch (error) {
      showMessage(error.message, "error-text");
    }
  });

  document.getElementById("cancel-edit").addEventListener("click", () => {
    document.getElementById("edit-api-key").value = "";
    dialog.close();
  });

  refresh().catch((error) => showMessage(error.message, "error-text"));
})();
