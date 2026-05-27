const THEMES = {
  teal: {
    name: "Graphite Teal",
    badge: "Recommended",
    description: "Technical, calm, and operational. Best default for Context Engine.",
    accent: "#4f8f83",
    accentStrong: "#2f6f65",
    accentSoft: "#eef6f4",
    accentBorder: "#cfe3df",
    accentText: "#275f57",
  },
  indigo: {
    name: "Graphite Indigo",
    badge: "Platform",
    description: "A more software-platform feel while remaining restrained.",
    accent: "#6d6adf",
    accentStrong: "#504dc4",
    accentSoft: "#f1f1fb",
    accentBorder: "#dadaf5",
    accentText: "#4643a8",
  },
  sage: {
    name: "Graphite Sage",
    badge: "Quietest",
    description: "Most Ollama-adjacent: muted, earthy, and low-chrome.",
    accent: "#71816d",
    accentStrong: "#53634f",
    accentSoft: "#f2f5f1",
    accentBorder: "#d8e0d5",
    accentText: "#495c45",
  },
  amber: {
    name: "Graphite Amber",
    badge: "Admin",
    description: "Useful for admin/attention emphasis, but warmer as a global accent.",
    accent: "#b9823b",
    accentStrong: "#8f6329",
    accentSoft: "#fbf5ec",
    accentBorder: "#ead8bd",
    accentText: "#754f20",
  },
  steel: {
    name: "Graphite Steel",
    badge: "Enterprise",
    description: "Balanced enterprise/engineering tone with cool operational clarity.",
    accent: "#5b7894",
    accentStrong: "#3f5f78",
    accentSoft: "#f0f5f8",
    accentBorder: "#d2e0e8",
    accentText: "#34546b",
  },
};

const BLOCKS = [
  { id: "overview", label: "Full workspace" },
  { id: "cards", label: "Cards & objects" },
  { id: "settings", label: "Flat settings form" },
  { id: "evidence", label: "Evidence panel" },
  { id: "status", label: "Status & jobs" },
  { id: "forms", label: "Forms & retrieval" },
  { id: "states", label: "Empty/error states" },
];

let currentTheme = "teal";
let currentBlock = "overview";

const $ = (selector) => document.querySelector(selector);
const stage = $("#componentStage");
const themeList = $("#themeList");
const blockList = $("#blockList");
const tokenList = $("#tokenList");
const themeCompare = $("#themeCompare");
const stageTitle = $("#stageTitle");
const stageDescription = $("#stageDescription");

function renderThemeButtons() {
  themeList.innerHTML = Object.entries(THEMES).map(([id, theme]) => `
    <button class="theme-button ${id === currentTheme ? "active" : ""}" data-theme-button="${id}" role="tab" aria-selected="${id === currentTheme}">
      <span class="theme-swatch" style="background:${theme.accent}"></span>
      <span>${theme.name}</span>
      <small>${theme.badge}</small>
    </button>
  `).join("");

  document.querySelectorAll("[data-theme-button]").forEach((button) => {
    button.addEventListener("click", () => setTheme(button.dataset.themeButton));
  });
}

function renderBlockButtons() {
  blockList.innerHTML = BLOCKS.map((block) => `
    <button class="block-button ${block.id === currentBlock ? "active" : ""}" data-block-button="${block.id}" role="tab" aria-selected="${block.id === currentBlock}">
      <span>${block.label}</span>
    </button>
  `).join("");

  document.querySelectorAll("[data-block-button]").forEach((button) => {
    button.addEventListener("click", () => setBlock(button.dataset.blockButton));
  });
}

function renderTokenList() {
  const t = THEMES[currentTheme];
  const rows = [
    ["--accent", t.accent],
    ["--accent-strong", t.accentStrong],
    ["--accent-soft", t.accentSoft],
    ["--accent-border", t.accentBorder],
    ["--accent-text", t.accentText],
  ];
  tokenList.innerHTML = rows.map(([name, value]) => `
    <div class="token-item"><span class="token-dot" style="background:${value}"></span><span>${name}</span><span>${value}</span></div>
  `).join("");
}

function renderThemeCompare() {
  themeCompare.innerHTML = Object.entries(THEMES).map(([id, theme]) => `
    <article class="compare-card ${id === currentTheme ? "active-theme" : ""}" style="--theme-accent:${theme.accent}">
      <div class="object-head">
        <h3>${theme.name.replace("Graphite ", "")}</h3>
        <span class="theme-swatch" style="background:${theme.accent}"></span>
      </div>
      <div class="compare-bars"><span></span><span></span><span></span><span></span></div>
      <p>${theme.badge} · ${theme.accent}</p>
    </article>
  `).join("");
}

function setTheme(themeId) {
  currentTheme = themeId;
  document.documentElement.dataset.theme = themeId;
  const theme = THEMES[themeId];
  stageTitle.textContent = `${theme.name} — ${theme.badge}`;
  stageDescription.textContent = theme.description;
  renderThemeButtons();
  renderTokenList();
  renderThemeCompare();
}

function setBlock(blockId) {
  currentBlock = blockId;
  renderBlockButtons();
  renderStage();
}

function renderStage() {
  const renderers = {
    overview: renderOverview,
    cards: renderCards,
    settings: renderSettings,
    evidence: renderEvidence,
    status: renderStatus,
    forms: renderForms,
    states: renderStates,
  };
  stage.innerHTML = renderers[currentBlock]();
}

function renderOverview() {
  return `
    <div class="card-grid">
      <div class="empty-state">
        <p class="eyebrow">Chat workspace</p>
        <h3>Ask your knowledge graph.</h3>
        <p>Use the retrieval settings button in the composer to choose a domain, then ask a plain-language question.</p>
        <button class="btn btn-control">Summarize this knowledge graph</button>
      </div>
      <div class="card-grid two">
        ${domainCard("fatigue-manuals", "Ready", "9622", "OpenAI · text-embedding-3-small", "42 docs", true)}
        ${providerCard("OpenAI", "Connected", "https://api.openai.com/v1", true)}
      </div>
      ${composerBlock()}
    </div>
  `;
}

function renderCards() {
  return `
    <div class="card-grid">
      <div class="card-header">
        <div class="card-title">shadcn Card patterns, flattened</div>
        <div class="card-description">Use cards for real objects. Use rows/dividers inside cards instead of nested boxes.</div>
      </div>
      <div class="card-grid two">
        ${domainCard("manufacturing-qa", "Ready", "9622", "Ollama · nomic-embed-text", "128 docs", true)}
        ${domainCard("clinical-policies", "Ingesting", "9630", "OpenAI · text-embedding-3-large", "17 docs", false)}
      </div>
      <div class="card-grid three">
        ${providerCard("OpenAI", "Connected", "https://api.openai.com/v1", true)}
        ${providerCard("Ollama", "Available", "http://localhost:11434/v1", false)}
        ${providerCard("AWS Bedrock", "Not configured", "OpenAI-compatible endpoint", false)}
      </div>
    </div>
  `;
}

function renderSettings() {
  return `
    <div class="dialog-preview" role="dialog" aria-label="Create knowledge graph domain preview">
      <h3>Create knowledge graph domain</h3>
      <p>Create an isolated retrieval domain for documents and evidence.</p>

      <div class="section-label">Domain identity</div>
      <div class="form-grid two">
        <div class="field"><label>Domain ID</label><input class="input" value="fatigue" /></div>
        <div class="field"><label>Display name</label><input class="input" value="Fatigue Manuals" /></div>
      </div>

      <div class="field" style="margin-top:14px"><label>Embedding model</label><select class="select"><option>openai · text-embedding-3-small · 1536 dims</option></select><p class="help">Locked after creation. All documents in this domain share the same embedding space.</p></div>

      <div class="section-label">Host port</div>
      <div class="radio-group-flat" aria-label="Host port">
        <label class="radio-row"><input type="radio" checked name="port" /> Auto-assign available port</label>
        <label class="radio-row"><input type="radio" name="port" /> Use custom port</label>
      </div>

      <button class="disclosure-row" type="button"><span>Advanced retrieval defaults</span><span>⌄</span></button>

      <div class="dialog-actions"><button class="btn btn-secondary">Cancel</button><button class="btn btn-primary">Create</button></div>
    </div>
  `;
}

function renderEvidence() {
  return `
    <div class="card-grid">
      <div class="card-header">
        <div class="card-title">Evidence with compact citation map</div>
        <div class="card-description">Document-first evidence display. Accent is limited to citation IDs and selected rows.</div>
      </div>
      <div class="citation-map">
        <div class="citation-row active"><span>[1]</span><b>suspension-report.pdf</b><em>p.12 · chunk_183</em></div>
        <div class="citation-row"><span>[2]</span><b>forging-notes.md</b><em>§3 · chunk_044</em></div>
        <div class="citation-row"><span>[3]</span><b>material-table.xlsx</b><em>T2 · table_002</em></div>
      </div>
      <div class="card-grid two">
        <article class="evidence-card">
          <div class="evidence-card-head"><span class="citation-pill">1</span><strong>suspension-report.pdf</strong><small>p.12</small></div>
          <p>“The optimized preform reduced flash while maintaining target fatigue performance.”</p>
          <footer>chunk_183 · score 0.82 · hybrid</footer>
          <div class="action-row"><button class="btn btn-secondary">Open source</button><button class="btn btn-quiet">Copy citation</button></div>
        </article>
        <article class="evidence-card">
          <div class="evidence-card-head"><span class="citation-pill">3</span><strong>material-table.xlsx</strong><small>T2</small></div>
          <div class="preview-artifact">compact table preview</div>
          <p>Material property table extracted during ingestion.</p>
          <footer>table_002 · score 0.76 · semantic</footer>
        </article>
      </div>
    </div>
  `;
}

function renderStatus() {
  return `
    <div class="card-grid">
      <section class="status-card">
        <div class="object-head"><div><h3>System status</h3><p>App Ready · Postgres Ready · Redis Ready · 3 LightRAG domains running</p></div><span class="badge accent-badge"><span class="dot accent"></span>live</span></div>
        <div class="row-list" style="margin-top:14px">
          ${statusRow("App API", "Ready", "latency 28ms", "success")}
          ${statusRow("LightRAG: fatigue-manuals", "Ingesting", "2 jobs queued", "accent")}
          ${statusRow("Redis worker", "Ready", "last heartbeat 12s", "success")}
          ${statusRow("Archived test", "Stopped", "not queryable", "muted")}
        </div>
      </section>
      <section class="status-card">
        <div class="object-head"><div><h3>Ingestion job</h3><p>suspension-report.pdf · extracting tables/images</p></div><span class="badge">56%</span></div>
        <div style="margin:14px 0 6px" class="progress-track"><div class="progress-fill"></div></div>
        <p class="meta">Job: ingest_01HX · pages 12/48 · started 09:41</p>
      </section>
      <section class="status-card">
        <div class="object-head"><div><h3>Recent logs</h3><p>Flat rows, monospace event names, no card-per-log.</p></div></div>
        <div class="log-list" style="margin-top:12px">
          <div class="log-line"><span>09:41:22</span><b>ingest.started</b><span>suspension-report.pdf</span></div>
          <div class="log-line"><span>09:42:10</span><b>parse.complete</b><span>48 pages</span></div>
          <div class="log-line"><span>09:42:33</span><b>lightrag.upsert</b><span>183 chunks</span></div>
          <div class="log-line"><span>09:43:01</span><b>ingest.complete</b><span>Ready</span></div>
        </div>
      </section>
    </div>
  `;
}

function renderForms() {
  return `
    <div class="card-grid two">
      <section class="popover-preview">
        <h3>Retrieval settings</h3>
        <p>Frequent controls live in a popover. Advanced settings are progressively disclosed.</p>
        <div class="segmented"><button class="active">Hybrid</button><button>Semantic</button><button>Graph</button></div>
        <div class="row-item"><div class="row-label"><h4>Domain</h4><p>Knowledge graph to query.</p></div><span class="chip selected">fatigue-manuals</span></div>
        <div class="row-item"><div class="row-label"><h4>Top-k</h4><p>Returned evidence items.</p></div><input class="input" value="10" style="max-width:82px" /></div>
        <div class="row-item"><div class="row-label"><h4>Include tables/images</h4><p>Return extracted artifacts.</p></div><label class="radio-row"><input type="checkbox" checked /> enabled</label></div>
      </section>
      <section class="popover-preview">
        <h3>API key form</h3>
        <p>Use rows and helper copy. Avoid nested cards.</p>
        <div class="field"><label>Provider</label><select class="select"><option>OpenAI</option><option>Ollama</option><option>AWS Bedrock</option></select></div>
        <div class="field" style="margin-top:12px"><label>Base URL</label><input class="input mono" value="https://api.openai.com/v1" /></div>
        <div class="field" style="margin-top:12px"><label>API key</label><input class="input mono" value="••••••••••••••••" /></div>
        <p class="help">Last validated 2 minutes ago. Full secret is never displayed after save.</p>
        <div class="action-row"><button class="btn btn-primary">Save</button><button class="btn btn-secondary">Test connection</button></div>
      </section>
      <section class="popover-preview" style="grid-column:1/-1;max-width:none">
        ${composerBlock()}
      </section>
    </div>
  `;
}

function renderStates() {
  return `
    <div class="card-grid two">
      <div class="empty-state"><h3>No documents in this domain yet.</h3><p>Upload documents to build the workspace tree and retrieval index.</p><button class="btn btn-primary">Upload documents</button></div>
      <div class="empty-state"><h3>Admin access required.</h3><p>You can query existing knowledge graph domains, but only admins can upload documents or manage lifecycle settings.</p><button class="btn btn-secondary">View available domains</button></div>
      <div class="empty-state"><h3>Operation-level error.</h3><p>The domain start request returned HTTP 200, but the operation result was <span class="mono">error</span>. View domain logs for the container startup failure.</p><button class="btn btn-secondary">View logs</button></div>
      <div class="empty-state"><h3>Delete domain?</h3><p>Deletion removes uploaded files, derived artifacts, vector stores, graph stores, and job history according to retention policy.</p><div class="action-row"><button class="btn btn-secondary">Cancel</button><button class="btn btn-danger">Delete domain</button></div></div>
    </div>
  `;
}

function domainCard(name, status, port, model, docs, active) {
  const dotClass = status === "Ready" ? "success" : status === "Ingesting" ? "accent" : "muted";
  return `
    <article class="domain-card">
      <div class="object-head">
        <div><h3>${name}</h3><p>Port ${port} · ${model} · ${docs}</p></div>
        <span class="badge ${active ? "accent-badge" : ""}"><span class="dot ${dotClass}"></span>${status}</span>
      </div>
      <p class="meta">Last indexed 2026-05-27 09:40 · embedding locked after ingestion</p>
      <div class="action-row"><button class="btn btn-primary">Open</button><button class="btn btn-secondary">Upload</button><button class="btn btn-quiet">Restart</button><button class="btn btn-quiet">Archive</button></div>
    </article>
  `;
}

function providerCard(name, status, url, connected) {
  return `
    <article class="provider-card">
      <div class="object-head">
        <div><h3>${name}</h3><p>${url}</p></div>
        <span class="badge ${connected ? "accent-badge" : ""}"><span class="dot ${connected ? "success" : ""}"></span>${status}</span>
      </div>
      <div class="row-item"><div class="row-label"><h4>Default LLM</h4><p>Answer generation behavior</p></div><span class="chip">gpt-4.1-mini</span></div>
      <div class="action-row"><button class="btn btn-secondary">Configure</button><button class="btn btn-quiet">Test</button></div>
    </article>
  `;
}

function statusRow(label, status, detail, dot) {
  return `
    <div class="row-item"><div class="row-label"><h4>${label}</h4><p>${detail}</p></div><span class="badge"><span class="dot ${dot}"></span>${status}</span></div>
  `;
}

function composerBlock() {
  return `
    <div class="card">
      <div class="card-header"><div class="card-title">Chat composer</div><div class="card-description">Quiet, persistent, and free of decorative AI chrome.</div></div>
      <div class="textarea" contenteditable="true" aria-label="Message input">Ask your knowledge graph about bearing inspection intervals...</div>
      <div class="action-row" style="justify-content:space-between;align-items:center">
        <div class="action-row"><span class="chip selected">fatigue-manuals</span><span class="chip">hybrid</span><span class="chip">top-k 10</span></div>
        <button class="btn btn-primary">Send ↑</button>
      </div>
    </div>
  `;
}

function copyTokens() {
  const t = THEMES[currentTheme];
  const css = `[data-ce-theme="${currentTheme}"] {\n  --ce-accent: ${t.accent};\n  --ce-accent-strong: ${t.accentStrong};\n  --ce-accent-soft: ${t.accentSoft};\n  --ce-accent-border: ${t.accentBorder};\n  --ce-accent-text: ${t.accentText};\n}`;
  navigator.clipboard?.writeText(css).then(() => {
    const button = $("#copyTokens");
    const previous = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => { button.textContent = previous; }, 1200);
  });
}

function init() {
  renderThemeButtons();
  renderBlockButtons();
  renderTokenList();
  renderThemeCompare();
  renderStage();

  $("#darkToggle").addEventListener("change", (event) => {
    document.documentElement.dataset.mode = event.target.checked ? "dark" : "light";
  });
  $("#boundaryToggle").addEventListener("change", (event) => {
    document.documentElement.dataset.boundaries = event.target.checked ? "visible" : "minimal";
  });
  $("#densitySelect").addEventListener("change", (event) => {
    document.documentElement.dataset.density = event.target.value;
  });
  $("#copyTokens").addEventListener("click", copyTokens);
  setTheme(currentTheme);
}

init();
