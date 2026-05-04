const state = {
  accessToken: localStorage.getItem("access_token") || "",
  refreshToken: localStorage.getItem("refresh_token") || "",
  profile: null,
};

const $ = (id) => document.getElementById(id);

let toastTimer = null;

function showMessage(text, type = "info") {
  const box = $("global-message");
  if (!box) return;

  if (toastTimer) {
    clearTimeout(toastTimer);
    toastTimer = null;
  }

  box.textContent = text;
  box.className = `toast ${type}`;
  box.style.display = "block";

  toastTimer = setTimeout(() => {
    box.style.display = "none";
  }, 3500);
}

function updateAuthStatus() {
  const status = $("auth-status");
  const isAuth = !!state.accessToken;
  status.textContent = isAuth ? "Авторизован" : "Не авторизован";
  status.className = `status-badge ${isAuth ? "status-on" : "status-off"}`;
}

function saveTokens(access, refresh) {
  state.accessToken = access || "";
  state.refreshToken = refresh || state.refreshToken || "";
  localStorage.setItem("access_token", state.accessToken);
  localStorage.setItem("refresh_token", state.refreshToken);
  updateAuthStatus();
}

function clearTokens() {
  state.accessToken = "";
  state.refreshToken = "";
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  updateAuthStatus();
}

async function refreshAccessToken() {
  if (!state.refreshToken) {
    clearTokens();
    throw new Error("Refresh token отсутствует");
  }

  const response = await fetch("/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: state.refreshToken }),
  });

  if (!response.ok) {
    clearTokens();
    throw new Error("Не удалось обновить токен");
  }

  const data = await response.json();
  saveTokens(data.access_token, data.refresh_token || state.refreshToken);
  return state.accessToken;
}

async function apiFetch(url, options = {}, retry = true) {
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  if (state.accessToken) {
    headers["Authorization"] = `Bearer ${state.accessToken}`;
  }

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401 && retry && state.refreshToken) {
    try {
      await refreshAccessToken();
      return apiFetch(url, options, false);
    } catch (e) {
      clearTokens();
      throw e;
    }
  }

  return response;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

function estimateCheckTime(file) {
  if (!file) return "5–15 сек";

  const sizeKB = file.size / 1024;

  if (sizeKB <= 300) return "5–10 сек";
  if (sizeKB <= 1024) return "10–20 сек";
  if (sizeKB <= 3072) return "20–40 сек";
  return "40–90 сек";
}

function showCheckLoading(fileName, estimatedTime) {
  const box = $("check-loading");
  const title = $("check-loading-title");
  const text = $("check-loading-text");

  if (!box || !title || !text) return;

  title.textContent = "Идёт проверка файла...";
  text.textContent = `Файл: ${fileName}. Ориентировочное время: ${estimatedTime}`;
  box.hidden = false;
}

function hideCheckLoading() {
  const box = $("check-loading");
  if (box) {
    box.hidden = true;
  }
}

function activateSection(sectionId) {
  document.querySelectorAll(".section").forEach((el) => el.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach((el) => el.classList.remove("active"));

  const targetSection = document.getElementById(sectionId);
  if (targetSection) targetSection.classList.add("active");

  const targetBtn = document.querySelector(`.nav-btn[data-section="${sectionId}"]`);
  if (targetBtn) targetBtn.classList.add("active");

  // Специальная обработка для РИО секции
  if (sectionId === "rio-section") {
    setTimeout(() => {
      if (typeof loadRioUserInfo === "function") loadRioUserInfo();
      if (typeof resetRioSession === "function") resetRioSession();
      if (typeof resetAndGoToStep1 === "function") resetAndGoToStep1();
    }, 100);
  }
}

async function handleLogin(event) {
  event.preventDefault();

  const payload = {
    email: $("login-email").value.trim(),
    password: $("login-password").value,
  };

  const response = await fetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Ошибка входа", "error");
    return;
  }

  saveTokens(data.access_token, data.refresh_token);
  showMessage("Вход выполнен успешно", "success");
  await loadProfile();
  activateSection("profile-section");
}

async function handleRegister(event) {
  event.preventDefault();

  let facultyCode = $("register-faculty-code").value.trim();

  if (!validateFacultyCode(facultyCode)) {
    showMessage("Код факультета должен быть в формате 00.00.00 (например, 09.03.04)", "error");
    return;
  }

  const payload = {
    fio: $("register-fio").value.trim(),
    email: $("register-email").value.trim(),
    password: $("register-password").value,
    faculty_code: facultyCode,
    department_name: $("register-department-name").value.trim(),
    role: $("register-role").value,
  };

  const response = await fetch("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Ошибка регистрации", "error");
    return;
  }

  showMessage("Регистрация успешна. Теперь выполните вход.", "success");
  event.target.reset();
}

async function loadProfile() {
  if (!state.accessToken) {
    $("profile-card").innerHTML = "Профиль пока не загружен";
    return;
  }

  const response = await apiFetch("/auth/me");
  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Не удалось загрузить профиль", "error");
    return;
  }

  state.profile = data;

  $("profile-card").innerHTML = `
    <div class="profile-item"><div class="label">ФИО</div><div class="value">${data.fio}</div></div>
    <div class="profile-item"><div class="label">Email</div><div class="value">${data.email}</div></div>
    <div class="profile-item"><div class="label">Роль</div><div class="value">${data.role}</div></div>
    <div class="profile-item"><div class="label">Факультет</div><div class="value">${data.faculty_name}</div></div>
    <div class="profile-item"><div class="label">Кафедра</div><div class="value">${data.department_name}</div></div>
    <div class="profile-item"><div class="label">Создан</div><div class="value">${new Date(data.created_at).toLocaleString()}</div></div>
  `;
}

async function handleCheck(event) {
  event.preventDefault();

  if (!state.accessToken) {
    showMessage("Сначала войдите в систему", "error");
    return;
  }

  const form = event.target;
  const submitBtn = form.querySelector('button[type="submit"]');
  const fileInput = $("manual-file");

  if (!fileInput || !fileInput.files.length) {
    showMessage("Выберите файл", "error");
    return;
  }

  const file = fileInput.files[0];
  const estimatedTime = estimateCheckTime(file);

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Проверяется...";
  }

  fileInput.disabled = true;

  showCheckLoading(file.name, estimatedTime);
  $("check-result").innerHTML = `
    <div class="stat-card">
      <h3>Проверка запущена</h3>
      <p>Идёт анализ документа. Пожалуйста, подождите.</p>
    </div>
  `;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await apiFetch("/checker/check", {
      method: "POST",
      body: formData,
      headers: {},
    });

    const rawData = await parseResponse(response);
    const data = typeof rawData === "object" && rawData !== null ? rawData : {};

    if (!response.ok) {
      showMessage(data.detail || data.text || "Ошибка проверки файла", "error");
      return;
    }

    const reportBtn = data.pdf_report_url
      ? `<a class="link-btn report" href="${data.pdf_report_url}" target="_blank">Открыть PDF-отчёт</a>`
      : "";

    $("check-result").innerHTML = `
      <div class="stat-card">
        <h3>Результат проверки</h3>
        <p><strong>Статус:</strong> ${data.has_errors ? "Найдены замечания" : "Ошибок не найдено"}</p>
        <p><strong>Ошибки:</strong> ${data.errors_count ?? 0}</p>
        <div class="actions-row">
          <a class="link-btn" href="${data.checked_file_url}" target="_blank">Скачать проверенный файл</a>
          ${reportBtn}
        </div>
      </div>
    `;

    if (data.pdf_report_url) {
      window.open(data.pdf_report_url, "_blank");
    }

    await loadManuals();
    showMessage(data.message || "Проверка завершена", "success");
  } catch (error) {
    $("check-result").innerHTML = `
      <div class="stat-card">
        <h3>Ошибка проверки</h3>
        <p>Во время обработки файла произошла ошибка.</p>
      </div>
    `;
    showMessage("Произошла ошибка во время проверки", "error");
  } finally {
    hideCheckLoading();

    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Проверить методичку";
    }

    fileInput.disabled = false;
  }
}

async function loadManuals() {
  if (!state.accessToken) {
    $("manuals-list").innerHTML = "Нужно войти в систему";
    return;
  }

  const response = await apiFetch("/checker/my");
  const data = await parseResponse(response);

  if (!response.ok) {
    $("manuals-list").innerHTML = "Не удалось загрузить список методичек";
    return;
  }

  if (!Array.isArray(data) || !data.length) {
    $("manuals-list").innerHTML = "Список пока пуст";
    return;
  }

  $("manuals-list").innerHTML = data.map(item => `
    <div class="manual-item">
      <div>
        <div><strong>${item.manual_name || item.file_name || "Методичка"}</strong></div>
        <div class="manual-meta">
          ${item.fio_user ? `Автор: ${item.fio_user}<br>` : ""}
          ${item.created_at ? `Добавлена: ${new Date(item.created_at).toLocaleString()}` : ""}
        </div>
      </div>
      <div class="manual-meta">
        Факультет: ${item.faculty_code ?? "-"}<br>
        Кафедра: ${item.department_name ?? "-"}
      </div>
    </div>
  `).join("");
}

async function handleFacultyStat(event) {
  event.preventDefault();

  let code = $("stat-faculty-code").value.trim();

  if (!validateFacultyCode(code)) {
    showMessage("Код факультета должен быть в формате 00.00.00 (например, 09.03.04)", "error");
    return;
  }

  const from = $("stat-faculty-from").value;
  const to = $("stat-faculty-to").value;

  const response = await apiFetch(
    `/statistics/faculty?faculty_code=${encodeURIComponent(code)}&date_from=${from}&date_to=${to}`
  );
  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Ошибка статистики", "error");
    return;
  }

  $("statistics-result").innerHTML = `
    <div class="stat-card">
      <h3>Результат</h3>
      <p><strong>Факультет:</strong> ${data.value}</p>
      <p><strong>Период:</strong> ${data.date_from} — ${data.date_to}</p>
      <p><strong>Количество методичек:</strong> ${data.manual_count}</p>
    </div>
  `;
}

async function handleDepartmentStat(event) {
  event.preventDefault();

  const departmentName = $("stat-department-name").value.trim();
  const from = $("stat-department-from").value;
  const to = $("stat-department-to").value;

  const response = await apiFetch(
    `/statistics/department?department_name=${encodeURIComponent(departmentName)}&date_from=${from}&date_to=${to}`
  );
  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Ошибка статистики", "error");
    return;
  }

  $("statistics-result").innerHTML = `
    <div class="stat-card">
      <h3>Результат</h3>
      <p><strong>Кафедра:</strong> ${data.value}</p>
      <p><strong>Период:</strong> ${data.date_from} — ${data.date_to}</p>
      <p><strong>Количество методичек:</strong> ${data.manual_count}</p>
    </div>
  `;
}

async function handleUserStat(event) {
  event.preventDefault();
  const fio = encodeURIComponent($("stat-user-fio").value.trim());
  const from = $("stat-user-from").value;
  const to = $("stat-user-to").value;

  const response = await apiFetch(`/statistics/user?fio_user=${fio}&date_from=${from}&date_to=${to}`);
  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Ошибка статистики", "error");
    return;
  }

  $("statistics-result").innerHTML = `
    <div class="stat-card">
      <h3>Результат</h3>
      <p><strong>Пользователь:</strong> ${data.value}</p>
      <p><strong>Период:</strong> ${data.date_from} — ${data.date_to}</p>
      <p><strong>Количество методичек:</strong> ${data.manual_count}</p>
    </div>
  `;
}

async function handleCreateFaculty(event) {
  event.preventDefault();

  let facultyCode = $("faculty-code").value.trim();

  if (!validateFacultyCode(facultyCode)) {
    showMessage("Код факультета должен быть в формате 00.00.00 (например, 09.03.04)", "error");
    return;
  }

  const payload = {
    faculty_name: $("faculty-name").value.trim(),
    faculty_code: facultyCode,
    dean_fio: $("dean-fio").value.trim(),
  };

  const response = await apiFetch("/admin/faculty", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Не удалось создать факультет", "error");
    return;
  }

  showMessage("Факультет создан", "success");
  event.target.reset();
}

async function handleCreateDepartment(event) {
  event.preventDefault();

  let facultyCode = $("department-faculty-code").value.trim();

  if (!validateFacultyCode(facultyCode)) {
    showMessage("Код факультета должен быть в формате 00.00.00 (например, 09.03.04)", "error");
    return;
  }

  const payload = {
    department_name: $("department-name").value.trim(),
    faculty_code: facultyCode,
  };

  const response = await apiFetch("/admin/department", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    showMessage(data.detail || "Не удалось создать кафедру", "error");
    return;
  }

  showMessage("Кафедра создана", "success");
  event.target.reset();
}

function setRequiredForBlock(block, isRequired) {
  if (!block) return;

  const fields = block.querySelectorAll("input, select, textarea");
  fields.forEach((field) => {
    if (isRequired) {
      if (field.dataset.wasRequired === "true") {
        field.required = true;
      }
    } else {
      if (field.required) {
        field.dataset.wasRequired = "true";
      }
      field.required = false;
    }
  });
}

function toggleTitleForms() {
  const type = $("title-doc-type")?.value;
  const manualBlock = $("manual-title-block");
  const tutorialBlock = $("tutorial-title-block");
  const monographBlock = $("monograph-title-block");

  const isManual = type === "manual";
  const isTutorial = type === "tutorial";
  const isMonograph = type === "monograph";

  if (manualBlock) manualBlock.style.display = isManual ? "block" : "none";
  if (tutorialBlock) tutorialBlock.style.display = isTutorial ? "block" : "none";
  if (monographBlock) monographBlock.style.display = isMonograph ? "block" : "none";

  setRequiredForBlock(manualBlock, isManual);
  setRequiredForBlock(tutorialBlock, isTutorial);
  setRequiredForBlock(monographBlock, isMonograph);
}

function bindTextareaCounter(textareaId, counterId, maxLength) {
  const textarea = $(textareaId);
  const counter = $(counterId);

  if (!textarea || !counter) return;

  const updateCounter = () => {
    const length = textarea.value.length;
    counter.textContent = `${length} / ${maxLength}`;
  };

  textarea.addEventListener("input", updateCounter);
  updateCounter();
}

function initTextareaCounters() {
  bindTextareaCounter("title-description", "title-description-counter", 1000);
  bindTextareaCounter("tutorial-description", "tutorial-description-counter", 500);
  bindTextareaCounter("monograph-description", "monograph-description-counter", 1000);
}

function addTutorialReviewer() {
  const container = $("tutorial-reviewers-container");
  if (!container) return;

  const block = document.createElement("div");
  block.className = "tutorial-reviewer-item";
  block.innerHTML = `
    <label>Ученая степень, должность рецензента</label>
    <input type="text" class="tutorial-reviewer-degree" />

    <label>ФИО рецензента</label>
    <input type="text" class="tutorial-reviewer-fio" />
  `;
  container.appendChild(block);
}

function addTutorialDirection() {
  const container = $("tutorial-directions-container");
  if (!container) return;

  const block = document.createElement("div");
  block.className = "tutorial-direction-item";
  block.innerHTML = `
    <label>Код направления</label>
    <input type="text" class="tutorial-direction-code" />

    <label>Название факультета / группы</label>
    <input type="text" class="tutorial-direction-name" />
  `;
  container.appendChild(block);
}

function addMonographAuthor() {
  const container = document.getElementById("monograph-authors-container");
  if (!container) return;

  const block = document.createElement("div");
  block.className = "monograph-author-item";
  block.innerHTML = `
    <label>ФИО автора</label>
    <input type="text" class="monograph-author-fio" />
    <button type="button" class="remove-author-btn secondary-btn" style="margin-top: 5px; margin-bottom: 10px;" onclick="this.parentElement.remove()">Удалить</button>
  `;
  container.appendChild(block);
}

async function handleTutorialTitlePageGenerate() {
  const reviewers = [...document.querySelectorAll(".tutorial-reviewer-item")]
    .map(item => ({
      degree_position: item.querySelector(".tutorial-reviewer-degree")?.value.trim(),
      fio: item.querySelector(".tutorial-reviewer-fio")?.value.trim(),
    }))
    .filter(item => item.degree_position && item.fio);

  const directions = [...document.querySelectorAll(".tutorial-direction-item")]
    .map(item => ({
      code: item.querySelector(".tutorial-direction-code")?.value.trim(),
      faculty_name: item.querySelector(".tutorial-direction-name")?.value.trim(),
    }))
    .filter(item => item.code && item.faculty_name);

  const payload = {
    author_name: $("tutorial-author-name")?.value.trim(),
    tutorial_title: $("tutorial-title")?.value.trim(),
    city: $("tutorial-city")?.value.trim(),
    year: Number($("tutorial-year")?.value),
    reviewers,
    a_value: $("tutorial-a-value")?.value.trim(),
    isbn: $("tutorial-isbn")?.value.trim(),
    directions,
    udk: $("tutorial-udk")?.value.trim(),
    bbk: $("tutorial-bbk")?.value.trim(),
    description: $("tutorial-description")?.value.trim(),
  };

  if (
    !payload.author_name ||
    !payload.tutorial_title ||
    !payload.city ||
    !payload.year ||
    !payload.a_value ||
    !payload.isbn ||
    !payload.udk ||
    !payload.bbk ||
    !payload.description ||
    !payload.reviewers.length ||
    !payload.directions.length
  ) {
    showMessage("Заполните все поля учебного пособия", "error");
    return;
  }

  if (payload.description.length > 500) {
    showMessage("Описание учебного пособия не должно превышать 500 символов", "error");
    return;
  }

  const response = await apiFetch("/title-page/generate-tutorial", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await parseResponse(response);

    if (Array.isArray(data.detail)) {
      const text = data.detail
        .map(err => `${err.loc.join(" → ")}: ${err.msg}`)
        .join("; ");
      showMessage(text, "error");
    } else {
      showMessage(data.detail || "Ошибка генерации учебного пособия", "error");
    }
    return;
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  let fileName = "tutorial_title_page.docx";
  const disposition = response.headers.get("content-disposition");
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) fileName = match[1];
  }

  $("title-page-result").innerHTML = `
    <div class="stat-card">
      <h3>Титульный лист учебного пособия создан</h3>
      <div class="actions-row">
        <a class="link-btn" href="${url}" download="${fileName}">Скачать файл</a>
      </div>
    </div>
  `;

  showMessage("Учебное пособие сгенерировано", "success");
}

async function handleMonographTitlePageGenerate() {
  const authors = [...document.querySelectorAll(".monograph-author-item")]
    .map(item => ({
      fio: item.querySelector(".monograph-author-fio")?.value.trim(),
    }))
    .filter(item => item.fio);

  const payload = {
    authors: authors,
    monograph_title: document.getElementById("monograph-title")?.value.trim(),
    city: document.getElementById("monograph-city")?.value.trim(),
    year: Number(document.getElementById("monograph-year")?.value),
    udk: document.getElementById("monograph-udk")?.value.trim(),
    bbk: document.getElementById("monograph-bbk")?.value.trim(),
    isbn: document.getElementById("monograph-isbn")?.value.trim(),
    description: document.getElementById("monograph-description")?.value.trim(),
  };

  // Валидация
  if (!payload.monograph_title || !payload.city || !payload.year ||
      !payload.udk || !payload.bbk || !payload.isbn || !payload.description ||
      payload.authors.length === 0) {
    showMessage("Заполните все поля монографии и добавьте хотя бы одного автора", "error");
    return;
  }

  if (payload.description.length > 1000) {
    showMessage("Описание монографии не должно превышать 1000 символов", "error");
    return;
  }

  const response = await apiFetch("/title-page/generate-monograph", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await parseResponse(response);
    showMessage(data.detail || "Ошибка генерации монографии", "error");
    return;
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  let fileName = "monograph_title_page.docx";
  const disposition = response.headers.get("content-disposition");
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) fileName = match[1];
  }

  document.getElementById("title-page-result").innerHTML = `
    <div class="stat-card">
      <h3>Титульный лист монографии создан</h3>
      <div class="actions-row">
        <a class="link-btn" href="${url}" download="${fileName}">Скачать файл</a>
      </div>
    </div>
  `;

  showMessage("Монография сгенерирована", "success");
}

function validateFacultyCode(code) {
  const regex = /^\d{2}\.\d{2}\.\d{2}$/;
  return regex.test(code);
}

async function handleTitlePageGenerate(event) {
  event.preventDefault();

  if (!state.accessToken) {
    showMessage("Сначала войдите в систему", "error");
    activateSection("auth-section");
    return;
  }

  const docType = $("title-doc-type")?.value;

  if (docType === "tutorial") {
    await handleTutorialTitlePageGenerate();
    return;
  }

  if (docType === "monograph") {
    await handleMonographTitlePageGenerate();
    return;
  }

  const payload = {
    manual_title: $("title-manual-title")?.value.trim(),
    discipline_name: $("title-discipline-name")?.value.trim(),
    audience: $("title-audience")?.value,
    direction_code: $("title-direction-code")?.value.trim(),
    direction_name: $("title-direction-name")?.value.trim(),
    city: $("title-city")?.value.trim(),
    year: Number($("title-year")?.value),
    udk: $("title-udk")?.value.trim(),
    compiler_name: $("title-compiler")?.value.trim(),
    reviewer_name: $("title-reviewer")?.value.trim(),
    reviewer_degree: $("title-reviewer-degree")?.value.trim(),
    description: $("title-description")?.value.trim(),
  };

  if (
    !payload.manual_title ||
    !payload.discipline_name ||
    !payload.audience ||
    !payload.direction_code ||
    !payload.direction_name ||
    !payload.city ||
    !payload.year ||
    !payload.udk ||
    !payload.compiler_name ||
    !payload.reviewer_name ||
    !payload.reviewer_degree ||
    !payload.description
  ) {
    showMessage("Заполните все поля титульного листа", "error");
    return;
  }

  if (payload.description.length > 1000) {
    showMessage("Описание не должно превышать 1000 символов", "error");
    return;
  }

  const response = await apiFetch("/title-page/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await parseResponse(response);

    if (Array.isArray(data.detail)) {
      const text = data.detail
        .map(err => `${err.loc.join(" → ")}: ${err.msg}`)
        .join("; ");
      showMessage(text, "error");
    } else {
      showMessage(data.detail || "Не удалось сгенерировать титульный лист", "error");
    }
    return;
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);

  let fileName = "title_page.docx";
  const disposition = response.headers.get("content-disposition");
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/);
    if (match && match[1]) {
      fileName = match[1];
    }
  }

  $("title-page-result").innerHTML = `
    <div class="stat-card">
      <h3>Титульный лист успешно создан</h3>
      <p>Файл готов к скачиванию.</p>
      <div class="actions-row">
        <a class="link-btn" href="${url}" download="${fileName}">Скачать титульный лист</a>
      </div>
    </div>
  `;

  showMessage("Титульный лист сгенерирован", "success");
}

async function logout() {
  if (state.refreshToken) {
    try {
      await apiFetch("/auth/logout", {
        method: "POST",
        body: JSON.stringify({ refresh_token: state.refreshToken }),
      });
    } catch (_) {}
  }

  clearTokens();
  state.profile = null;
  $("profile-card").innerHTML = "Профиль пока не загружен";
  $("manuals-list").innerHTML = "Список пока пуст";
  $("check-result").innerHTML = "Здесь появится результат проверки";
  showMessage("Вы вышли из системы", "info");
  activateSection("auth-section");
}

function initNavigation() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => activateSection(btn.dataset.section));
  });
}

function initEvents() {
  $("login-form")?.addEventListener("submit", handleLogin);
  $("register-form")?.addEventListener("submit", handleRegister);
  $("check-form")?.addEventListener("submit", handleCheck);
  $("title-page-form")?.addEventListener("submit", handleTitlePageGenerate);
  $("faculty-stat-form")?.addEventListener("submit", handleFacultyStat);
  $("department-stat-form")?.addEventListener("submit", handleDepartmentStat);
  $("user-stat-form")?.addEventListener("submit", handleUserStat);
  $("faculty-form")?.addEventListener("submit", handleCreateFaculty);
  $("department-form")?.addEventListener("submit", handleCreateDepartment);
  $("logout-btn")?.addEventListener("click", logout);
  $("load-profile-btn")?.addEventListener("click", loadProfile);
  $("load-manuals-btn")?.addEventListener("click", loadManuals);

  $("title-doc-type")?.addEventListener("change", toggleTitleForms);
  $("add-reviewer-btn")?.addEventListener("click", addTutorialReviewer);
  $("add-direction-btn")?.addEventListener("click", addTutorialDirection);
  $("add-monograph-author-btn")?.addEventListener("click", addMonographAuthor);
}

// ========== РИО ОТПРАВКА ==========
let rioCurrentStep = 1;
let rioStep1Files = [];
let rioStep2File = null;

async function resetRioSession() {
    if (!state.accessToken) return;

    try {
        await apiFetch("/rio/reset", { method: "POST" });
    } catch (e) {
        console.log("Сброс сессии не требуется");
    }
}

async function handleRioStep1(event) {
    event.preventDefault();

    if (!state.accessToken) {
        showMessage("Сначала войдите в систему", "error");
        activateSection("auth-section");
        return;
    }

    const fileInput1 = document.getElementById("rio-file-1");
    const fileInput2 = document.getElementById("rio-file-2");

    if (!fileInput1 || !fileInput2 || !fileInput1.files.length || !fileInput2.files.length) {
        showMessage("Пожалуйста, прикрепите оба файла", "error");
        return;
    }

    const formData = new FormData();
    formData.append("files", fileInput1.files[0]);
    formData.append("files", fileInput2.files[0]);

    const btn = event.target.querySelector('button[type="submit"]');
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Загрузка...";
    }

    try {
        const response = await apiFetch("/rio/upload-step1", {
            method: "POST",
            body: formData,
            headers: {}
        });

        const data = await response.json();

        if (!response.ok) {
            showMessage(data.detail || "Ошибка загрузки", "error");
            return;
        }

        rioStep1Files = data.files;
        showMessage(data.message, "success");
        goToRioStep(2);

    } catch (error) {
        showMessage("Ошибка загрузки файлов", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Загрузить файлы и продолжить →";
        }
    }
}

async function handleRioStep2(event) {
    event.preventDefault();

    if (!state.accessToken) {
        showMessage("Сначала войдите в систему", "error");
        return;
    }

    const fileInput = document.getElementById("rio-file-check");

    if (!fileInput || !fileInput.files.length) {
        showMessage("Пожалуйста, прикрепите файл для проверки", "error");
        return;
    }

    const file = fileInput.files[0];
    const ext = file.name.split('.').pop().toLowerCase();

    if (ext !== 'doc' && ext !== 'docx') {
        showMessage("Поддерживаются только файлы .doc и .docx", "error");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const btn = event.target.querySelector('button[type="submit"]');
    const loadingDiv = document.getElementById("rio-step2-loading");
    const progressSpan = document.getElementById("rio-check-progress");

    if (btn) {
        btn.disabled = true;
        btn.textContent = "Проверка...";
    }
    if (loadingDiv) loadingDiv.hidden = false;

    let progress = 0;
    const progressInterval = setInterval(() => {
        progress = Math.min(progress + 10, 90);
        if (progressSpan) progressSpan.textContent = `${progress}%`;
    }, 500);

    try {
        const response = await apiFetch("/rio/upload-step2", {
            method: "POST",
            body: formData,
            headers: {}
        });

        const data = await response.json();

        clearInterval(progressInterval);

        if (!response.ok) {
            if (response.status === 422) {
                showMessage(data.message || "Файл содержит ошибки", "error");
            } else {
                showMessage(data.detail || "Ошибка проверки", "error");
            }
            return;
        }

        if (!data.success) {
            showMessage(data.message, "error");
            return;
        }

        rioStep2File = data.filename;
        showMessage(data.message, "success");
        goToRioStep(3);

    } catch (error) {
        clearInterval(progressInterval);
        showMessage("Ошибка при проверке файла", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Проверить файл и продолжить →";
        }
        if (loadingDiv) loadingDiv.hidden = true;
    }
}

async function handleRioStep3(event) {
    event.preventDefault();

    if (!state.accessToken) {
        showMessage("Сначала войдите в систему", "error");
        return;
    }

    const comment = document.getElementById("rio-comment")?.value || "";

    if (comment.length > 1000) {
        showMessage("Комментарий не должен превышать 1000 символов", "error");
        return;
    }

    const btn = event.target.querySelector('button[type="submit"]');
    if (btn) {
        btn.disabled = true;
        btn.textContent = "Отправка...";
    }

    try {
        const response = await apiFetch("/rio/submit-step3", {
            method: "POST",
            body: JSON.stringify({ comment }),
        });

        const data = await response.json();

        if (!response.ok) {
            showMessage(data.detail || "Ошибка отправки", "error");
            return;
        }

        showMessage(data.message, "success");

        const resultDiv = document.getElementById("rio-step3-result");
        if (resultDiv) {
            resultDiv.innerHTML = `
                <div class="stat-card" style="background: #f0fdf4; border-color: #86efac; margin-top: 20px;">
                    <h3 style="color: #166534;">✅ Отправлено успешно!</h3>
                    <p>Ваши файлы отправлены в РИО. Ожидайте ответа на указанный email.</p>
                    <button type="button" class="primary-btn" onclick="resetAndGoToStep1()">
                        Отправить новые файлы
                    </button>
                </div>
            `;
        }

    } catch (error) {
        showMessage("Ошибка при отправке", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = "Отправить в РИО ✉";
        }
    }
}

function goToRioStep(step) {
    rioCurrentStep = step;

    for (let i = 1; i <= 3; i++) {
        const stepDiv = document.getElementById(`rio-step-${i}`);
        if (stepDiv) stepDiv.style.display = "none";
    }

    const currentStepDiv = document.getElementById(`rio-step-${step}`);
    if (currentStepDiv) currentStepDiv.style.display = "block";

    for (let i = 1; i <= 3; i++) {
        const stepIndicator = document.getElementById(`rio-step-${i}-indicator`);
        if (stepIndicator) {
            if (i < step) {
                stepIndicator.className = "step-indicator completed";
            } else if (i === step) {
                stepIndicator.className = "step-indicator active";
            } else {
                stepIndicator.className = "step-indicator";
            }
        }
    }
}

function goToPreviousStep() {
    if (rioCurrentStep > 1) {
        goToRioStep(rioCurrentStep - 1);
    }
}

async function resetAndGoToStep1() {
    await resetRioSession();
    rioStep1Files = [];
    rioStep2File = null;

    const file1 = document.getElementById("rio-file-1");
    const file2 = document.getElementById("rio-file-2");
    const fileCheck = document.getElementById("rio-file-check");
    const comment = document.getElementById("rio-comment");
    const resultDiv = document.getElementById("rio-step3-result");

    if (file1) file1.value = "";
    if (file2) file2.value = "";
    if (fileCheck) fileCheck.value = "";
    if (comment) comment.value = "";
    if (resultDiv) resultDiv.innerHTML = "";

    goToRioStep(1);
}

function loadRioUserInfo() {
    if (state.profile) {
        const fioSpan = document.getElementById("rio-user-fio");
        const emailSpan = document.getElementById("rio-user-email");
        if (fioSpan) fioSpan.textContent = state.profile.fio;
        if (emailSpan) emailSpan.textContent = state.profile.email;
    }
}

function initRioEvents() {
    const form1 = document.getElementById("rio-form-step1");
    const form2 = document.getElementById("rio-form-step2");
    const form3 = document.getElementById("rio-form-step3");
    const backBtn = document.getElementById("rio-back-btn");

    if (form1) form1.addEventListener("submit", handleRioStep1);
    if (form2) form2.addEventListener("submit", handleRioStep2);
    if (form3) form3.addEventListener("submit", handleRioStep3);
    if (backBtn) backBtn.addEventListener("click", goToPreviousStep);

    // Счетчик комментария
    bindTextareaCounter("rio-comment", "rio-comment-counter", 1000);
}

function addRioSectionHTML() {
    if (document.getElementById("rio-section")) return;

    const rioSectionHTML = `
        <section id="rio-section" class="card section">
            <h2>Отправка документов в РИО</h2>
            <p>Заполните все шаги для отправки документов в редакционно-издательский отдел.</p>
            
            <div class="step-indicators">
                <div id="rio-step-1-indicator" class="step-indicator active">Шаг 1: Загрузка файлов</div>
                <div id="rio-step-2-indicator" class="step-indicator">Шаг 2: Проверка документа</div>
                <div id="rio-step-3-indicator" class="step-indicator">Шаг 3: Отправка</div>
            </div>
            
            <div id="rio-step-1" class="rio-step">
                <div class="panel">
                    <h3>Шаг 1: Прикрепите два файла</h3>
                    <form id="rio-form-step1">
                        <label for="rio-file-1">Файл 1 (doc, docx, pdf, txt, rtf, odt)</label>
                        <input type="file" id="rio-file-1" accept=".doc,.docx,.pdf,.txt,.rtf,.odt" required />
                        
                        <label for="rio-file-2">Файл 2 (doc, docx, pdf, txt, rtf, odt)</label>
                        <input type="file" id="rio-file-2" accept=".doc,.docx,.pdf,.txt,.rtf,.odt" required />
                        
                        <button type="submit" class="primary-btn">Загрузить файлы и продолжить →</button>
                    </form>
                </div>
            </div>
            
            <div id="rio-step-2" class="rio-step" style="display: none;">
                <div class="panel">
                    <h3>Шаг 2: Прикрепите документ для проверки</h3>
                    <form id="rio-form-step2">
                        <label for="rio-file-check">Файл для проверки (только .doc или .docx)</label>
                        <input type="file" id="rio-file-check" accept=".doc,.docx" required />
                        
                        <div id="rio-step2-loading" class="loading-box" hidden>
                            <div class="loader"></div>
                            <div class="loading-content">
                                <div class="loading-title">Проверка документа...</div>
                                <div id="rio-check-progress" class="loading-text">0%</div>
                            </div>
                        </div>
                        
                        <div class="form-actions" style="display: flex; gap: 10px; margin-top: 20px;">
                            <button type="button" id="rio-back-btn" class="secondary-btn">← Назад</button>
                            <button type="submit" class="primary-btn">Проверить файл и продолжить →</button>
                        </div>
                    </form>
                </div>
            </div>
            
            <div id="rio-step-3" class="rio-step" style="display: none;">
                <div class="panel">
                    <h3>Шаг 3: Отправка в РИО</h3>
                    
                    <div class="info-box" style="background: #f0f9ff; padding: 15px; border-radius: 12px; margin-bottom: 20px;">
                        <p><strong>Отправитель:</strong> <span id="rio-user-fio"></span></p>
                        <p><strong>Email:</strong> <span id="rio-user-email"></span></p>
                    </div>
                    
                    <form id="rio-form-step3">
                        <label for="rio-comment">Комментарий к отправке (макс. 1000 символов)</label>
                        <div class="textarea-field">
                            <textarea id="rio-comment" rows="4" placeholder="Введите ваш комментарий..."></textarea>
                            <div class="textarea-footer">
                                <small class="field-hint">Дополнительная информация для РИО</small>
                                <span id="rio-comment-counter" class="char-counter">0 / 1000</span>
                            </div>
                        </div>
                        
                        <div class="form-actions" style="display: flex; gap: 10px; margin-top: 20px;">
                            <button type="button" class="secondary-btn" onclick="goToPreviousStep()">← Назад</button>
                            <button type="submit" class="primary-btn">Отправить в РИО ✉</button>
                        </div>
                    </form>
                    
                    <div id="rio-step3-result"></div>
                </div>
            </div>
        </section>
    `;

    const main = document.querySelector('main');
    if (main) {
        main.insertAdjacentHTML('beforeend', rioSectionHTML);
    }
}

function addRioStyles() {
    if (document.getElementById('rio-styles')) return;

    const style = document.createElement('style');
    style.id = 'rio-styles';
    style.textContent = `
        .step-indicators {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .step-indicator {
            flex: 1;
            padding: 12px;
            text-align: center;
            background: #f3f4f6;
            border-radius: 12px;
            font-weight: 500;
            color: #6b7280;
        }
        
        .step-indicator.active {
            background: #2563eb;
            color: white;
        }
        
        .step-indicator.completed {
            background: #15803d;
            color: white;
        }
        
        .rio-step {
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .info-box {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 12px;
        }
        
        .info-box p {
            margin: 8px 0;
        }
        
        .info-box strong {
            color: #0369a1;
        }
    `;
    document.head.appendChild(style);
}

// Делаем функции глобальными
window.goToPreviousStep = goToPreviousStep;
window.resetAndGoToStep1 = resetAndGoToStep1;

// ИНИЦИАЛИЗАЦИЯ
async function bootstrap() {
  updateAuthStatus();
  initNavigation();
  initEvents();
  toggleTitleForms();
  initTextareaCounters();
  hideCheckLoading();

  // Добавляем РИО секцию и стили
  addRioSectionHTML();
  addRioStyles();
  initRioEvents();

  const messageBox = $("global-message");
  if (messageBox) {
    messageBox.style.display = "none";
  }

  const yearInput = $("title-year");
  if (yearInput && !yearInput.value) {
    yearInput.value = new Date().getFullYear();
  }

  const tutorialYearInput = $("tutorial-year");
  if (tutorialYearInput && !tutorialYearInput.value) {
    tutorialYearInput.value = new Date().getFullYear();
  }

  if (state.accessToken) {
    await loadProfile();
    await loadManuals();
  }
}

// Запуск
bootstrap();