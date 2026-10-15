(() => {
  const csrf = document.querySelector('meta[name="jipdam-csrf"]').content;
  const chatLog = document.getElementById("chatLog");
  const chatForm = document.getElementById("chatForm");
  const searchForm = document.getElementById("searchForm");
  const searchMessage = document.getElementById("searchMessage");
  const resultSection = document.getElementById("results");
  const dataState = document.getElementById("dataState");
  const candidateList = document.getElementById("candidateList");
  const conditionSummary = document.getElementById("conditionSummary");
  const detailsPage = document.getElementById("detailsPage");
  const needsPage = document.getElementById("needsPage");
  const detail = document.getElementById("candidateDetail");
  const detailEmpty = document.getElementById("detailEmpty");
  let sessionId = null;
  let latestRequest = null;
  let results = [], selectedId = null, servingVersion = null, map = null, tileFailed = false;
  let chatGeneration = 0, searchGeneration = 0, detailGeneration = 0;
  const markers = new Map(), revisions = new Map();
  const explicitDraftFields = new Set();
  let previousMonthly = searchForm.elements.namedItem('max_monthly_rent_krw').value;
  searchForm.addEventListener('input', (event) => {
    const key = event.target.name === 'condition' || event.target.dataset.kind ? 'conditions' : event.target.name;
    revisions.set(key, (revisions.get(key) || 0) + 1);
  });
  function syncType() {
    const monthly = searchForm.elements.namedItem('max_monthly_rent_krw');
    const jeonse = searchForm.elements.namedItem('rental_type').value === 'jeonse';
    if (jeonse && !monthly.disabled) { previousMonthly = monthly.value; monthly.value = '0'; }
    if (!jeonse && monthly.disabled) monthly.value = previousMonthly;
    monthly.disabled = jeonse;
  }
  searchForm.elements.namedItem('rental_type').addEventListener('change', syncType);
  function draftFromForm(forChat = false) {
    const body = new FormData(searchForm);
    const draft = {rental_type: body.get('rental_type'), districts: body.getAll('districts'), conditions: []};
    for (const key of ['max_deposit_krw','max_monthly_rent_krw','area_min_sqm','area_max_sqm']) {
      const value = body.get(key);
      if (value !== null && value !== '') draft[key] = Number(value);
    }
    if (draft.rental_type === 'jeonse') draft.max_monthly_rent_krw = 0;
    for (const kind of body.getAll('condition')) draft.conditions.push({kind,
      max_distance_m: Number(searchForm.querySelector(`.condition-distance[data-kind="${kind}"]`).value),
      required: searchForm.querySelector(`.condition-priority[data-kind="${kind}"]`).value === 'true'});
    if (forChat) {
      for (const key of Object.keys(draft)) {
        if (!revisions.has(key) && !explicitDraftFields.has(key)) delete draft[key];
      }
    }
    return draft;
  }
  function clearDetail() {
    detailGeneration += 1; results = []; selectedId = null; servingVersion = null;
    detail.replaceChildren(); detail.classList.add('hidden'); detailEmpty.classList.remove('hidden');
    detailEmpty.textContent = '후보를 선택하면 저장된 상세 정보를 확인할 수 있습니다.';
    document.getElementById('viewMap').disabled = true;
    document.getElementById('mapStatus').textContent = '검수 좌표가 있는 후보를 선택해 주세요.';
    if (map) { map.remove(); map = null; }
    tileFailed = false; markers.clear(); document.getElementById('rentalMap').classList.add('hidden'); setTab('needs');
  }
  document.getElementById('newChat').addEventListener('click', async () => {
    chatGeneration += 1; const old = sessionId; sessionId = null;
    chatLog.replaceChildren(); addBubble('새 대화입니다. 직접 입력한 조건은 유지됩니다.', 'assistant');
    if (old) await api('/api/chat', {session_id: old, reset: true}).catch(() => {});
  });
  const fieldLabels = {
    contract_date: "계약일", kind: "전월세 유형", deposit_krw: "보증금 (원)",
    monthly_rent_krw: "월세 (원)", area_sqm: "전용 면적 (㎡)", floor: "층",
    build_year: "건축 연도", source_id: "출처 ID", dataset_id: "데이터셋 ID",
    batch_id: "배치 ID", snapshot_date: "기준일", mapping_version: "정규화 버전",
    source_file_ref: "원본 파일", source_content_sha256: "원본 SHA-256",
    source_row_number: "원본 행", legal_dong: "법정동", jibun: "지번", sgg_cd: "자치구 코드"
  };

  const districtCodes = {
      "11110": "종로구", "11140": "중구", "11170": "용산구", "11200": "성동구", "11215": "광진구",
      "11230": "동대문구", "11260": "중랑구", "11290": "성북구", "11305": "강북구", "11320": "도봉구",
      "11350": "노원구", "11380": "은평구", "11410": "서대문구", "11440": "마포구", "11470": "양천구",
      "11500": "강서구", "11530": "구로구", "11545": "금천구", "11560": "영등포구", "11590": "동작구",
      "11620": "관악구", "11650": "서초구", "11680": "강남구", "11710": "송파구", "11740": "강동구"
    };

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[char]);
  }

  async function api(path, body) {
    const response = await fetch(path, {
      method: body ? "POST" : "GET",
      headers: body ? {"Content-Type": "application/json", "X-Jipdam-CSRF": csrf} : {},
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store"
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) { const error = new Error(result.error || '요청을 처리하지 못했습니다.'); error.status = response.status; throw error; }
    return result;
  }

  function addBubble(text, role) {
    const bubble = document.createElement("div");
    bubble.className = `bubble ${role}`;
    bubble.textContent = text;
    chatLog.appendChild(bubble);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const input = document.getElementById("chatMessage");
    const message = input.value.trim();
    if (!message) return;
    const generation = chatGeneration, before = new Map(revisions);
    input.value = "";
    addBubble(message, "user");
    const button = chatForm.querySelector("button");
    button.disabled = true;
    try {
      const result = await api("/api/chat", {session_id: sessionId, message, draft: draftFromForm(true)});
      if (generation !== chatGeneration) return;
      sessionId = result.session_id;
      addBubble(result.reply, "assistant");
      const patch = {...(result.draft_patch || {})};
      for (const key of Object.keys(patch)) if ((before.get(key) || 0) !== (revisions.get(key) || 0)) delete patch[key];
      applyDraft(patch);
      document.getElementById('modelState').textContent = result.mode === 'local_llm' ? '로컬 모델이 조건 초안을 정리했습니다.' : '모델 응답을 이용할 수 없어 직접 입력으로 이어갑니다.';
      if (Object.keys(result.draft || {}).length) {
        searchMessage.textContent = "대화에서 확인한 조건을 검색 초안에 반영했습니다. 내용을 확인하고 수정한 뒤 검색해 주세요.";
      }
    } catch (error) {
      if (generation === chatGeneration) addBubble(`${error.message} 입력은 보존했으며 아래에서 직접 조건을 입력할 수 있습니다.`, "assistant");
    } finally {
      button.disabled = false;
      input.focus();
    }
  });

  searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const generation = ++searchGeneration; clearDetail(); candidateList.replaceChildren();
    resultSection.classList.remove('hidden'); dataState.classList.add('hidden'); conditionSummary.replaceChildren();
    searchMessage.textContent = "DB를 조회하고 있습니다…";
    const form = new FormData(searchForm);
    const request = {
      rental_type: form.get("rental_type"),
      max_deposit_krw: Number(form.get("max_deposit_krw")),
      max_monthly_rent_krw: form.get("rental_type") === "jeonse" ? 0 : Number(form.get("max_monthly_rent_krw")),
      districts: form.getAll("districts"), limit: 5, conditions: []
    };
    if (!request.districts.length) delete request.districts;
    for (const key of ['max_deposit_krw','max_monthly_rent_krw']) {
      if (!Number.isSafeInteger(request[key]) || request[key] < 0) { searchMessage.textContent = '예산은 정확하게 표현할 수 있는 0 이상의 원 정수로 입력해 주세요.'; return; }
    }
    for (const key of ["area_min_sqm", "area_max_sqm"]) {
      const value = form.get(key);
      if (value) request[key] = Number(value);
    }
    for (const kind of form.getAll("condition")) {
      const distance = Number(searchForm.querySelector(`.condition-distance[data-kind="${kind}"]`).value);
      const required = searchForm.querySelector(`.condition-priority[data-kind="${kind}"]`).value === "true";
      request.conditions.push({kind, max_distance_m: distance, required});
    }
    if (request.conditions.some((condition) => condition.kind === "workplace")) {
      const latitude = form.get("workplace_latitude");
      const longitude = form.get("workplace_longitude");
      if (!latitude || !longitude || !form.get("workplace_verified")) {
        searchMessage.textContent = "직장 거리 조건은 직접 확인한 좌표와 확인 표시가 필요합니다.";
        return;
      }
      request.workplace = {
        latitude: Number(latitude), longitude: Number(longitude), verified: true,
        source: "user_confirmed_coordinate", source_ref: "local-user-input"
      };
    }
    latestRequest = request;
    for (const key of Object.keys(request)) explicitDraftFields.add(key);
    try {
      const result = await api("/api/recommendations", {request});
      if (generation !== searchGeneration) return;
      showResults(result);
      searchMessage.textContent = "";
    } catch (error) {
      if (generation === searchGeneration) {
        searchMessage.textContent = error.status === 503 ? `DB 연결 오류: ${error.message}` : error.message;
      }
    }
  });

  function showResults(result) {
    results = result.results || []; servingVersion = result.serving_version;
    resultSection.classList.remove("hidden");
    document.getElementById("resultCount").textContent = `${result.count ?? 0}곳`;
    candidateList.replaceChildren();
    dataState.classList.toggle("hidden", result.status === "ok");
    dataState.classList.toggle("warning", result.status === "data_not_ready");
    if (result.status === "data_not_ready") {
      const linked = result.confirmed_complex_observations ?? 0;
      const total = result.observations ?? 0;
      dataState.textContent = `${result.reason || "실제 추천 데이터가 준비되지 않았습니다."} 전월세 원본 ${total.toLocaleString("ko-KR")}건 중 확정 단지 연결 ${linked.toLocaleString("ko-KR")}건입니다. 미확정 후보를 추천에 사용하지 않습니다.`;
    } else if (result.status === "no_match") {
      dataState.textContent = result.reason || "입력 조건을 만족하는 후보가 없습니다.";
    }
    const conditions = result.conditions || (latestRequest?.conditions || []).map((condition) => ({
      kind: condition.kind, status: "unknown", reason: "현재 DB에 검수된 좌표·시설 범위가 없습니다."
    }));
    conditionSummary.replaceChildren();
    conditionSummary.classList.toggle("hidden", conditions.length === 0);
    const conditionNames = {workplace: "직장", station: "지하철역", supermarket: "마트", park: "공원", hospital: "병원"};
    for (const condition of conditions) {
      const chip = document.createElement("span");
      chip.className = `condition-chip ${condition.status === "unknown" ? "unknown" : ""}`;
      chip.textContent = `${conditionNames[condition.kind] || condition.kind}: ${condition.status === "met" ? "충족" : condition.status === "unmet" ? "미충족" : "미확인"}`;
      chip.title = condition.reason || "";
      conditionSummary.appendChild(chip);
    }
    for (const item of result.results || []) {
      const card = document.createElement("article");
      card.className = "candidate-card";
      card.innerHTML = `<div><h3>${escapeHtml(item.name)}</h3><div class="candidate-meta">${escapeHtml(item.legal_dong || "")} · ${escapeHtml(item.contract_date)} 계약 · ${escapeHtml(item.area_sqm)}㎡</div><div class="candidate-price">보증금 ${Number(item.deposit_krw).toLocaleString("ko-KR")}원 · 월세 ${Number(item.monthly_rent_krw).toLocaleString("ko-KR")}원</div></div><button class="detail-button" type="button" data-id="${escapeHtml(item.complex_id)}">전체 정보 보기 →</button>`;
      card.dataset.id = item.complex_id;
      const comparison = document.createElement('div'); comparison.className = 'table-scroll';
      comparison.innerHTML = `<table class="needs-table"><thead><tr><th>조건</th><th>상태</th><th>실제 값</th><th>요청 기준</th><th>판정 근거</th></tr></thead><tbody>${(item.needs || []).map(needRow).join('')}</tbody></table>`;
      card.appendChild(comparison); candidateList.appendChild(card);
    }
    candidateList.querySelectorAll("button[data-id]").forEach((button) => {
      button.addEventListener("click", () => loadDetail(button.dataset.id));
    });
    if (result.status === "data_not_ready" && requestNeedsDistance(latestRequest)) {
      dataState.textContent += " 지하철·마트·공원·병원 거리 자료와 검수 좌표도 현재 DB에 없습니다.";
    }
    const notice = document.createElement('p'); notice.className = 'source-note'; notice.textContent = (result.notices || []).join(' '); candidateList.appendChild(notice);
    resultSection.scrollIntoView({behavior: "smooth", block: "start"});
  }

  function requestNeedsDistance(request) {
    return Boolean(request?.conditions?.length);
  }

  function applyDraft(draft) {
    for (const key of Object.keys(draft)) explicitDraftFields.add(key);
    const type = searchForm.elements.namedItem("rental_type");
    if (["jeonse", "wolse"].includes(draft.rental_type)) { type.value = draft.rental_type; syncType(); }
    for (const key of ["max_deposit_krw", "max_monthly_rent_krw", "area_min_sqm", "area_max_sqm"]) {
      const input = searchForm.elements.namedItem(key);
      if (key === 'max_monthly_rent_krw' && type.value === 'jeonse') continue;
      if (input && key in draft) { if (draft[key] === null) input.value = ''; else if (Number.isFinite(draft[key])) input.value = String(draft[key]); }
    }
    const districtNames = Object.fromEntries(
      [...searchForm.elements.namedItem("districts").options].map((option) => [option.value, option.value])
    );

    if (Array.isArray(draft.districts)) {
      const selected = new Set(draft.districts.map((value) => districtNames[value] || districtCodes[value]).filter(Boolean));
      for (const option of searchForm.elements.namedItem("districts").options) option.selected = selected.has(option.value);
    }
    if (Array.isArray(draft.conditions)) {
      const byKind = new Map(draft.conditions.map((condition) => [condition.kind, condition]));
      for (const checkbox of searchForm.querySelectorAll('input[name="condition"]')) {
        const condition = byKind.get(checkbox.value);
        checkbox.checked = Boolean(condition);
        if (!condition) continue;
        searchForm.querySelector(`.condition-priority[data-kind="${checkbox.value}"]`).value = String(condition.required);
        searchForm.querySelector(`.condition-distance[data-kind="${checkbox.value}"]`).value = String(condition.max_distance_m);
      }
    }
  }

  async function loadDetail(complexId, offset = 0) {
    const generation = ++detailGeneration; selectedId = complexId;
    for (const card of candidateList.querySelectorAll('.candidate-card')) card.classList.toggle('selected', card.dataset.id === complexId);
    detail.dataset.complexId = complexId;
    setTab("details");
    detail.classList.add("hidden");
    detailEmpty.classList.remove("hidden");
    detailEmpty.textContent = "DB 상세 정보를 불러오고 있습니다…";
    try {
      const result = await api(`/api/candidates/${encodeURIComponent(complexId)}/${offset}`);
      if (generation !== detailGeneration) return;
      if (servingVersion && result.serving_version !== servingVersion) throw new Error('DB 버전이 바뀌었습니다. 다시 검색해 주세요.');
      if (result.status !== "ok") throw new Error(result.reason || "이 후보의 검수된 상세 정보가 없습니다.");
      renderDetail(result); selectMap(complexId);
    } catch (error) {
      if (generation === detailGeneration) detailEmpty.textContent = error.message;
    }
  }

  function renderDetail(result) {
    const candidate = result.complex;
    const coords = candidate.coordinates;
    document.getElementById('mapStatus').textContent = coords ? `${candidate.name} · 검수 좌표 ${coords.latitude}, ${coords.longitude}` : `${candidate.name}의 검수 좌표가 없어 위치를 제공하지 않습니다.`;
    if (tileFailed) document.getElementById('mapStatus').textContent += ' 배경 지도 연결에 실패했습니다. 좌표와 후보는 유지됩니다.';
    document.getElementById('viewMap').disabled = !results.some((item) => item.coordinates);
    const fields = result.fields || [];
    const facilityNames = {station:'지하철역',supermarket:'마트',park:'공원',hospital:'병원'};
    const facilityRows = (result.facilities || []).map((item) => `<tr><td>${escapeHtml(facilityNames[item.category] || item.category)}</td><td>${escapeHtml(item.name)}</td><td>${escapeHtml(item.distance_m)}m 직선거리</td><td>${escapeHtml(item.source_date)}</td><td>${escapeHtml(item.source.source_id)}</td></tr>`).join('');
    const facilityTable = facilityRows ? `<details><summary>주변 검수 시설 ${(result.facilities || []).length}곳</summary><div class="table-scroll"><table class="needs-table"><thead><tr><th>종류</th><th>시설</th><th>거리</th><th>기준일</th><th>출처</th></tr></thead><tbody>${facilityRows}</tbody></table></div></details>` : '<p class="source-note">관련 검수 시설 자료가 없습니다.</p>';

    const table = `<div class="table-scroll"><table class="observation-table"><thead><tr>${fields.map((field) => `<th title="${escapeHtml(`${field.type} · ${field.unit} · ${field.section} · ${field.validity}`)}">${escapeHtml(field.label || fieldLabels[field.key] || field.key)}</th>`).join("")}</tr></thead><tbody>${(result.observations || []).map((observation) => `<tr>${fields.map((field) => `<td>${escapeHtml(formatValue(field.key, observation[field.key] ?? "—"))}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
    const more = result.next_offset !== null && result.next_offset !== undefined
      ? `<button class="detail-button more-button" type="button" data-next="${result.next_offset}">이전 거래 더 보기 →</button>` : "";
    detail.innerHTML = `<header class="detail-head"><h3>${escapeHtml(candidate.name)}</h3><p>${escapeHtml(candidate.legal_dong || "")} ${escapeHtml(candidate.jibun || "")} · 기준일 ${escapeHtml(result.snapshot_date)} · 단지 ID ${escapeHtml(candidate.complex_id)}</p></header><div class="observation-heading"><strong>저장된 전월세 관측 ${Number(result.total_observations).toLocaleString("ko-KR")}건</strong><span>${Number(result.offset) + 1}–${Number(result.offset) + result.observations.length}건 표시</span></div>${table}${more}${result.previous_offset !== null && result.previous_offset !== undefined ? `<button type="button" class="detail-button previous-button" data-previous="${result.previous_offset}">더 최근 거래</button>` : ''}${proof('단지·좌표 검수 근거', candidate)}${facilityTable}${proof('시설 계보', result.facilities)}${proof('시설 커버리지·기준일', result.coverage)}${proof('거래 연결 검수 근거', result.reviewed_relations)}${proof('미지원 원본 항목', result.unsupported_fields)}<p class="source-note">상세 표는 DB에 저장된 정규화 필드와 출처 계보를 표시합니다. 원문 payload 전체는 브라우저로 보내지 않습니다.</p>`;
    const previousButton = detail.querySelector('.previous-button');
    if (previousButton) previousButton.addEventListener('click', () => loadDetail(candidate.complex_id, Number(previousButton.dataset.previous)));
    const moreButton = detail.querySelector(".more-button");
    if (moreButton) moreButton.addEventListener("click", () => loadDetail(detail.dataset.complexId, Number(moreButton.dataset.next)));
    detailEmpty.classList.add("hidden");
    detail.classList.remove("hidden");
  }

  function formatValue(key, value) {
    if (value === "—" || value === "") return "—";
    if (["deposit_krw", "monthly_rent_krw"].includes(key)) return `${Number(value).toLocaleString("ko-KR")}원`;
    if (key === "area_sqm") return `${value}㎡`;
    if (key === "kind") return value === "jeonse" ? "전세" : "월세";
    return value;
  }

  function setTab(name) {
    const needs = name === "needs";
    needsPage.classList.toggle("hidden", !needs);
    detailsPage.classList.toggle("hidden", needs);
    document.getElementById("needsTab").classList.toggle("active", needs);
    document.getElementById("detailsTab").classList.toggle("active", !needs);
    if (!needs && map) map.invalidateSize();
    document.getElementById('needsTab').tabIndex = needs ? 0 : -1;
    document.getElementById('detailsTab').tabIndex = needs ? -1 : 0;
    document.getElementById("needsTab").setAttribute("aria-selected", String(needs));
    document.getElementById("detailsTab").setAttribute("aria-selected", String(!needs));
  }
  document.getElementById("needsTab").addEventListener("click", () => setTab("needs"));
  document.getElementById("detailsTab").addEventListener("click", () => setTab("details"));


  function proof(label, rows) { return `<details><summary>${escapeHtml(label)}</summary><pre>${escapeHtml(JSON.stringify(rows || {}, null, 2))}</pre></details>`; }
  function needRow(need) {
    const states = {met:'충족',unmet:'미충족',unknown:'미확인'};
    const actual = need.actual ?? (need.distance_m !== null && need.distance_m !== undefined ? `${need.distance_m}m 직선거리` : '미확인');
    const expected = need.expected ?? `${need.required ? '필수' : '선호'} · ${need.max_distance_m}m 이내`;
    const text = (value) => {
      if (need.kind === 'rental_type') return value === 'jeonse' ? '전세' : '월세';
      if (need.kind === 'district') return Array.isArray(value) ? value.map((code) => districtCodes[code] || code).join(', ') : districtCodes[value] || value;
      if (need.kind === 'budget' && typeof value === 'object') {
        return `보증금 ${Number(value.deposit_krw ?? value.max_deposit_krw).toLocaleString('ko-KR')}원 · 월세 ${Number(value.monthly_rent_krw ?? value.max_monthly_rent_krw).toLocaleString('ko-KR')}원`;
      }
      if (need.kind === 'area') return typeof value === 'object' ? `${value.area_min_sqm ?? '제한 없음'} ~ ${value.area_max_sqm ?? '제한 없음'}㎡` : `${value}㎡`;
      return typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value);
    };
    const label = need.label || {workplace:'직장',station:'지하철역',supermarket:'마트',park:'공원',hospital:'병원'}[need.kind] || need.kind;
    return `<tr><th>${escapeHtml(label)}</th><td class="need-${escapeHtml(need.status)}">${states[need.status]}</td><td>${escapeHtml(text(actual))}</td><td>${escapeHtml(text(expected))}</td><td>${escapeHtml(need.reason)} ${escapeHtml(need.facility?.name || '')}${proof('출처', need.facility?.source || need.coverage_source || need.source)}</td></tr>`;
  }
  function selectMap(id) { if (map && markers.has(id)) { const marker = markers.get(id); map.panTo(marker.getLatLng(), {animate:false}); marker.openPopup(); } }
  document.getElementById('viewMap').addEventListener('click', () => {
    if (map) { map.invalidateSize(); selectMap(selectedId); return; }
    const located = results.filter((item) => item.coordinates);
    if (!located.length) return;
    if (!window.L) { document.getElementById('mapStatus').textContent += ' 지도 라이브러리를 불러오지 못했습니다. 좌표는 유지됩니다.'; return; }
    document.getElementById('rentalMap').classList.remove('hidden'); map = L.map('rentalMap');
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom:19,
      referrerPolicy:'strict-origin-when-cross-origin', attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors'});
    tiles.on('tileerror', () => { tileFailed = true; document.getElementById('mapStatus').textContent = '배경 지도 연결에 실패했습니다. 검수 좌표와 후보 정보는 유지됩니다.'; }); tiles.addTo(map);
    for (const item of located) {
      const marker = L.marker([item.coordinates.latitude,item.coordinates.longitude], {title:item.name, alt:item.name}).addTo(map);
      const name = document.createElement('span'); name.textContent = item.name; marker.bindPopup(name);
      marker.on('click', () => loadDetail(item.complex_id)); markers.set(item.complex_id,marker);
    }
    map.fitBounds(L.latLngBounds(located.map((item) => [item.coordinates.latitude,item.coordinates.longitude])), {maxZoom:16}); selectMap(selectedId);
  });
  for (const name of ['needs','details']) document.getElementById(`${name}Tab`).addEventListener('keydown', (event) => {
    if (['ArrowLeft','ArrowRight'].includes(event.key)) { event.preventDefault(); const next = name === 'needs' ? 'details' : 'needs'; setTab(next); document.getElementById(`${next}Tab`).focus(); }
  });
  syncType();

  api("/api/status").then((status) => {
    const badge = document.getElementById("dataBadge");
    document.getElementById('modelState').textContent = status.model_configured ? '로컬 모델의 조건 정리를 사용할 수 있습니다.' : '로컬 모델이 설정되지 않았습니다. 조건을 직접 입력할 수 있습니다.';
    if (status.quality_status === 'synthetic_only') { badge.textContent = '합성 검증 데이터'; }
    else if (status.status === "ready") {
      badge.textContent = `실제 DB · 기준 ${status.snapshot_date}`;
      badge.classList.add("ready");
    } else {
      badge.textContent = "실제 추천 데이터 준비 중";
    }
  }).catch(() => {
    document.getElementById("dataBadge").textContent = "실제 DB 연결 필요";
  });
})();
