const form = document.getElementById("assessmentForm");
const fillSampleBtn = document.getElementById("fillSampleBtn");
const clearBtn = document.getElementById("clearBtn");
const clearRecordsBtn = document.getElementById("clearRecordsBtn");
const searchInput = document.getElementById("searchInput");
const recordsTableBody = document.getElementById("recordsTableBody");
const submitBtn = form.querySelector('button[type="submit"]');
const toastContainer = document.getElementById("toastContainer");

const riskBadge = document.getElementById("riskBadge");
const riskTitle = document.getElementById("riskTitle");
const riskScore = document.getElementById("riskScore");
const riskReason = document.getElementById("riskReason");
const recommendationList = document.getElementById("recommendationList");

const heroRiskLabel = document.getElementById("heroRiskLabel");
const heroRiskHint = document.getElementById("heroRiskHint");
const statsTotal = document.getElementById("statsTotal");
const statsHigh = document.getElementById("statsHigh");
const statsAverage = document.getElementById("statsAverage");
const toggleChips = document.querySelectorAll("[data-toggle-chip]");

const sampleAssessment = {
  passengerName: "Aisha Rahman",
  bookingReference: "BRG472",
  bagTag: "BG-1001",
  flightNumber: "EK211",
  origin: "DXB",
  destination: "LHR",
  layoverMinutes: 55,
  transferPoints: 2,
  terminalDistance: 1200,
  incomingDelay: 18,
  checkedBags: 2,
  baggageType: "transfer",
  priorityStatus: false,
  internationalTransfer: true,
};

let records = [];
let editingRecordId = null;
let recordsLoadState = "idle";

function showToast(message, type = "success") {
  if (!toastContainer) {
    if (type === "error") {
      window.alert(message);
    }
    return;
  }

  const toast = document.createElement("div");
  toast.className = `toast is-${type}`;
  toast.textContent = message;
  toastContainer.appendChild(toast);

  window.setTimeout(() => {
    toast.classList.add("is-hiding");
    window.setTimeout(() => toast.remove(), 250);
  }, 2600);
}

function setRecordsState(state) {
  recordsLoadState = state;
}

function setEditingRecord(recordId) {
  editingRecordId = recordId;
  submitBtn.textContent = recordId ? "Update and save" : "Predict and save";
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    throw new Error(payload?.message || "Something went wrong while syncing records.");
  }

  return payload;
}

async function loadRecords() {
  setRecordsState("loading");
  renderTable();

  try {
    records = await requestJson("/records");
    setRecordsState("ready");
    renderTable();
  } catch (error) {
    setRecordsState("error");
    renderTable();
    throw error;
  }
}

function fillForm(data) {
  Object.entries(data).forEach(([key, value]) => {
    const field = form.elements.namedItem(key);
    if (!field) return;
    if (field.type === "checkbox") {
      field.checked = Boolean(value);
      return;
    }
    field.value = value;
  });

  syncToggleChips();
}

function clearForm() {
  form.reset();
  setEditingRecord(null);
  syncToggleChips();
}

function syncToggleChips() {
  toggleChips.forEach((chip) => {
    const input = chip.querySelector(".toggle-input");
    if (!input) return;
    chip.classList.toggle("is-selected", input.checked);
  });
}

function getFormData() {
  const data = new FormData(form);
  return {
    passengerName: String(data.get("passengerName") || "").trim(),
    bookingReference: String(data.get("bookingReference") || "").trim().toUpperCase(),
    bagTag: String(data.get("bagTag") || "").trim().toUpperCase(),
    flightNumber: String(data.get("flightNumber") || "").trim().toUpperCase(),
    origin: String(data.get("origin") || "").trim().toUpperCase(),
    destination: String(data.get("destination") || "").trim().toUpperCase(),
    layoverMinutes: Number(data.get("layoverMinutes")),
    transferPoints: Number(data.get("transferPoints")),
    terminalDistance: Number(data.get("terminalDistance")),
    incomingDelay: Number(data.get("incomingDelay")),
    checkedBags: Number(data.get("checkedBags")),
    baggageType: String(data.get("baggageType") || "transfer"),
    priorityStatus: form.elements.namedItem("priorityStatus").checked,
    internationalTransfer: form.elements.namedItem("internationalTransfer").checked,
  };
}

function validate(data) {
  const required = [
    "passengerName",
    "bookingReference",
    "bagTag",
    "flightNumber",
    "origin",
    "destination",
  ];
  if (required.some((key) => !data[key])) {
    throw new Error("Please fill in all text fields.");
  }

  const numbers = [
    "layoverMinutes",
    "transferPoints",
    "terminalDistance",
    "incomingDelay",
    "checkedBags",
  ];
  if (numbers.some((key) => Number.isNaN(data[key]) || data[key] < 0)) {
    throw new Error("Please enter valid positive numbers.");
  }
  if (data.layoverMinutes < 1 || data.transferPoints < 1 || data.checkedBags < 1) {
    throw new Error("Layover, transfer points, and checked bags must be greater than zero.");
  }
}

function scoreAssessment(data) {
  return requestJson("/predict", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

function buildRecord(data, result) {
  return {
    id: editingRecordId || crypto.randomUUID(),
    ...data,
    route: `${data.origin}-${data.destination}`,
    risk: result.risk,
    score: result.score,
    savedAt: new Date().toLocaleString(),
  };
}

function getRecordById(recordId) {
  return records.find((record) => record.id === recordId);
}

function getEditableData(record) {
  const [origin = "", destination = ""] = String(record.route || "-").split("-");

  return {
    passengerName: record.passengerName || "",
    bookingReference: record.bookingReference || "",
    bagTag: record.bagTag || "",
    flightNumber: record.flightNumber || "",
    origin: record.origin || origin,
    destination: record.destination || destination,
    layoverMinutes: record.layoverMinutes ?? "",
    transferPoints: record.transferPoints ?? "",
    terminalDistance: record.terminalDistance ?? "",
    incomingDelay: record.incomingDelay ?? "",
    checkedBags: record.checkedBags ?? "",
    baggageType: record.baggageType || "transfer",
    priorityStatus: Boolean(record.priorityStatus),
    internationalTransfer: Boolean(record.internationalTransfer),
  };
}

function updateSummary(result) {
  riskBadge.className = `risk-badge ${result.risk.toLowerCase()}`;
  riskBadge.textContent = `${result.risk} Risk`;
  riskTitle.textContent = `${result.risk} transfer probability detected`;
  riskScore.textContent = `Confidence score: ${result.score}%`;
  riskReason.textContent = result.reasons.join(" ");
  recommendationList.innerHTML = result.recommendations.map((item) => `<li>${item}</li>`).join("");

  heroRiskLabel.textContent = result.risk;
  heroRiskHint.textContent = `${result.score}% confidence from the latest assessment`;
}

function renderStats() {
  const total = records.length;
  const high = records.filter((record) => record.risk === "High").length;
  const average = total
    ? Math.round(records.reduce((sum, record) => sum + record.score, 0) / total)
    : 0;

  statsTotal.textContent = total;
  statsHigh.textContent = high;
  statsAverage.textContent = `${average}%`;
}

function renderTable() {
  if (recordsLoadState === "loading") {
    recordsTableBody.innerHTML = `
      <tr class="status-row">
        <td colspan="8">Loading shared assessments...</td>
      </tr>
    `;
    renderStats();
    return;
  }

  if (recordsLoadState === "error") {
    recordsTableBody.innerHTML = `
      <tr class="status-row is-error">
        <td colspan="8">We couldn't load the shared records right now. Please refresh and try again.</td>
      </tr>
    `;
    renderStats();
    return;
  }

  const query = searchInput.value.trim().toLowerCase();
  const filtered = records.filter((record) => {
    const haystack = [
      record.passengerName,
      record.flightNumber,
      record.route,
      record.bagTag,
      record.risk,
      record.bookingReference,
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(query);
  });

  if (!filtered.length) {
    recordsTableBody.innerHTML = `
      <tr class="empty-row">
        <td colspan="8">${
          query
            ? "No assessments match your current search."
            : "No saved assessments yet. Run a prediction to populate this table."
        }</td>
      </tr>
    `;
    renderStats();
    return;
  }

  recordsTableBody.innerHTML = filtered
    .map(
      (record) => `
        <tr>
          <td>
            <strong>${escapeHtml(record.passengerName)}</strong><br />
            <small>${escapeHtml(record.bookingReference)}</small>
          </td>
          <td>${escapeHtml(record.flightNumber)}</td>
          <td>${escapeHtml(record.route)}</td>
          <td>${escapeHtml(record.bagTag)}<br /><small>${escapeHtml(record.baggageType)}</small></td>
          <td><span class="pill-cell pill-${String(record.risk).toLowerCase()}">${escapeHtml(record.risk)}</span></td>
          <td>${record.score}%</td>
          <td>${escapeHtml(record.savedAt)}</td>
          <td>
            <div class="row-actions">
              <button class="table-action-btn" type="button" data-action="edit" data-record-id="${record.id}">Edit</button>
              <button class="table-action-btn is-danger" type="button" data-action="delete" data-record-id="${record.id}">Delete</button>
            </div>
          </td>
        </tr>
      `
    )
    .join("");

  renderStats();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  try {
    const data = getFormData();
    validate(data);
    const result = await scoreAssessment(data);
    const record = buildRecord(data, result);

    if (editingRecordId) {
      await requestJson(`/records/${editingRecordId}`, {
        method: "PUT",
        body: JSON.stringify(record),
      });
      showToast("Assessment updated.");
    } else {
      await requestJson("/records", {
        method: "POST",
        body: JSON.stringify(record),
      });
      showToast("Assessment saved.");
    }

    updateSummary(result);
    await loadRecords();
    setEditingRecord(null);
  } catch (error) {
    showToast(error.message, "error");
  }
});

fillSampleBtn.addEventListener("click", () => {
  fillForm(sampleAssessment);
});

clearBtn.addEventListener("click", () => {
  clearForm();
});

clearRecordsBtn.addEventListener("click", async () => {
  const confirmed = window.confirm("Clear all saved assessments for everyone?");
  if (!confirmed) return;

  try {
    await requestJson("/records", { method: "DELETE" });
    records = [];
    setRecordsState("ready");
    renderTable();
    showToast("All shared assessments cleared.");
  } catch (error) {
    showToast(error.message, "error");
  }
});

searchInput.addEventListener("input", renderTable);

recordsTableBody.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;

  const { action, recordId } = button.dataset;
  const record = getRecordById(recordId);
  if (!record) return;

  if (action === "delete") {
    const confirmed = window.confirm("Delete this saved assessment?");
    if (!confirmed) return;

    try {
      await requestJson(`/records/${recordId}`, { method: "DELETE" });
      records = records.filter((item) => item.id !== recordId);

      if (editingRecordId === recordId) {
        clearForm();
      }

      renderTable();
      showToast("Assessment deleted.");
    } catch (error) {
      showToast(error.message, "error");
    }
    return;
  }

  if (action === "edit") {
    const editableData = getEditableData(record);
    fillForm(editableData);
    setEditingRecord(recordId);
    showToast("Assessment loaded into the form.");

    try {
      const previewData = {
        ...editableData,
        layoverMinutes: Number(editableData.layoverMinutes),
        transferPoints: Number(editableData.transferPoints),
        terminalDistance: Number(editableData.terminalDistance),
        incomingDelay: Number(editableData.incomingDelay),
        checkedBags: Number(editableData.checkedBags),
      };
      validate(previewData);
      updateSummary(await scoreAssessment(previewData));
    } catch {
    }
  }
});

toggleChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    const input = chip.querySelector(".toggle-input");
    if (!input) return;

    window.setTimeout(syncToggleChips, 0);
  });
});

loadRecords().catch((error) => {
  showToast(error.message, "error");
});
