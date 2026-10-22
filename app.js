const nav = document.querySelector(".topbar nav");
document.querySelector(".menu")?.addEventListener("click", () => nav.classList.toggle("open"));
nav?.querySelectorAll("a").forEach(a => a.addEventListener("click", () => nav.classList.remove("open")));
document.querySelector("#year").textContent = new Date().getFullYear();

const apiInput = document.querySelector("#api-url");
const statusText = document.querySelector("#api-status");
const statusDot = document.querySelector("#status-dot");
const base = () => apiInput.value.trim().replace(/\/+$/, "");
async function request(path, options={}) {
  const response = await fetch(base() + path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || data.message || `Request failed (${response.status})`);
  return data;
}
async function connect() {
  statusText.textContent = "Connecting…";
  try {
    const data = await request("/api/health");
    statusDot.className = "status-dot online";
    statusText.textContent = `API connected · ${data.registered_dogs} registered dog(s)`;
    return true;
  } catch (err) {
    statusDot.className = "status-dot offline";
    statusText.textContent = "API not connected — start the FastAPI server";
    return false;
  }
}
document.querySelector("#connect-btn").addEventListener("click", async () => { await connect(); });
apiInput.addEventListener("change", connect);
connect();

document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => {
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t === tab));
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.toggle("active", p.id === `panel-${tab.dataset.tab}`));
  if (tab.dataset.tab === "records") loadRecords();
}));

function showResult(id, content, isError=false) {
  const el = document.querySelector(id);
  el.className = "result" + (isError ? " error" : "");
  el.innerHTML = content;
}
function escapeHTML(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
document.querySelector("#identify-form").addEventListener("submit", async e => {
  e.preventDefault();
  const form = e.currentTarget;
  const file = form.querySelector('input[type="file"]').files[0];
  if (!file) return;
  showResult("#identify-result", "Checking image…");
  const fd = new FormData(); fd.append("image", file);
  try {
    const data = await request("/api/identify/image", {method:"POST", body:fd});
    const dog = data.dog || {};
    const score = data.similarity == null ? "Not available" : `${(data.similarity * 100).toFixed(1)}% prototype similarity`;
    showResult("#identify-result", `<div class="result-card"><h4>${escapeHTML(data.status.replaceAll("_"," ").toUpperCase())}</h4><p>${escapeHTML(data.message)}</p><p><b>Score:</b> ${escapeHTML(score)}</p>${dog.dog_id ? `<p><b>Dog ID:</b> ${escapeHTML(dog.dog_id)} · ${escapeHTML(dog.name)} · ${escapeHTML(dog.area)}</p>` : ""}<p><small>${escapeHTML(data.note || "Prototype result only; verify manually.")}</small></p></div>`);
  } catch (err) { showResult("#identify-result", escapeHTML(err.message), true); }
});
document.querySelector("#register-form").addEventListener("submit", async e => {
  e.preventDefault();
  const form = e.currentTarget;
  const file = form.querySelector('input[type="file"]').files[0];
  if (!file) return;
  showResult("#register-result", "Registering dog and generating QR…");
  const fd = new FormData(form);
  fd.set("image", file);
  try {
    const data = await request("/api/register", {method:"POST", body:fd});
    const dog = data.dog || {};
    showResult("#register-result", `<div class="result-card"><h4>♡ ${escapeHTML(data.message)}</h4><p><b>Dog ID:</b> ${escapeHTML(dog.dog_id)}</p><p><b>Name:</b> ${escapeHTML(dog.name)}</p><p><b>Area:</b> ${escapeHTML(dog.area)}</p><p><b>QR tag:</b> <a href="${base()+escapeHTML(data.qr_download)}" target="_blank" rel="noopener">Download QR PNG ↗</a></p>${data.possible_duplicates?.length ? `<p><b>Possible duplicates to review:</b> ${data.possible_duplicates.map(x=>escapeHTML(x.dog_id)).join(", ")}</p>` : ""}<p><small>${escapeHTML(data.embedding_note || "")}</small></p></div>`);
    form.reset();
    await connect();
  } catch (err) { showResult("#register-result", escapeHTML(err.message), true); }
});
async function loadRecords() {
  const el = document.querySelector("#records-list");
  el.innerHTML = '<p class="muted">Loading records…</p>';
  try {
    const data = await request("/api/dogs");
    if (!data.dogs.length) { el.innerHTML = '<p class="muted">No registered dogs yet. Register a sample dog to begin.</p>'; return; }
    el.innerHTML = data.dogs.map(d => `<article class="record-card"><h4>${escapeHTML(d.name || "Unnamed")} · ${escapeHTML(d.dog_id)}</h4><p><b>Area:</b> ${escapeHTML(d.area)}</p><p><b>Vaccination:</b> ${escapeHTML(d.vaccination_status)}</p><p><b>Sterilisation:</b> ${escapeHTML(d.sterilization_status)}</p><p><b>Care notes:</b> ${escapeHTML(d.care_notes || "Not provided")}</p><div class="record-actions"><a class="small-button" href="${base()}/api/dogs/${encodeURIComponent(d.dog_id)}/qr" target="_blank" rel="noopener">Open QR</a><button class="small-button" data-copy="${escapeHTML(d.dog_id)}">Copy Dog ID</button></div></article>`).join("");
    el.querySelectorAll("[data-copy]").forEach(b => b.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(b.dataset.copy); b.textContent = "Copied ✓"; }
      catch { b.textContent = b.dataset.copy; }
    }));
  } catch (err) { el.innerHTML = `<p class="muted">${escapeHTML(err.message)}</p>`; }
}
document.querySelector("#refresh-records").addEventListener("click", loadRecords);
