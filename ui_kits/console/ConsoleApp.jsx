function ConsoleApp() {
  const D = window.ARGUS_DATA;
  if (!D) return null;
  const {
    AppHeader, ServiceGraph, LogStream, ChatPanel, IncidentReport,
    NodeDetailPanel, NavDrawer, BlastRadiusPanel, Button, Icon, Badge, CitationChip, ConfidenceTag, CodeBlock, StatGrid,
  } = window.ARGUSDesignSystem_7fa82c || {};
  if (!AppHeader) return null;

  const [screen, setScreen] = React.useState("workspace");
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [messages, setMessages] = React.useState([]);
  const [busy, setBusy] = React.useState(false);
  const [visited, setVisited] = React.useState([]);
  const [activeHop, setActiveHop] = React.useState(null);
  const [rootId, setRootId] = React.useState(null);
  const [settled, setSettled] = React.useState(false);
  const [resolved, setResolved] = React.useState(false);
  const [selected, setSelected] = React.useState(null);
  const [flashId, setFlashId] = React.useState(null);
  const timers = React.useRef([]);

  React.useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const flash = (id) => {
    setFlashId(null);
    setTimeout(() => setFlashId(id), 20);
    const el = document.getElementById("log-" + id);
    if (el) el.parentNode.parentNode.scrollTop = el.offsetTop - 40;
  };

  const runTrace = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setVisited([]); setRootId(null); setSettled(false); setActiveHop(null);
    const path = D.tracePath;
    setVisited([path[0]]);
    path.slice(1).forEach((id, i) => {
      timers.current.push(setTimeout(() => {
        setActiveHop({ from: path[i], to: id });
        timers.current.push(setTimeout(() => setVisited((v) => v.concat(id)), 200));
      }, 260 * i + 120));
    });
    timers.current.push(setTimeout(() => {
      setActiveHop(null);
      setRootId(path[path.length - 1]);
      setSettled(true);
    }, 260 * (path.length - 1) + 420));
  };

  const ask = (text) => {
    const q = (text || "").trim() || "Why are payments failing?";
    setQuery("");
    setMessages((m) => m.concat({ role: "user", text: q }));
    setBusy(true);
    setResolved(false);
    runTrace();
    timers.current.push(setTimeout(() => {
      setBusy(false);
      setResolved(true);
      setScreen("report");
      setMessages((m) => m.concat({ role: "agent", cards: agentCards() }));
    }, 1900));
  };

  const agentCards = () => [
    {
      label: "Root cause",
      content: (
        <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)", flexWrap: "wrap" }}>
          <span className="argus-mono" style={{ color: "var(--brand)" }}>{D.incident.rootCause}</span>
          <ConfidenceTag level="high" />
        </div>
      ),
    },
    {
      label: "Evidence",
      content: (
        <div style={{ display: "flex", gap: "var(--space-xs)", flexWrap: "wrap" }}>
          {D.incident.evidence.map((e) => (
            <CitationChip key={e.id} label={e.label} onClick={() => flash(e.id)} />
          ))}
        </div>
      ),
    },
    {
      label: "Relevant code",
      content: <CodeBlock lines={D.incident.code.lines} filename={D.incident.code.filename} startLine={142} />,
    },
    {
      label: "Recommended fix",
      content: <CodeBlock diff lines={D.incident.fix.lines} filename={D.incident.fix.filename} />,
    },
  ];

  const logs = D.logs.map((l) => ({ ...l, cited: resolved ? l.cited : false }));
  const detail = selected ? D.services.find((s) => s.id === selected) : null;
  const detailCode = detail ? D.serviceCode[detail.id] : null;
  const blastRadiusIds = resolved ? D.blastRadius.map((b) => b.id) : [];

  const [exportText, setExportText] = React.useState(null);
  const exportRef = React.useRef(null);
  React.useEffect(() => {
    if (exportText && exportRef.current) { exportRef.current.focus(); exportRef.current.select(); }
  }, [exportText]);

  const formatPostmortem = (incident) => {
    const incidentId = "INC-" + Date.now().toString(36).slice(-6).toUpperCase();
    const date = new Date().toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
    const toSeconds = (t) => t.split(":").reduce((a, v) => a * 60 + parseFloat(v), 0);
    const timeline = incident.timeline || [];
    const firstTime = timeline.length ? timeline[0].time : null;
    const detectedTime = timeline.length ? timeline[timeline.length - 1].time : null;
    const duration = timeline.length > 1
      ? Math.max(1, Math.round((toSeconds(detectedTime) - toSeconds(firstTime)) / 60)) + "m"
      : null;
    const affected = D.blastRadius || [];
    const confidenceLabel = incident.confidence === "low" ? "Needs review" : "High";

    const evidenceLines = (incident.evidence || [])
      .map((e) => D.logs.find((l) => l.id === e.id))
      .filter(Boolean)
      .sort((a, b) => (a.time < b.time ? -1 : a.time > b.time ? 1 : 0))
      .map((log) => `${log.time}  ${log.text}`)
      .join("\n");

    let md = `# ${incidentId} — ${incident.service}\n${date}\n\n`;

    if (incident.confidentCauseFound === false) {
      md += `${incident.summary}\n\n`;
      md += `## What was checked\n\n${incident.ruledOut || "No candidate met the confidence threshold."}\n\n`;
      if (evidenceLines) md += "## Evidence reviewed\n\n```\n" + evidenceLines + "\n```\n\n";
      md += "## Outcome\n\nNo confident root cause was identified. This record exists as proof an investigation happened, not as a diagnosis.\n\n";
      md += "---\nGenerated by ARGUS · confidence: Needs review";
    } else {
      const durationMin = duration ? parseInt(duration, 10) : null;
      const narrative = firstTime
        ? `At ${firstTime}, ${incident.service} began failing with a ${incident.rootCauseFailureType || "fault"} in ${incident.rootCauseFn ? incident.rootCauseFn + "'s call to " + (incident.rootCauseTarget || "a dependency") : "its dependency"} (see evidence below).`
          + (durationMin && detectedTime ? ` The cause was identified ${durationMin} minute${durationMin === 1 ? "" : "s"} later, at ${detectedTime}.` : "")
        : `${incident.service} was traced to ${incident.rootCause}.`;
      md += narrative + "\n\n";

      const impactList = affected.length ? affected.map((a) => a.name).join(", ") : "none";
      md += `**Impact:** ${affected.length} downstream service${affected.length === 1 ? "" : "s"} (${impactList}).\n\n`;

      if (evidenceLines) md += "## Evidence\n\n```\n" + evidenceLines + "\n```\n\n";

      if (incident.code) {
        md += `*The ${incident.rootCauseFailureType || "failure"} traced above originates in the code below:*\n\n`;
        md += "## Relevant code\n\n```ts\n" + incident.code.lines.join("\n") + "\n```\n\n";
      }
      if (incident.fix) {
        const diff = incident.fix.lines.map((l) => (l.kind === "add" ? "+ " : l.kind === "remove" ? "- " : "  ") + l.text).join("\n");
        md += "## Resolution\n\n```diff\n" + diff + "\n```\n\n";
      }
      md += `---\nGenerated by ARGUS · confidence: ${confidenceLabel}`;
    }

    return md;
  };

  const onExportPostmortem = async (incident) => {
    const md = formatPostmortem(incident);
    const ok = await copyToClipboard(md);
    if (!ok) setExportText(md);
    return ok;
  };

  const copyToClipboard = (text) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(() => true).catch(() => fallbackCopy(text));
    }
    return Promise.resolve(fallbackCopy(text));
  };

  const fallbackCopy = (text) => {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    let ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    return ok;
  };

  const navItems = [
    { id: "workspace", label: "Workspace", icon: "layout-grid" },
    { id: "report", label: "Report", icon: "file-text", badge: resolved ? 1 : null },
    { id: "blast", label: "Blast Radius", icon: "share-2" },
    { id: "guide", label: "How it works", icon: "help-circle" },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", background: "var(--canvas)" }}>
      <AppHeader
        services={D.services}
        onSelectService={(id) => { setScreen("workspace"); setSelected(id); }}
        onMenuClick={() => setDrawerOpen(true)}
        right={<Badge>prod · us-east-1</Badge>}
      />

      <NavDrawer open={drawerOpen} items={navItems} activeId={screen} onSelect={setScreen} onClose={() => setDrawerOpen(false)} />

      {screen === "workspace" && (
        <main style={{ flex: 1, minHeight: 0, display: "flex", gap: "var(--gap-zone)", padding: "var(--space-lg)" }}>
          <section style={{ flex: "1 1 60%", minWidth: 0, display: "flex", flexDirection: "column", gap: "var(--gap-zone)" }}>
            <div style={{ position: "relative", flex: "1 1 auto", minHeight: 320, display: "flex" }}>
              <ServiceGraph
                nodes={D.services}
                edges={D.edges}
                visited={visited}
                rootId={rootId}
                blastRadiusIds={blastRadiusIds}
                activeHop={activeHop}
                settled={settled}
                selectedId={selected}
                onSelectNode={setSelected}
                style={{ flex: 1 }}
              />
              {settled && (
                <Button
                  variant="secondary" size="sm"
                  onClick={runTrace}
                  icon={<Icon name="rotate-ccw" size={14} />}
                  style={{ position: "absolute", right: "var(--space-md)", bottom: "var(--space-md)" }}
                >Replay</Button>
              )}
            </div>
            <LogStream lines={logs} flashId={flashId} onLineClick={flash} style={{ flex: "1 1 160px", minHeight: 140 }} />
          </section>

          <section style={{ flex: "1 1 40%", minWidth: 380, display: "flex", flexDirection: "column", minHeight: 0 }}>
            <ChatPanel
              messages={messages}
              busy={busy}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onSubmit={ask}
            />
          </section>
        </main>
      )}

      {screen === "report" && (
        <main style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "var(--space-lg)" }}>
          <IncidentReport
            incident={resolved ? D.incident : null}
            onRootCauseClick={() => { setScreen("workspace"); setSelected("payment"); }}
            onStatClick={(s) => s.sourceLogIds && (setScreen("workspace"), flash(s.sourceLogIds[0]))}
            onCitationClick={(e) => { setScreen("workspace"); flash(e.id); }}
            onCodeClick={() => { setScreen("workspace"); setSelected("payment"); }}
            onExportPostmortem={onExportPostmortem}
            style={{ maxWidth: 760, margin: "0 auto" }}
          />
        </main>
      )}

      {screen === "blast" && (
        <main style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "var(--space-lg)" }}>
          <div style={{ maxWidth: 560, margin: "0 auto", display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
            {resolved ? (
              <>
                <p className="argus-body" style={{ margin: 0 }}>
                  {D.blastRadius.length} downstream services affected by <span className="argus-mono" style={{ color: "var(--brand)" }}>payment-service</span>.
                </p>
                <BlastRadiusPanel items={D.blastRadius} />
              </>
            ) : (
              <p className="argus-body" style={{ margin: 0, textAlign: "center", color: "var(--ink-subtle)" }}>
                No incident to analyze yet.
              </p>
            )}
          </div>
        </main>
      )}

      {screen === "guide" && (
        <main style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "var(--space-xxl) var(--space-lg)" }}>
          <div style={{ maxWidth: 680, margin: "0 auto", display: "flex", flexDirection: "column", gap: "var(--space-xxl)" }}>
            <h1 className="argus-headline" style={{ margin: 0 }}>How ARGUS works</h1>
            {[
              {
                t: "Workspace",
                items: [
                  { l: "Header & status strip", d: "56px bar with the ARGUS wordmark and one live dot per service. A dot pulses only while that service has an active anomaly — healthy and idle dots stay still. Click a dot to pan the graph to that service." },
                  { l: "Service graph", d: "Every real service in the dependency graph, rendered on load before you ask anything — nothing is generated by a query. Only position is draggable; identity and edges come straight from the dependency graph. A node lights --brand as the trace reaches it, holds --critical if it's the confirmed root cause, and shows a dashed border with a \"needs review\" tag when the agent isn't confident." },
                  { l: "Log stream", d: "The raw evidence, scrolling in real time even at idle. Each line has a severity dot; lines cited by the current report get a brand tint and a \"cited\" tag, right-aligned." },
                  { l: "Chat", d: "Ask in plain language. Answers render as separate Root Cause / Evidence / Code / Fix cards, never one paragraph, staggered in as each resolves. A pulsing dot plus a rotating label (\"Analyzing logs…\", \"Tracing dependencies…\") shows the agent working." },
                  { l: "Node detail panel", d: "Click any node to open it. Shows the relevant source code and recent logs for that one service, plus a one-line bridge explaining why they belong together. Click a cited log line to highlight the exact code line it explains, or click the code line to highlight the log back." },
                ],
              },
              {
                t: "Incident Report",
                items: [
                  { l: "Status header", d: "Red \"INCIDENT — service name\" the moment a cause is confirmed; green \"No active incidents\" at idle." },
                  { l: "Plain-language summary", d: "One sentence, no jargon — what happened, stated as fact." },
                  { l: "Timeline", d: "Dots for first anomaly, escalation and diagnosis, colored with the same severity convention as the log stream." },
                  { l: "Stat grid", d: "Every number is clickable and jumps straight to the log line that produced it — no number ships without a working source link." },
                  { l: "Root cause & confidence", d: "The service name links back to the graph. A confidence tag reads \"High\" or \"Needs review\" and is always visible — this is the product's core trust signal, never hidden." },
                  { l: "Evidence", d: "Citation chips, each clickable through to its source log line." },
                  { l: "Relevant code & recommended fix", d: "Two separate blocks on purpose: the code the cause lives in, then a diff-styled fix — \"here's where it lives\" before \"here's what to change.\"" },
                  { l: "Honest failure state", d: "If nothing clears the confidence bar, the header turns brand — not red — and says so directly: what was checked and what was ruled out, instead of a fabricated best guess." },
                  { l: "Postmortem export", d: "One click formats the report already on screen into a markdown document and copies it — pure templating of existing data, no extra reasoning call." },
                ],
              },
              {
                t: "Blast Radius",
                items: [
                  { l: "What it answers", d: "Which other services are affected by the root cause — a different question from which ones the agent walked through to find it." },
                  { l: "How it's built", d: "Computed by walking the same dependency graph the Workspace already shows, outward from the root cause. No new data source." },
                  { l: "On the graph", d: "Affected nodes get a small brand-tinted corner marker, distinct from the trace-path glow, so the two states can overlap without reading as the same thing." },
                ],
              },
            ].map((section) => (
              <div key={section.t} style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
                <h2 className="argus-card-title">{section.t}</h2>
                <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
                  {section.items.map((it) => (
                    <div key={it.l} style={{ display: "flex", flexDirection: "column", gap: "var(--space-xxs)" }}>
                      <span className="argus-body-sm" style={{ color: "var(--ink)" }}>{it.l}</span>
                      <p className="argus-body-sm" style={{ margin: 0 }}>{it.d}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {exportText && (
        <div
          onClick={() => setExportText(null)}
          style={{ position: "fixed", inset: 0, background: "rgba(1,1,2,0.6)", zIndex: 50, display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          <div onClick={(e) => e.stopPropagation()} style={{ background: "var(--surface-3)", border: "1px solid var(--hairline)", borderRadius: "var(--radius-lg)", padding: "var(--space-lg)", width: 520, display: "flex", flexDirection: "column", gap: "var(--space-sm)" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <span className="argus-card-title">Copy postmortem</span>
              <button onClick={() => setExportText(null)} aria-label="Close" style={{ display: "flex", background: "transparent", border: "1px solid var(--hairline)", borderRadius: "var(--radius-xs)", padding: "var(--space-xxs)", color: "var(--ink-subtle)", cursor: "pointer" }}>
                <Icon name="x" size={14} />
              </button>
            </div>
            <p className="argus-caption" style={{ margin: 0 }}>Automatic copy was blocked by this browser. The text is already selected — press ⌘/Ctrl+C.</p>
            <textarea
              ref={exportRef}
              readOnly
              value={exportText}
              style={{ width: "100%", height: 260, background: "var(--surface-2)", border: "1px solid var(--hairline-tertiary)", borderRadius: "var(--radius-sm)", color: "var(--ink)", fontFamily: "var(--font-mono)", fontSize: "var(--text-mono)", padding: "var(--space-md)", resize: "vertical", boxSizing: "border-box" }}
            />
          </div>
        </div>
      )}

      <NodeDetailPanel
        open={!!detail}
        service={detail ? detail.name : ""}
        health={detail ? detail.health : "healthy"}
        anomaly={detail ? !!detail.anomaly : false}
        bridge={detailCode ? detailCode.bridge : null}
        filename={detailCode ? detailCode.filename : null}
        code={detailCode ? detailCode.lines : []}
        matches={detailCode ? detailCode.matches : []}
        logs={D.logs.slice(2, 7)}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

window.ConsoleApp = ConsoleApp;
