const API_BASE = window.location.protocol === "file:"
  ? "http://127.0.0.1:8000/api"
  : `${window.location.origin}/api`;

const fallbackDoctors = [
  { id: 1, name: "Ananya Sharma", specialty: "Cardiology", hospital: "City Heart Institute", location: "Mumbai", rating: 4.8, email: "ananya.sharma@cityheart.in", available_slots: ["2026-06-12 10:00", "2026-06-12 14:00", "2026-06-13 09:00"] },
  { id: 2, name: "Rahul Mehta", specialty: "Dermatology", hospital: "SkinCare Clinic", location: "Delhi", rating: 4.6, email: "rahul.mehta@skincare.in", available_slots: ["2026-06-12 11:00", "2026-06-14 15:00"] },
  { id: 3, name: "Priya Nair", specialty: "Pediatrics", hospital: "Children's Wellness Center", location: "Bangalore", rating: 4.9, email: "priya.nair@kidshealth.in", available_slots: ["2026-06-12 09:30", "2026-06-13 16:00"] },
  { id: 4, name: "Vikram Singh", specialty: "Orthopedics", hospital: "Bone & Joint Hospital", location: "Mumbai", rating: 4.5, email: "vikram.singh@bonejoint.in", available_slots: ["2026-06-15 10:00", "2026-06-15 12:00"] },
  { id: 5, name: "Meera Kapoor", specialty: "General Physician", hospital: "Metro Health", location: "Pune", rating: 4.4, email: "meera.kapoor@metrohealth.in", available_slots: ["2026-06-12 08:00", "2026-06-12 17:00"] },
];

const fallbackPatients = {
  1: { id: 1, name: "Arjun Patel", email: "arjun.patel@email.com", phone: "+91-9876543210", date_of_birth: "1990-05-15", medical_history: ["Hypertension (controlled)", "Seasonal allergies"], allergies: ["Penicillin"] },
  2: { id: 2, name: "Sneha Reddy", email: "sneha.reddy@email.com", phone: "+91-9123456789", date_of_birth: "1985-11-22", medical_history: ["Type 2 Diabetes"], allergies: [] },
};

const fallbackAppointments = [
  { id: 1, patient_id: 1, doctor_id: 1, doctor_name: "Ananya Sharma", datetime: "2026-06-12 13:25", status: "scheduled", notes: "Routine cardiac checkup" },
];

const state = {
  patientId: 1,
  apiOnline: false,
  doctors: [...fallbackDoctors],
  patients: { ...fallbackPatients },
  appointments: [...fallbackAppointments],
  activeDoctorId: null,
  pendingRequest: false,
  call: {
    id: null,
    active: false,
    stage: "idle",
    startedAt: null,
    timerId: null,
    voiceOutput: true,
    autoListen: true,
    voiceMode: "idle",
    processing: false,
  },
};

const titleByView = {
  chat: "AI Care Chat",
  doctors: "Doctor Directory",
  appointments: "Appointments",
  call: "AI Booking Call",
  records: "Patient Records",
};

const subtitleByView = {
  chat: "Route care requests to search, scheduling, records, reminders, and summaries.",
  doctors: "Compare specialists, locations, ratings, and open slots without leaving the workspace.",
  appointments: "Review upcoming visits and move directly into cancellation or summary workflows.",
  call: "Let the AI call agent book a slot and schedule reminders based on the appointment date.",
  records: "Keep patient demographics, allergy alerts, and history visible while coordinating care.",
};

const routeLabelByIntent = {
  search_doctor: "Doctor search",
  book_appointment: "Scheduling",
  patient_records: "Patient records",
  reminder: "Reminder workflow",
  visit_summary: "Visit summary",
  general: "General intake",
};

document.addEventListener("DOMContentLoaded", () => {
  bindEvents();
  refreshData();
  switchView("chat");
});

function bindEvents() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => switchView(button.dataset.view));
  });

  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => sendPrompt(button.dataset.prompt));
  });

  document.getElementById("patient-select").addEventListener("change", async (event) => {
    state.patientId = Number(event.target.value);
    await loadPatient(state.patientId);
    await loadAppointments(state.patientId);
    updatePatientHeader();
    renderAppointments();
    renderRecords();
    updateMetrics();
    toast(`Switched to ${getPatient().name}`);
  });

  document.getElementById("chat-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const input = document.getElementById("chat-input");
    const message = input.value.trim();
    if (!message) return;
    input.value = "";
    resizeComposer(input);
    sendChat(message);
  });

  document.getElementById("chat-input").addEventListener("input", (event) => {
    resizeComposer(event.target);
  });

  ["doctor-search", "specialty-filter", "location-filter"].forEach((id) => {
    document.getElementById(id).addEventListener("input", renderDoctors);
  });

  document.getElementById("refresh-btn").addEventListener("click", refreshData);
  document.getElementById("command-btn").addEventListener("click", openCommandPalette);
  document.getElementById("command-close").addEventListener("click", closeCommandPalette);
  document.getElementById("command-palette").addEventListener("click", (event) => {
    if (event.target.id === "command-palette") closeCommandPalette();
  });
  document.getElementById("command-search").addEventListener("input", renderCommandResults);
  document.getElementById("command-search").addEventListener("keydown", (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    document.querySelector(".command-item.active")?.click();
  });
  document.getElementById("drawer-close").addEventListener("click", closeDoctorDrawer);
  document.getElementById("doctor-drawer").addEventListener("click", (event) => {
    if (event.target.id === "doctor-drawer") closeDoctorDrawer();
  });
  document.getElementById("booking-close").addEventListener("click", closeBookingModal);
  document.getElementById("booking-cancel").addEventListener("click", closeBookingModal);
  document.getElementById("booking-modal").addEventListener("click", (event) => {
    if (event.target.id === "booking-modal") closeBookingModal();
  });
  document.getElementById("booking-form").addEventListener("submit", submitBooking);
  document.getElementById("start-call-btn").addEventListener("click", startAiCall);
  document.getElementById("end-call-btn").addEventListener("click", resetAiCall);
  document.getElementById("quick-start-call").addEventListener("click", () => {
    switchView("call");
    startAiCall();
  });
  document.getElementById("call-form").addEventListener("submit", submitCallTurn);
  document.getElementById("call-voice-output").addEventListener("change", (event) => {
    state.call.voiceOutput = event.target.checked;
  });
  document.getElementById("call-auto-listen").addEventListener("change", (event) => {
    state.call.autoListen = event.target.checked;
  });
  bindVoiceControls();

  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openCommandPalette();
    }
    if (event.key === "Escape") {
      closeCommandPalette();
      closeDoctorDrawer();
      closeBookingModal();
    }
  });
}

async function refreshData() {
  setRefreshState(true);
  await checkApiHealth();
  await loadDoctors();
  await loadPatient(state.patientId);
  await loadAppointments(state.patientId);
  populateFilters();
  updatePatientHeader();
  updateMetrics();
  renderDoctors();
  renderAppointments();
  renderRecords();
  setRefreshState(false);
}

async function checkApiHealth() {
  try {
    const data = await apiGet("/health");
    state.apiOnline = data.status === "ok";
  } catch {
    state.apiOnline = false;
  }
  updateApiStatus();
}

async function loadDoctors() {
  try {
    state.doctors = await apiGet("/doctors");
  } catch {
    state.doctors = [...fallbackDoctors];
  }
}

async function loadPatient(patientId) {
  try {
    state.patients[patientId] = await apiGet(`/patients/${patientId}`);
  } catch {
    state.patients[patientId] = fallbackPatients[patientId];
  }
}

async function loadAppointments(patientId) {
  try {
    const rows = await apiGet(`/patients/${patientId}/appointments`);
    state.appointments = rows.map((row) => ({
      ...row,
      patient_id: patientId,
      doctor_id: doctorIdFromName(row.doctor_name),
    }));
  } catch {
    state.appointments = fallbackAppointments.filter((row) => row.patient_id === patientId);
  }
}

async function apiGet(path) {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

function updateApiStatus() {
  const status = document.getElementById("api-status");
  status.classList.toggle("offline", !state.apiOnline);
  status.lastChild.textContent = state.apiOnline ? " API connected" : " Demo data";
  document.getElementById("data-mode-label").textContent = state.apiOnline ? "Live backend" : "Local fallback";
}

function setRefreshState(isLoading) {
  const button = document.getElementById("refresh-btn");
  button.disabled = isLoading;
  button.textContent = isLoading ? "Refreshing" : "Refresh";
}

function switchView(viewName) {
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  document.getElementById(`view-${viewName}`).classList.add("active");
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === viewName);
  });
  document.getElementById("view-title").textContent = titleByView[viewName];
  document.getElementById("view-subtitle").textContent = subtitleByView[viewName];
}

function updatePatientHeader() {
  const patient = getPatient();
  const initials = getInitials(patient.name);
  document.getElementById("patient-name").textContent = patient.name;
  document.getElementById("patient-meta").textContent = `Patient #${patient.id}`;
  document.getElementById("patient-avatar").textContent = initials;
}

function updateMetrics() {
  const patient = getPatient();
  document.getElementById("metric-doctors").textContent = state.doctors.length;
  document.getElementById("metric-appointments").textContent = getPatientAppointments().length;
  document.getElementById("metric-allergies").textContent = patient.allergies.length;
  document.getElementById("sync-pill").textContent = `Last sync ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
}

function populateFilters() {
  fillSelect("specialty-filter", "All specialties", uniqueValues(state.doctors.map((doc) => doc.specialty)));
  fillSelect("location-filter", "All locations", uniqueValues(state.doctors.map((doc) => doc.location)));
}

function fillSelect(id, label, values) {
  const select = document.getElementById(id);
  const current = select.value;
  select.innerHTML = `<option value="">${label}</option>${values.map((value) => `<option value="${escapeAttr(value)}">${escapeHtml(value)}</option>`).join("")}`;
  if (values.includes(current)) select.value = current;
}

function renderDoctors() {
  const grid = document.getElementById("doctor-grid");
  const query = document.getElementById("doctor-search").value.toLowerCase();
  const specialty = document.getElementById("specialty-filter").value;
  const location = document.getElementById("location-filter").value;

  const doctors = state.doctors.filter((doctor) => {
    const searchable = `${doctor.name} ${doctor.specialty} ${doctor.hospital} ${doctor.location}`.toLowerCase();
    return (!query || searchable.includes(query)) &&
      (!specialty || doctor.specialty === specialty) &&
      (!location || doctor.location === location);
  });

  if (!doctors.length) {
    grid.innerHTML = emptyState("No doctors match those filters.");
    return;
  }

  grid.innerHTML = doctors.map((doctor) => {
    const slots = normalizeSlots(doctor).slice(0, 3);
    const slotHtml = slots.length
      ? slots.map((slot) => `<button class="slot-pill" type="button" data-slot="${escapeAttr(slot)}" data-doctor="${doctor.id}">${formatSlot(slot)}</button>`).join("")
      : `<span class="pill">No open slots</span>`;

    return `
      <article class="doctor-card">
        <div class="doctor-top">
          <span class="doctor-avatar">${getInitials(doctor.name)}</span>
          <div>
            <h3 class="doctor-name">Dr. ${escapeHtml(doctor.name)}</h3>
            <div class="doctor-specialty">${escapeHtml(doctor.specialty)}</div>
            <div class="muted">${escapeHtml(doctor.hospital)}</div>
          </div>
        </div>
        <div class="doctor-meta">
          <span class="pill">${escapeHtml(doctor.location)}</span>
          <span class="pill">Rating ${doctor.rating}/5</span>
        </div>
        <div class="slot-row">${slotHtml}</div>
        <div class="doctor-actions">
          <button type="button" data-profile-doctor="${doctor.id}">Profile</button>
          <button class="primary-action" type="button" data-book-doctor="${doctor.id}">Book</button>
        </div>
      </article>
    `;
  }).join("");

  grid.querySelectorAll("[data-slot]").forEach((button) => {
    button.addEventListener("click", () => {
      const doctor = state.doctors.find((item) => item.id === Number(button.dataset.doctor));
      openBookingModal(doctor.id, button.dataset.slot);
    });
  });

  grid.querySelectorAll("[data-profile-doctor]").forEach((button) => {
    button.addEventListener("click", () => {
      openDoctorDrawer(Number(button.dataset.profileDoctor));
    });
  });

  grid.querySelectorAll("[data-book-doctor]").forEach((button) => {
    button.addEventListener("click", () => {
      openBookingModal(Number(button.dataset.bookDoctor));
    });
  });
}

function renderAppointments() {
  const list = document.getElementById("appointment-list");
  const appointments = getPatientAppointments();

  if (!appointments.length) {
    list.innerHTML = emptyState("No appointments yet. Use chat or the doctor directory to book one.");
    return;
  }

  list.innerHTML = appointments.map((appointment) => {
    const doctor = doctorFromAppointment(appointment);
    const date = parseDate(appointment.datetime);
    return `
      <article class="appointment-card">
        <div class="date-card">
          <span>${date.toLocaleString("en-IN", { month: "short" })}</span>
          <strong>${date.getDate()}</strong>
        </div>
        <div>
          <h3 class="doctor-name">Dr. ${escapeHtml(doctor.name || appointment.doctor_name || "Unknown")}</h3>
          <div class="muted">${escapeHtml(doctor.specialty || "Consultation")} at ${formatTime(appointment.datetime)}</div>
          <div class="muted">${escapeHtml(appointment.notes || "No notes recorded")}</div>
          <span class="pill status ${escapeAttr(appointment.status)}">${escapeHtml(appointment.status)}</span>
        </div>
        <div class="appointment-actions">
          <button type="button" data-summary="${appointment.id}">Summary</button>
          <button type="button" data-cancel="${appointment.id}">Cancel</button>
        </div>
      </article>
    `;
  }).join("");

  list.querySelectorAll("[data-summary]").forEach((button) => {
    button.addEventListener("click", () => sendPrompt(`Summary for appointment #${button.dataset.summary}`));
  });
  list.querySelectorAll("[data-cancel]").forEach((button) => {
    button.addEventListener("click", () => sendPrompt(`Cancel appointment #${button.dataset.cancel}`));
  });
}

function renderRecords() {
  const patient = getPatient();
  const grid = document.getElementById("records-grid");
  const age = calculateAge(patient.date_of_birth);
  const allergies = patient.allergies.length
    ? patient.allergies.map((item) => `<span class="tag alert">${escapeHtml(item)}</span>`).join("")
    : `<span class="tag">No known allergies</span>`;
  const history = patient.medical_history.length
    ? patient.medical_history.map((item) => `<span class="tag">${escapeHtml(item)}</span>`).join("")
    : `<span class="tag">No history recorded</span>`;

  grid.innerHTML = `
    <article class="record-card">
      <h3>Personal information</h3>
      <div class="record-row"><span>Name</span><span>${escapeHtml(patient.name)}</span></div>
      <div class="record-row"><span>Date of birth</span><span>${escapeHtml(patient.date_of_birth)}</span></div>
      <div class="record-row"><span>Age</span><span>${age} years</span></div>
      <div class="record-row"><span>Email</span><span>${escapeHtml(patient.email)}</span></div>
      <div class="record-row"><span>Phone</span><span>${escapeHtml(patient.phone)}</span></div>
    </article>
    <article class="record-card">
      <h3>Clinical notes</h3>
      <p class="muted">Allergies</p>
      <div class="tag-row">${allergies}</div>
      <p class="muted">Medical history</p>
      <div class="tag-row">${history}</div>
    </article>
  `;
}

function openDoctorDrawer(doctorId) {
  const doctor = state.doctors.find((item) => item.id === doctorId);
  if (!doctor) return;
  state.activeDoctorId = doctorId;
  const slots = normalizeSlots(doctor);
  const drawer = document.getElementById("doctor-drawer");
  const content = document.getElementById("drawer-content");
  content.innerHTML = `
    <div class="drawer-hero">
      <span class="doctor-avatar">${getInitials(doctor.name)}</span>
      <div>
        <p class="eyebrow">Doctor profile</p>
        <h2 id="drawer-title">Dr. ${escapeHtml(doctor.name)}</h2>
        <p>${escapeHtml(doctor.specialty)} at ${escapeHtml(doctor.hospital)}</p>
      </div>
    </div>
    <section class="drawer-section">
      <h3>Practice details</h3>
      <div class="record-row"><span>Location</span><span>${escapeHtml(doctor.location)}</span></div>
      <div class="record-row"><span>Rating</span><span>${doctor.rating}/5</span></div>
      <div class="record-row"><span>Email</span><span>${escapeHtml(doctor.email || "Not listed")}</span></div>
    </section>
    <section class="drawer-section">
      <h3>Available slots</h3>
      <div class="slot-row">
        ${slots.length ? slots.map((slot) => `<button class="slot-pill" type="button" data-drawer-slot="${escapeAttr(slot)}">${formatSlot(slot)}</button>`).join("") : `<span class="pill">No open slots</span>`}
      </div>
    </section>
    <div class="drawer-actions">
      <button class="secondary-btn" type="button" data-drawer-ask>Ask AI</button>
      <button class="send-btn" type="button" data-drawer-book>Book visit</button>
    </div>
  `;
  drawer.classList.add("open");
  drawer.setAttribute("aria-hidden", "false");

  content.querySelectorAll("[data-drawer-slot]").forEach((button) => {
    button.addEventListener("click", () => openBookingModal(doctor.id, button.dataset.drawerSlot));
  });
  content.querySelector("[data-drawer-ask]").addEventListener("click", () => {
    closeDoctorDrawer();
    sendPrompt(`Tell me about Dr. ${doctor.name}`);
  });
  content.querySelector("[data-drawer-book]").addEventListener("click", () => openBookingModal(doctor.id));
}

function closeDoctorDrawer() {
  const drawer = document.getElementById("doctor-drawer");
  drawer.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
}

function openBookingModal(doctorId, selectedSlot = "") {
  const doctor = state.doctors.find((item) => item.id === doctorId);
  if (!doctor) return;
  const slots = normalizeSlots(doctor);
  document.getElementById("booking-doctor-id").value = doctor.id;
  document.getElementById("booking-doctor-name").value = `Dr. ${doctor.name}`;
  document.getElementById("booking-slot").innerHTML = slots.length
    ? slots.map((slot) => `<option value="${escapeAttr(slot)}">${formatSlot(slot)}</option>`).join("")
    : `<option value="">No slots available</option>`;
  document.getElementById("booking-slot").value = selectedSlot || slots[0] || "";
  document.getElementById("booking-notes").value = "";
  const modal = document.getElementById("booking-modal");
  modal.classList.add("open");
  modal.setAttribute("aria-hidden", "false");
  setTimeout(() => document.getElementById("booking-slot").focus(), 0);
}

function closeBookingModal() {
  const modal = document.getElementById("booking-modal");
  modal.classList.remove("open");
  modal.setAttribute("aria-hidden", "true");
}

async function submitBooking(event) {
  event.preventDefault();
  const doctorId = Number(document.getElementById("booking-doctor-id").value);
  const slot = document.getElementById("booking-slot").value;
  const notes = document.getElementById("booking-notes").value.trim();
  const doctor = state.doctors.find((item) => item.id === doctorId);
  if (!doctor || !slot) {
    toast("No available slot selected.");
    return;
  }

  try {
    if (state.apiOnline) {
      const response = await fetch(`${API_BASE}/appointments/book`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: state.patientId, doctor_id: doctorId, slot, notes }),
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      await response.json();
      await loadDoctors();
      await loadAppointments(state.patientId);
    } else {
      state.appointments.push({
        id: Date.now(),
        patient_id: state.patientId,
        doctor_id: doctorId,
        doctor_name: doctor.name,
        datetime: slot,
        status: "scheduled",
        notes: notes || "Booked from frontend workspace",
      });
      doctor.available_slots = normalizeSlots(doctor).filter((item) => item !== slot);
    }
    closeBookingModal();
    closeDoctorDrawer();
    updateMetrics();
    renderDoctors();
    renderAppointments();
    switchView("appointments");
    toast(`Booked Dr. ${doctor.name} on ${formatSlot(slot)}.`);
  } catch (error) {
    toast(`Booking failed: ${error.message}`);
  }
}

function openCommandPalette() {
  const palette = document.getElementById("command-palette");
  palette.classList.add("open");
  palette.setAttribute("aria-hidden", "false");
  document.getElementById("command-search").value = "";
  renderCommandResults();
  setTimeout(() => document.getElementById("command-search").focus(), 0);
}

function closeCommandPalette() {
  const palette = document.getElementById("command-palette");
  palette.classList.remove("open");
  palette.setAttribute("aria-hidden", "true");
}

function renderCommandResults() {
  const query = document.getElementById("command-search").value.toLowerCase();
  const actions = [
    { title: "Open AI chat", detail: "Go to chat workspace", kind: "View", run: () => switchView("chat") },
    { title: "Find doctors", detail: "Open provider directory", kind: "View", run: () => switchView("doctors") },
    { title: "Show appointments", detail: "Review patient schedule", kind: "View", run: () => switchView("appointments") },
    { title: "Open patient records", detail: "View allergies and history", kind: "View", run: () => switchView("records") },
    { title: "Ask for reminder", detail: "Send a reminder request to chat", kind: "AI", run: () => sendPrompt("Set appointment reminder") },
    ...state.doctors.map((doctor) => ({
      title: `Dr. ${doctor.name}`,
      detail: `${doctor.specialty} in ${doctor.location}`,
      kind: "Doctor",
      run: () => openDoctorDrawer(doctor.id),
    })),
  ];
  const filtered = actions.filter((item) => `${item.title} ${item.detail} ${item.kind}`.toLowerCase().includes(query)).slice(0, 8);
  const results = document.getElementById("command-results");
  results.innerHTML = filtered.length
    ? filtered.map((item, index) => `
      <button class="command-item ${index === 0 ? "active" : ""}" type="button" data-command-index="${index}">
        <span><strong>${escapeHtml(item.title)}</strong><span>${escapeHtml(item.detail)}</span></span>
        <span class="command-kbd">${escapeHtml(item.kind)}</span>
      </button>
    `).join("")
    : emptyState("No commands found.");

  results.querySelectorAll("[data-command-index]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = filtered[Number(button.dataset.commandIndex)];
      closeCommandPalette();
      action.run();
    });
  });
}

function sendPrompt(prompt) {
  switchView("chat");
  document.getElementById("chat-input").value = "";
  sendChat(prompt);
}

async function sendChat(message) {
  document.getElementById("welcome-card")?.remove();
  addMessage("user", message);
  showTyping(true);
  state.pendingRequest = true;
  setComposerEnabled(false);

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, patient_id: state.patientId }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    showTyping(false);
    addMessage("assistant", data.response, data.intent);
    document.getElementById("route-label").textContent = routeLabelByIntent[data.intent] || "General intake";
    await loadAppointments(state.patientId);
    updateMetrics();
    renderAppointments();
  } catch (error) {
    showTyping(false);
    addMessage("assistant", `I could not reach the API. From the project folder, start it with: python -m app\n\n${error.message}`);
  } finally {
    state.pendingRequest = false;
    setComposerEnabled(true);
  }
}

function setComposerEnabled(isEnabled) {
  const input = document.getElementById("chat-input");
  const button = document.querySelector("#chat-form .send-btn");
  input.disabled = !isEnabled;
  button.disabled = !isEnabled;
  if (isEnabled) input.focus();
}

function addMessage(role, message, intent = "") {
  const feed = document.getElementById("chat-feed");
  const patient = getPatient();
  const row = document.createElement("article");
  row.className = `message-row ${role === "user" ? "user" : "assistant"}`;
  row.innerHTML = `
    <span class="avatar ${role === "assistant" ? "assistant" : ""}">${role === "assistant" ? "AI" : getInitials(patient.name)}</span>
    <div class="message-body">
      <div class="message-bubble">${escapeHtml(message)}</div>
      <div class="message-meta">
        ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        ${intent ? `<span class="intent-tag">${escapeHtml(intent)}</span>` : ""}
      </div>
    </div>
  `;
  feed.appendChild(row);
  feed.scrollTop = feed.scrollHeight;
}

function showTyping(isVisible) {
  document.getElementById("typing-row").classList.toggle("show", isVisible);
}

function toast(message) {
  const stack = document.getElementById("toast-stack");
  const node = document.createElement("div");
  node.className = "toast";
  node.textContent = message;
  stack.appendChild(node);
  setTimeout(() => node.remove(), 2800);
}

function resizeComposer(input) {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 130)}px`;
}

function getPatient() {
  return state.patients[state.patientId] || fallbackPatients[state.patientId] || fallbackPatients[1];
}

function getPatientAppointments() {
  return state.appointments.filter((appointment) => !appointment.patient_id || appointment.patient_id === state.patientId);
}

function doctorFromAppointment(appointment) {
  return state.doctors.find((doctor) => doctor.id === appointment.doctor_id) ||
    state.doctors.find((doctor) => doctor.name === appointment.doctor_name) ||
    {};
}

function doctorIdFromName(name) {
  const clean = String(name || "").replace(/^Dr\.\s*/i, "");
  const doctor = state.doctors.find((item) => item.name === clean);
  return doctor?.id || 0;
}

function normalizeSlots(doctor) {
  return doctor.available_slots || doctor.slots || [];
}

function uniqueValues(values) {
  return [...new Set(values.filter(Boolean))].sort();
}

function getInitials(name) {
  return String(name)
    .split(" ")
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function parseDate(value) {
  return new Date(String(value).replace(" ", "T"));
}

function formatSlot(value) {
  const date = parseDate(value);
  return `${date.toLocaleDateString("en-IN", { month: "short", day: "numeric" })}, ${formatTime(value)}`;
}

function formatTime(value) {
  return parseDate(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function calculateAge(dateOfBirth) {
  const birth = new Date(dateOfBirth);
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) age -= 1;
  return age;
}

function emptyState(message) {
  return `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeAttr(value) {
  return escapeHtml(value);
}

const CallVoice = {
  recognition: null,
  supported: false,

  init() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.supported = Boolean(SpeechRecognition && window.speechSynthesis);
    if (!SpeechRecognition) return;

    this.recognition = new SpeechRecognition();
    this.recognition.lang = "en-IN";
    this.recognition.interimResults = true;
    this.recognition.continuous = false;
    this.recognition.maxAlternatives = 1;

    this.recognition.onresult = (event) => {
      let interim = "";
      let finalText = "";
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += transcript;
        else interim += transcript;
      }
      const input = document.getElementById("call-input");
      input.value = (finalText || interim).trim();
      if (finalText.trim()) {
        stopListening(false);
        deliverCallMessage(finalText.trim());
      }
    };

    this.recognition.onerror = (event) => {
      stopListening(false);
      if (event.error !== "aborted" && event.error !== "no-speech") {
        setVoiceStatus("Voice error", "Try again or type your response.");
        toast(`Voice input error: ${event.error}`);
      } else if (event.error === "no-speech" && state.call.active && state.call.autoListen) {
        setVoiceStatus("Listening", "I did not catch that. Please speak again.");
        window.setTimeout(() => {
          if (state.call.active && !state.call.processing) startListening(true);
        }, 700);
      }
    };

    this.recognition.onend = () => {
      if (state.call.voiceMode === "listening") {
        setVoiceMode("idle");
      }
    };
  },

  speak(text) {
    if (!this.supported || !state.call.voiceOutput || !text) {
      return Promise.resolve();
    }

    window.speechSynthesis.cancel();
    return new Promise((resolve) => {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = "en-IN";
      utterance.rate = 1;
      utterance.pitch = 1;
      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find((voice) => /en-IN|en-GB|Google UK English Female|Microsoft Zira/i.test(`${voice.lang} ${voice.name}`));
      if (preferred) utterance.voice = preferred;

      utterance.onstart = () => {
        setVoiceMode("speaking");
        setVoiceStatus("AI speaking", "Listen to the agent and respond when prompted.");
      };
      utterance.onend = () => {
        setVoiceMode("idle");
        resolve();
      };
      utterance.onerror = () => {
        setVoiceMode("idle");
        resolve();
      };
      window.speechSynthesis.speak(utterance);
    });
  },

  startListening() {
    if (!this.supported || !this.recognition || state.call.processing || !state.call.active) return false;
    if (state.call.voiceMode === "speaking") return false;
    try {
      this.recognition.start();
      setVoiceMode("listening");
      setVoiceStatus("Listening", "Speak naturally. Say your specialty, doctor choice, slot, then confirm.");
      return true;
    } catch {
      return false;
    }
  },

  stop() {
    if (this.recognition && state.call.voiceMode === "listening") {
      try {
        this.recognition.stop();
      } catch {
        // Ignore stop errors from browsers that already ended recognition.
      }
    }
    window.speechSynthesis.cancel();
    setVoiceMode("idle");
  },
};

function bindVoiceControls() {
  CallVoice.init();
  if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
  }

  const micBtn = document.getElementById("call-mic-btn");
  micBtn.addEventListener("mousedown", () => startListening(false));
  micBtn.addEventListener("mouseup", () => stopListening(false));
  micBtn.addEventListener("mouseleave", () => {
    if (state.call.voiceMode === "listening" && !state.call.autoListen) stopListening(false);
  });
  micBtn.addEventListener("touchstart", (event) => {
    event.preventDefault();
    startListening(false);
  }, { passive: false });
  micBtn.addEventListener("touchend", (event) => {
    event.preventDefault();
    stopListening(false);
  }, { passive: false });
}

function setVoiceMode(mode) {
  state.call.voiceMode = mode;
  const orb = document.getElementById("call-orb");
  orb.classList.remove("listening", "speaking", "processing");
  if (mode !== "idle") orb.classList.add(mode);
  document.getElementById("call-mic-btn").setAttribute("aria-pressed", mode === "listening" ? "true" : "false");
}

function setVoiceStatus(title, hint) {
  document.getElementById("call-voice-status").textContent = title;
  document.getElementById("call-voice-hint").textContent = hint;
}

function startListening(autoTriggered = false) {
  if (!CallVoice.supported) {
    setVoiceStatus("Voice unavailable", "Use Chrome or Edge, or type your response below.");
    return;
  }
  if (state.call.processing || !state.call.active) return;
  if (autoTriggered && !state.call.autoListen) return;
  CallVoice.startListening();
}

function stopListening(shouldProcess = false) {
  if (CallVoice.recognition && state.call.voiceMode === "listening") {
    try {
      CallVoice.recognition.stop();
    } catch {
      // Ignore stop errors.
    }
  }
  if (!shouldProcess) setVoiceMode("idle");
}

async function speakAiMessage(message) {
  if (!message) return;
  await CallVoice.speak(message);
  if (state.call.active && state.call.autoListen && CallVoice.supported) {
    window.setTimeout(() => startListening(true), 500);
  }
}

async function deliverCallMessage(message) {
  if (!message || !state.call.active || !state.call.id || state.call.processing) return;
  document.getElementById("call-input").value = message;
  await processCallTurn(message);
}

async function startAiCall() {
  if (!state.apiOnline) {
    toast("Start the backend with: python -m app");
    return;
  }

  resetAiCall(false);
  switchView("call");
  setCallUi("connecting");
  state.call.voiceOutput = document.getElementById("call-voice-output").checked;
  state.call.autoListen = document.getElementById("call-auto-listen").checked;

  try {
    const response = await fetch(`${API_BASE}/calls/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patient_id: state.patientId }),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    state.call = {
      ...state.call,
      id: data.call.id,
      active: true,
      stage: data.call.stage,
      startedAt: Date.now(),
      timerId: window.setInterval(updateCallTimer, 1000),
      processing: false,
    };
    renderCallTranscript(data.call.transcript);
    updateCallStage(data.call.stage);
    setCallUi("live");
    setVoiceStatus("Connected", CallVoice.supported ? "The AI agent is speaking now." : "Voice is unavailable in this browser. Type below instead.");
    toast("AI call connected");
    await speakAiMessage(data.ai_message);
  } catch (error) {
    resetAiCall();
    toast(`Could not start AI call: ${error.message}`);
  }
}

async function submitCallTurn(event) {
  if (event) event.preventDefault();
  const input = document.getElementById("call-input");
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  await processCallTurn(message);
}

async function processCallTurn(message) {
  if (!message || !state.call.active || !state.call.id || state.call.processing) return;

  CallVoice.stop();
  state.call.processing = true;
  setVoiceMode("processing");
  setVoiceStatus("Processing", "Finding doctors, slots, and booking details...");
  setCallComposerEnabled(false);

  try {
    const response = await fetch(`${API_BASE}/calls/${state.call.id}/turn`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `HTTP ${response.status}`);
    }
    const data = await response.json();
    renderCallTranscript(data.call.transcript);
    updateCallStage(data.call.stage);
    if (data.booked) {
      renderCallReminders(data.reminders || data.call.reminders || []);
      state.call.active = false;
      setCallUi("done");
      setVoiceStatus("Booking complete", "Your appointment is confirmed and reminders are scheduled.");
      await speakAiMessage(data.ai_message);
      await loadDoctors();
      await loadAppointments(state.patientId);
      renderAppointments();
      updateMetrics();
      toast("Appointment booked and reminders scheduled");
    } else {
      setVoiceStatus("Connected", "Respond when you are ready.");
      await speakAiMessage(data.ai_message);
    }
  } catch (error) {
    setVoiceStatus("Call issue", error.message);
    toast(`Call failed: ${error.message}`);
    if (state.call.active && state.call.autoListen) startListening(true);
  } finally {
    state.call.processing = false;
    setVoiceMode("idle");
    setCallComposerEnabled(state.call.active);
  }
}

function resetAiCall(clearView = true) {
  CallVoice.stop();
  if (state.call.timerId) {
    window.clearInterval(state.call.timerId);
  }
  state.call = {
    id: null,
    active: false,
    stage: "idle",
    startedAt: null,
    timerId: null,
    voiceOutput: document.getElementById("call-voice-output").checked,
    autoListen: document.getElementById("call-auto-listen").checked,
    voiceMode: "idle",
    processing: false,
  };
  document.getElementById("call-transcript").innerHTML = `
    <article class="call-empty">
      <strong>Start a call to begin booking.</strong>
      <p>Example flow: say you need a cardiologist in Mumbai, pick Dr. Ananya, choose a slot, then confirm with “yes”.</p>
    </article>
  `;
  document.getElementById("call-reminders").innerHTML =
    `<div class="empty-state">Reminders appear here once the AI confirms a booking.</div>`;
  updateCallStage("idle");
  setCallUi("idle");
  setVoiceMode("idle");
  setVoiceStatus("Voice idle", CallVoice.supported ? "Start a call to speak with the AI booking agent." : "Use Chrome or Edge for voice, or type responses below.");
  if (clearView) switchView("call");
}

function renderCallTranscript(transcript) {
  const container = document.getElementById("call-transcript");
  if (!transcript?.length) return;
  container.innerHTML = transcript.map((turn) => `
    <article class="call-line ${turn.speaker === "ai" ? "ai" : "patient"}">
      <span class="call-speaker">${turn.speaker === "ai" ? "MedAssist AI" : getPatient().name}</span>
      <div class="call-bubble">${escapeHtml(turn.text)}</div>
    </article>
  `).join("");
  container.scrollTop = container.scrollHeight;
}

function renderCallReminders(reminders) {
  const container = document.getElementById("call-reminders");
  if (!reminders.length) {
    container.innerHTML = `<div class="empty-state">No future reminder windows were available for this appointment.</div>`;
    return;
  }
  container.innerHTML = reminders.map((item) => `
    <article class="reminder-item">
      <strong>${escapeHtml((item.type || "reminder").replaceAll("_", " "))}</strong>
      <span>${escapeHtml(String(item.remind_at || item.remind_at).replace("T", " ").slice(0, 16))}</span>
    </article>
  `).join("");
}

function updateCallStage(stage) {
  const labels = {
    idle: "Not started",
    collecting_need: "Understanding your need",
    selecting_doctor: "Choosing a doctor",
    selecting_slot: "Selecting a slot",
    confirming: "Confirming booking",
    completed: "Booking completed",
  };
  document.getElementById("call-stage-label").textContent = labels[stage] || stage;
}

function setCallUi(mode) {
  const pill = document.getElementById("call-status-pill");
  const input = document.getElementById("call-input");
  const respondBtn = document.querySelector("#call-form .send-btn");
  const startBtn = document.getElementById("start-call-btn");
  const endBtn = document.getElementById("end-call-btn");

  pill.classList.remove("live", "done");
  if (mode === "connecting") {
    pill.textContent = "Connecting";
  } else if (mode === "live") {
    pill.textContent = "Live call";
    pill.classList.add("live");
  } else if (mode === "done") {
    pill.textContent = "Completed";
    pill.classList.add("done");
  } else {
    pill.textContent = "Idle";
    document.getElementById("call-timer").textContent = "00:00";
  }

  const live = mode === "live";
  input.disabled = !live;
  respondBtn.disabled = !live;
  startBtn.disabled = live || mode === "connecting";
  endBtn.disabled = mode === "idle" || mode === "connecting";
  document.getElementById("call-mic-btn").disabled = !live || !CallVoice.supported;
  if (live) input.focus();
}

function setCallComposerEnabled(enabled) {
  const live = state.call.active && !state.call.processing;
  document.getElementById("call-input").disabled = !enabled || !live;
  document.querySelector("#call-form .send-btn").disabled = !enabled || !live;
  document.getElementById("call-mic-btn").disabled = !enabled || !live || !CallVoice.supported;
}

function updateCallTimer() {
  if (!state.call.startedAt) return;
  const elapsed = Math.floor((Date.now() - state.call.startedAt) / 1000);
  const minutes = String(Math.floor(elapsed / 60)).padStart(2, "0");
  const seconds = String(elapsed % 60).padStart(2, "0");
  document.getElementById("call-timer").textContent = `${minutes}:${seconds}`;
}
