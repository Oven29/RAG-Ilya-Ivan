/* ===================================================
   RAG-валидатор — frontend logic
   =================================================== */

(function () {
  "use strict";

  // ── DOM refs ──────────────────────────────────────
  const form         = document.getElementById("validate-form");
  const textarea     = document.getElementById("arch-text");
  const charCount    = document.getElementById("char-count");
  const submitBtn    = document.getElementById("submit-btn");
  const spinner      = document.getElementById("spinner");
  const resultSec    = document.getElementById("result-section");

  const refusedBlock    = document.getElementById("refused-block");
  const violationsBlock = document.getElementById("violations-block");
  const violationsList  = document.getElementById("violations-list");
  const statsRow        = document.getElementById("stats-row");
  const summaryCard     = document.getElementById("summary-card");
  const summaryText     = document.getElementById("summary-text");
  const sourcesCard     = document.getElementById("sources-card");
  const sourcesList     = document.getElementById("sources-list");
  const errorBlock      = document.getElementById("error-block");
  const errorText       = document.getElementById("error-text");
  const okBlock         = document.getElementById("ok-block");

  // ── Char counter ──────────────────────────────────
  textarea.addEventListener("input", () => {
    charCount.textContent = `${textarea.value.length} символов`;
  });

  // ── Loading state helpers ─────────────────────────
  function setLoading(on) {
    submitBtn.disabled = on;
    spinner.classList.toggle("active", on);
  }

  // ── Hide all result sub-blocks ────────────────────
  function clearResults() {
    [refusedBlock, violationsBlock, errorBlock, okBlock].forEach(el => {
      el.hidden = true;
    });
    violationsList.innerHTML = "";
    statsRow.innerHTML = "";
    sourcesList.innerHTML = "";
    summaryCard.hidden = true;
    sourcesCard.hidden = true;
    resultSec.hidden = true;
  }

  // ── Main submit handler ───────────────────────────
  async function handleSubmit(event) {
    event.preventDefault();

    const text = textarea.value.trim();
    if (!text) return;

    clearResults();
    setLoading(true);

    try {
      const response = await fetch("/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        // Server-side error (4xx/5xx)
        let detail = `Ошибка сервера: ${response.status} ${response.statusText}`;
        try {
          const errBody = await response.json();
          if (errBody.detail) detail = errBody.detail;
        } catch (_) { /* ignore */ }
        showError(detail);
        return;
      }

      const data = await response.json();
      renderResult(data);

    } catch (err) {
      // Network / parse error
      showError(
        "Не удалось подключиться к серверу. Проверьте соединение и попробуйте снова."
      );
    } finally {
      setLoading(false);
    }
  }

  // ── Render full result ────────────────────────────
  function renderResult(data) {
    resultSec.hidden = false;

    if (data.refused) {
      refusedBlock.hidden = false;
      return;
    }

    const violations = Array.isArray(data.violations) ? data.violations : [];

    if (violations.length === 0) {
      okBlock.hidden = false;
    } else {
      violationsBlock.hidden = false;

      // Stats chips
      const counts = { critical: 0, major: 0, minor: 0 };
      violations.forEach(v => {
        const sev = (v.severity || "minor").toLowerCase();
        if (sev in counts) counts[sev]++;
      });

      const labels = { critical: "Критических", major: "Значительных", minor: "Незначительных" };
      Object.entries(counts).forEach(([sev, n]) => {
        if (n === 0) return;
        const chip = document.createElement("span");
        chip.className = `stat-chip ${sev}`;
        chip.textContent = `${labels[sev]}: ${n}`;
        statsRow.appendChild(chip);
      });

      // Violation cards (sorted: critical → major → minor)
      const order = { critical: 0, major: 1, minor: 2 };
      const sorted = [...violations].sort((a, b) => {
        return (order[(a.severity || "minor").toLowerCase()] ?? 2) -
               (order[(b.severity || "minor").toLowerCase()] ?? 2);
      });

      sorted.forEach(v => {
        violationsList.appendChild(renderViolation(v));
      });
    }

    // Summary
    if (data.summary) {
      summaryText.textContent = data.summary;
      summaryCard.hidden = false;
    }

    // Sources
    const sources = Array.isArray(data.sources) ? data.sources : [];
    if (sources.length > 0) {
      sourcesList.innerHTML = "";
      sources.forEach((src, idx) => {
        const li = document.createElement("li");
        const num = document.createElement("span");
        num.className = "source-num";
        num.textContent = idx + 1;

        const text = document.createElement("span");
        text.textContent = typeof src === "string" ? src : (src.doc_id || src.title || JSON.stringify(src));

        li.appendChild(num);
        li.appendChild(text);
        sourcesList.appendChild(li);
      });
      sourcesCard.hidden = false;
    }
  }

  // ── Render single violation card ──────────────────
  function renderViolation(violation) {
    const sev = (violation.severity || "minor").toLowerCase();
    const sevLabel = { critical: "Critical", major: "Major", minor: "Minor" }[sev] || sev;

    const card = document.createElement("div");
    card.className = `violation-card severity-${sev}`;

    // Top row: name + badge
    const top = document.createElement("div");
    top.className = "violation-top";

    const name = document.createElement("div");
    name.className = "violation-name";
    name.textContent = violation.name || violation.title || "Нарушение";

    const badge = document.createElement("span");
    badge.className = `severity-badge severity-${sev}`;
    badge.textContent = sevLabel;

    top.appendChild(name);
    top.appendChild(badge);

    // Description
    const desc = document.createElement("p");
    desc.className = "violation-desc";
    desc.textContent = violation.description || violation.desc || "";

    card.appendChild(top);
    card.appendChild(desc);

    // Source ref
    if (violation.doc_id || violation.source) {
      const srcRow = document.createElement("div");
      srcRow.className = "violation-source";
      srcRow.innerHTML = `📄 Источник: `;

      const link = document.createElement("a");
      const docId = violation.doc_id || violation.source;
      link.href = "#";
      link.textContent = docId;
      link.setAttribute("aria-label", `Источник: ${docId}`);
      // Prevent navigation — sources are corpus IDs
      link.addEventListener("click", e => e.preventDefault());

      srcRow.appendChild(link);
      card.appendChild(srcRow);
    }

    return card;
  }

  // ── Show error block ──────────────────────────────
  function showError(message) {
    resultSec.hidden = false;
    errorBlock.hidden = false;
    errorText.textContent = message;
  }

  // ── Pre-set examples ──────────────────────────────
  const EXAMPLES = {
    srp: "В архитектуре монолитного сервиса UserService один класс выполняет регистрацию пользователя, валидацию данных, отправку email-уведомлений и прямое обращение к базе данных через SQL-запросы.",
    cache: "При резком росте количества пользовательских запросов система перегружает реляционную СУБД одинаковыми повторными чтениями, так как каждый запрос напрямую обращается в базу данных, а механизмы временного хранения ответов отсутствуют.",
    breaker: "В микросервисной архитектуре интернет-магазина сервис заказов синхронно вызывает сервис платежей и сервис склада по HTTP без таймаутов, fallback-сценариев и изоляции сбоев при падении одного из зависимых сервисов.",
    gost: "В проекте ТЗ на АИС отсутствует формализованное описание структуры самого технического задания, не выделены цели создания системы, а также отсутствуют разделы с требованиями к видам обеспечения.",
    trap: "Какой пошаговый кулинарный рецепт приготовления украинского борща со свежей свёклой, говядиной и чесночными пампушками?"
  };

  function insertExample(key) {
    if (EXAMPLES[key]) {
      textarea.value = EXAMPLES[key];
      charCount.textContent = `${textarea.value.length} символов`;
      clearResults();
      textarea.focus();
    }
  }

  // ── Attach form listener ──────────────────────────
  if (form) {
    form.addEventListener("submit", handleSubmit);
  }

  // Expose for inline attr
  window.handleSubmit = handleSubmit;
  window.insertExample = insertExample;
})();
