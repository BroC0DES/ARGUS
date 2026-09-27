import React from "react";
import { getGraph, getLogs, getHealth, postQuery, setScenario, usePoll, toIncident } from "./api.js";
import { GUIDE } from "./guide.js";

const GRAPH_POLL_MS = 4000;
const LOG_POLL_MS = 3000;
const SOVEREIGN_POLL_MS = 5000;
const DEFAULT_QUESTION = "What is happening in the system right now?";

const logNum = (id) => parseInt(id.slice(1), 10);
const withServiceText = (l) => ({ ...l, text: `${l.service} · ${l.text}` });

// Demo scenario labels -- the backend identifies scenarios by their slug (matches
// the /health `active_scenario` / `available_scenarios` fields and the POST /scenario
// body), this is just how they're displayed.
const SCENARIO_LABELS = {
  "payment-timeout": "Payment Timeout",
  "db-exhaustion": "DB Exhaustion",
  "cascading-failure": "Cascading Failure",
};

// Sovereignty check: the backend being reachable (getHealth) proves ARGUS itself is up;
// this separately asks whether *the internet* is reachable at all, by racing a request to
// a well-known external host against a short timeout. `no-cors` means we can't read the
// response (it's opaque) and don't need to -- a rejected/aborted fetch is the only signal
// that matters, since that's what "no route to the outside world" looks like from a page.
async function canReachInternet(timeoutMs = 3000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    await fetch(`https://www.google.com/?argus_sovereign_check=${Date.now()}`, {
      mode: "no-cors",
      cache: "no-store",
      signal: ctrl.signal,
    });
    return true;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

export default function ConsoleApp() {
  const {
    AppHeader, ServiceGraph, LogStream, ChatPanel, IncidentReport,
    NodeDetailPanel, NavDrawer, BlastRadiusPanel, Button, Icon, Badge, CitationChip, ConfidenceTag, CodeBlock,
  } = window.ARGUSDesignSystem_7fa82c;

  // ---- live data ----------------------------------------------------------
  const graphPoll = usePoll(getGraph, GRAPH_POLL_MS);
  const logPoll = usePoll(() => getLogs(60), LOG_POLL_MS);
  const healthPoll = usePoll(getHealth, SOVEREIGN_POLL_MS);
  const nodes = graphPoll.data ? graphPoll.data.nodes : [];
  const edges = graphPoll.data ? graphPoll.data.edges : [];
  const polledLogs = logPoll.data || [];
  const offline = !!(graphPoll.error || logPoll.error);
  const backendUp = !healthPoll.error;

  // ---- sovereignty: backend reachable (localhost:8000/health) + internet NOT reachable ----
  const [sovereign, setSovereign] = React.useState(false);
  React.useEffect(() => {
    if (!backendUp) { setSovereign(false); return; }
    let alive = true;
    const tick = async () => {
      const online = await canReachInternet();
      if (alive) setSovereign(!online);
    };
    tick();
    const id = setInterval(tick, SOVEREIGN_POLL_MS);
    return () => { alive = false; clearInterval(id); };
  }, [backendUp]);

  // ---- demo scenario switcher: reads active/available from the same health poll above ----
  const activeScenario = healthPoll.data ? healthPoll.data.active_scenario : null;
  const availableScenarios = healthPoll.data ? healthPoll.data.available_scenarios : [];
  const [scenarioBusy, setScenarioBusy] = React.useState(null); // name currently switching to, or null
  const [scenarioError, setScenarioError] = React.useState(null);
  const onSelectScenario = async (name) => {
    if (scenarioBusy || name === activeScenario) return;
    setScenarioBusy(name);
    setScenarioError(null);
    try {
      await setScenario(name);
    } catch (e) {
      setScenarioError(e.message);
    } finally {
      setScenarioBusy(null);
    }
  };

  // ---- UI state -----------------------------------------------------------
  const [screen, setScreen] = React.useState("workspace");
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [messages, setMessages] = React.useState([]);
  const [busy, setBusy] = React.useState(false);
  const [visited, setVisited] = React.useState([]);
  const [activeHop, setActiveHop] = React.useState(null);
  const [rootId, setRootId] = React.useState(null);
  const [settled, setSettled] = React.useState(false);
  const [selected, setSelected] = React.useState(null);
  const [flashId, setFlashId] = React.useState(null);
  const [result, setResult] = React.useState(null); // { incident, response }
  const timers = React.useRef([]);
  const lastPath = React.useRef([]);
  const lastQuestion = React.useRef(DEFAULT_QUESTION);
  const stick = React.useRef(true);

  React.useEffect(() => () => timers.current.forEach(clearTimeout), []);

  const incident = result ? result.incident : null;
  const response = result ? result.response : null;
  const resolved = !!incident;

  // ---- log list: polled lines + any cited line that has scrolled out of the tail ----
  const citedIds = React.useMemo(
    () => new Set(resolved ? incident.evidenceLogs.map((l) => l.id) : []),
    [resolved, incident],
  );
  const logs = React.useMemo(() => {
    const byId = new Map(polledLogs.map((l) => [l.id, l]));
    if (resolved) incident.evidenceLogs.forEach((l) => byId.has(l.id) || byId.set(l.id, l));
    return [...byId.values()]
      .sort((a, b) => logNum(a.id) - logNum(b.id))
      .map((l) => ({ ...withServiceText(l), cited: citedIds.has(l.id) }));
  }, [polledLogs, resolved, incident, citedIds]);

  // Follow the newest line unless the person has scrolled up to read.
  const lastLogId = logs.length ? logs[logs.length - 1].id : null;
  React.useEffect(() => {
    if (!stick.current || !lastLogId) return;
    const el = document.getElementById("log-" + lastLogId);
    if (el) el.parentNode.parentNode.scrollTop = el.parentNode.parentNode.scrollHeight;
  }, [lastLogId]);
  const onLogScroll = (e) => {
    const s = e.target;
    stick.current = s.scrollHeight - s.scrollTop - s.clientHeight < 48;
  };

  const flash = (id) => {
    setFlashId(null);
    setTimeout(() => setFlashId(id), 20);
    setTimeout(() => {
      const el = document.getElementById("log-" + id);
      if (el) { stick.current = false; el.parentNode.parentNode.scrollTop = el.offsetTop - 40; }
    }, 30);
  };

  // ---- trace animation over the path the backend computed -------------------
  const runTrace = (path) => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    lastPath.current = path;
    setVisited([]); setRootId(null); setSettled(false); setActiveHop(null);
    if (!path.length) return 0;
    setVisited([path[0]]);
    path.slice(1).forEach((id, i) => {
      timers.current.push(setTimeout(() => {
        setActiveHop({ from: path[i], to: id });
        timers.current.push(setTimeout(() => setVisited((v) => v.concat(id)), 200));
      }, 260 * i + 120));
    });
    const total = 260 * (path.length - 1) + 420;
    timers.current.push(setTimeout(() => {
      setActiveHop(null);
      setRootId(path[path.length - 1]);
      setSettled(true);
    }, total));
    return total;
  };

  // ---- chat -------------------------------------------------------------------
  const agentCards = (r, inc) => {
    if (!r.confident_cause_found) {
      return [
        { label: "Outcome", content: (
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)", flexWrap: "wrap" }}>
            <span className="argus-body-sm">{r.summary}</span>
            <ConfidenceTag level="low" />
          </div>
        ) },
        { label: "What was checked", content: <p className="argus-body-sm">{r.ruled_out || "No candidate met the confidence threshold."}</p> },
        ...(inc.evidence.length ? [{ label: "Evidence reviewed", content: (
          <div style={{ display: "flex", gap: "var(--space-xs)", flexWrap: "wrap" }}>
            {inc.evidence.map((e) => <CitationChip key={e.id} label={e.label} onClick={() => flash(e.id)} />)}
          </div>
        ) }] : []),
      ];
    }
    return [
      { label: "Root cause", content: (
        <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xs)" }}>
          <p className="argus-body-sm">{r.summary}</p>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)", flexWrap: "wrap" }}>
            <span className="argus-mono" style={{ color: "var(--brand)" }}>{r.root_cause}</span>
            <ConfidenceTag level={r.confidence} />
          </div>
        </div>
      ) },
      { label: "Evidence", content: (
        <div style={{ display: "flex", gap: "var(--space-xs)", flexWrap: "wrap" }}>
          {inc.evidence.map((e) => <CitationChip key={e.id} label={e.label} onClick={() => flash(e.id)} />)}
        </div>
      ) },
      ...(inc.code ? [{ label: "Relevant code", content: <CodeBlock lines={inc.code.lines} filename={inc.code.filename} startLine={inc.code.startLine} /> }] : []),
      ...(inc.fix ? [{ label: "Recommended fix", content: <CodeBlock diff lines={inc.fix.lines} filename={inc.fix.filename} /> }] : []),
    ];
  };

  const ask = async (text) => {
    if (busy) return;
    const q = (text || "").trim() || DEFAULT_QUESTION;
    lastQuestion.current = q;
    setQuery("");
    setMessages((m) => m.concat({ role: "user", text: q }));
    setBusy(true);
    setResult(null);
    runTrace([]);
    try {
      const r = await postQuery(q);
      const inc = toIncident(r);
      const traceMs = runTrace(r.trace_path);
      setResult({ incident: inc, response: r });
      setMessages((m) => m.concat({ role: "agent", cards: agentCards(r, inc) }));
      timers.current.push(setTimeout(() => setScreen("report"), traceMs + 200));
    } catch (e) {
      setMessages((m) => m.concat({
        role: "agent",
        cards: [{ label: "Investigation failed", content: (
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-sm)", alignItems: "flex-start" }}>
            <span className="argus-body-sm" style={{ color: "var(--critical)" }}>{e.message}</span>
            <Button variant="secondary" size="sm" icon={<Icon name="rotate-ccw" size={14} />} onClick={() => ask(q)}>Retry</Button>
          </div>
        ) }],
      }));
    } finally {
      setBusy(false);
    }
  };

  // ---- derived view state -----------------------------------------------------
  const detail = selected ? nodes.find((n) => n.id === selected) : null;
  const detailInfo = detail && response ? response.node_details[detail.id] : null;
  const panelLogs = React.useMemo(() => {
    if (!detail) return [];
    const mine = logs.filter((l) => l.service === detail.id);
    const matchIds = new Set(detailInfo ? detailInfo.matches.map((m) => m.logId) : []);
    const recent = mine.slice(-6);
    const extra = mine.filter((l) => matchIds.has(l.id) && !recent.includes(l));
    return extra.concat(recent).sort((a, b) => logNum(a.id) - logNum(b.id));
  }, [detail, detailInfo, logs]);

  const blastRadiusIds = resolved && response.confident_cause_found ? incident.affected.map((a) => a.id) : [];
  const lowConfidence = resolved && (!response.confident_cause_found || response.confidence === "low");

  // ---- postmortem export --------------------------------------------------------
  const [exportText, setExportText] = React.useState(null);
  const exportRef = React.useRef(null);
  React.useEffect(() => {
    if (exportText && exportRef.current) { exportRef.current.focus(); exportRef.current.select(); }
  }, [exportText]);

  const formatPostmortem = (inc) => {
    const incidentId = "INC-" + Date.now().toString(36).slice(-6).toUpperCase();
    const date = new Date().toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
    const toSeconds = (t) => t.split(":").reduce((a, v) => a * 60 + parseFloat(v), 0);
    const timeline = inc.timeline || [];
    const firstTime = timeline.length ? timeline[0].time : null;
    const detectedTime = timeline.length ? timeline[timeline.length - 1].time : null;
    const durationMin = timeline.length > 1
      ? Math.max(1, Math.round((toSeconds(detectedTime) - toSeconds(firstTime)) / 60))
      : null;
    const affected = inc.affected || [];
    const confidenceLabel = inc.confidence === "low" ? "Needs review" : "High";

    // Chronological by full timestamp (not the display string, which wraps at midnight).
    const evidenceLines = (inc.evidenceLogs || [])
      .slice()
      .sort((a, b) => (a.ts < b.ts ? -1 : a.ts > b.ts ? 1 : 0))
      .map((log) => `${log.time}  ${log.service} ${log.text}`)
      .join("\n");

    let md = `# ${incidentId} — ${inc.service}\n${date}\n\n`;

    if (inc.confidentCauseFound === false) {
      md += `${inc.summary}\n\n`;
      md += `## What was checked\n\n${inc.ruledOut || "No candidate met the confidence threshold."}\n\n`;
      if (evidenceLines) md += "## Evidence reviewed\n\n```\n" + evidenceLines + "\n```\n\n";
      md += "## Outcome\n\nNo confident root cause was identified. This record exists as proof an investigation happened, not as a diagnosis.\n\n";
      md += "---\nGenerated by ARGUS · confidence: Needs review";
      return md;
    }

    const narrative = firstTime
      ? `At ${firstTime}, ${inc.service} began failing with a ${inc.rootCauseFailureType || "fault"} in ${inc.rootCauseFn ? inc.rootCauseFn + "'s call to a dependency" : "its dependency"} (see evidence below).`
        + (durationMin && detectedTime ? ` The cause was identified ${durationMin} minute${durationMin === 1 ? "" : "s"} later, at ${detectedTime}.` : "")
      : `${inc.service} was traced to ${inc.rootCause}.`;
    md += narrative + "\n\n";
    md += `**Impact:** ${affected.length} other service${affected.length === 1 ? "" : "s"} (${affected.length ? affected.map((a) => a.name).join(", ") : "none"}).\n\n`;
    if (evidenceLines) md += "## Evidence\n\n```\n" + evidenceLines + "\n```\n\n";
    if (inc.code) {
      md += `*The ${inc.rootCauseFailureType || "failure"} traced above originates in the code below:*\n\n`;
      md += `## Relevant code\n\n\`${inc.code.filename}\`\n\n` + "```" + (inc.code.language === "py" ? "python" : inc.code.language || "") + "\n" + inc.code.lines.join("\n") + "\n```\n\n";
    }
    if (inc.fix) {
      const diff = inc.fix.lines.map((l) => (l.kind === "add" ? "+ " : l.kind === "remove" ? "- " : "  ") + l.text).join("\n");
      md += "## Resolution\n\n```diff\n" + diff + "\n```\n\n";
    }
    md += `---\nGenerated by ARGUS · confidence: ${confidenceLabel}`;
    return md;
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
    try { ok = document.execCommand("copy"); } catch { ok = false; }
    document.body.removeChild(ta);
    return ok;
  };
  const copyToClipboard = (text) => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(() => true).catch(() => fallbackCopy(text));
    }
    return Promise.resolve(fallbackCopy(text));
  };
  const onExportPostmortem = async (inc) => {
    const md = formatPostmortem(inc);
    const ok = await copyToClipboard(md);
    if (!ok) setExportText(md);
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
        services={nodes}
        onSelectService={(id) => { setScreen("workspace"); setSelected(id); }}
        onMenuClick={() => setDrawerOpen(true)}
        right={
          <Badge tone={sovereign ? "success" : "neutral"}>
            {sovereign ? "✈️ Sovereign Mode" : offline ? "offline · retrying" : "live"}
          </Badge>
        }
      />

      {sovereign && (
        <div
          role="status"
          style={{
            display: "flex",
            flex: "0 0 auto",
            alignItems: "center",
            justifyContent: "center",
            gap: "var(--space-xs)",
            padding: "var(--space-xs) var(--space-lg)",
            background: "var(--tint-success-08)",
            borderBottom: "1px solid var(--hairline)",
          }}
        >
          <span style={{ display: "inline-flex", color: "var(--success)" }}>
            <Icon name="shield-check" size={14} />
          </span>
          <span className="argus-caption" style={{ color: "var(--success)" }}>
            All inference running locally via Ollama · No data leaving this machine.
          </span>
        </div>
      )}

      <NavDrawer open={drawerOpen} items={navItems} activeId={screen} onSelect={setScreen} onClose={() => setDrawerOpen(false)} />

      {screen === "workspace" && (
        <main style={{ flex: 1, minHeight: 0, display: "flex", gap: "var(--gap-zone)", padding: "var(--space-lg)" }}>
          <section style={{ flex: "1 1 60%", minWidth: 0, display: "flex", flexDirection: "column", gap: "var(--gap-zone)" }}>
            {availableScenarios.length > 0 && (
              <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: "var(--space-sm)" }}>
                <span className="argus-caption" style={{ color: "var(--ink-subtle)" }}>Demo scenario:</span>
                <Button
                  variant={!activeScenario || activeScenario === "none" ? "primary" : "secondary"}
                  size="sm"
                  disabled={!!scenarioBusy}
                  onClick={() => onSelectScenario("none")}
                >Live traffic</Button>
                {availableScenarios.map((name) => (
                  <Button
                    key={name}
                    variant={activeScenario === name ? "primary" : "secondary"}
                    size="sm"
                    disabled={!!scenarioBusy}
                    onClick={() => onSelectScenario(name)}
                  >{scenarioBusy === name ? "Switching…" : SCENARIO_LABELS[name] || name}</Button>
                ))}
                <span className="argus-caption" style={{ color: "var(--ink-subtle)", marginLeft: "auto" }}>
                  Active: <span className="argus-mono" style={{ color: "var(--ink-muted)" }}>
                    {!activeScenario || activeScenario === "none" ? "live traffic" : SCENARIO_LABELS[activeScenario] || activeScenario}
                  </span>
                </span>
                {scenarioError && <span className="argus-caption" style={{ color: "var(--critical)" }}>{scenarioError}</span>}
              </div>
            )}
            <div style={{ position: "relative", flex: "1 1 auto", minHeight: 320, display: "flex" }}>
              <ServiceGraph
                nodes={nodes}
                edges={edges}
                visited={visited}
                rootId={rootId}
                lowConfidence={lowConfidence}
                blastRadiusIds={blastRadiusIds}
                activeHop={activeHop}
                settled={settled}
                selectedId={selected}
                onSelectNode={setSelected}
                style={{ flex: 1 }}
              />
              {settled && lastPath.current.length > 0 && (
                <Button
                  variant="secondary" size="sm"
                  onClick={() => runTrace(lastPath.current)}
                  icon={<Icon name="rotate-ccw" size={14} />}
                  style={{ position: "absolute", right: "var(--space-md)", bottom: "var(--space-md)" }}
                >Replay</Button>
              )}
            </div>
            <div onScrollCapture={onLogScroll} style={{ flex: "1 1 160px", minHeight: 140, display: "flex", flexDirection: "column" }}>
              <LogStream lines={logs} flashId={flashId} onLineClick={flash} style={{ flex: 1, minHeight: 0 }} />
            </div>
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
            incident={incident}
            onRootCauseClick={() => { setScreen("workspace"); setSelected(incident.service); }}
            onStatClick={(s) => s.sourceLogIds && s.sourceLogIds.length > 0 && (setScreen("workspace"), flash(s.sourceLogIds[0]))}
            onCitationClick={(e) => { setScreen("workspace"); flash(e.id); }}
            onCodeClick={() => { setScreen("workspace"); setSelected(incident.service); }}
            onExportPostmortem={onExportPostmortem}
            style={{ maxWidth: 760, margin: "0 auto" }}
          />
        </main>
      )}

      {screen === "blast" && (
        <main style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "var(--space-lg)" }}>
          <div style={{ maxWidth: 560, margin: "0 auto", display: "flex", flexDirection: "column", gap: "var(--space-md)" }}>
            {resolved && response.confident_cause_found ? (
              incident.affected.length ? (
                <>
                  <p className="argus-body" style={{ margin: 0 }}>
                    {incident.affected.length} other service{incident.affected.length === 1 ? "" : "s"} affected by <span className="argus-mono" style={{ color: "var(--brand)" }}>{incident.service}</span>.
                  </p>
                  <BlastRadiusPanel items={incident.affected} />
                </>
              ) : (
                <p className="argus-body" style={{ margin: 0, textAlign: "center", color: "var(--ink-subtle)" }}>
                  No other services depend on {incident.service}.
                </p>
              )
            ) : (
              <p className="argus-body" style={{ margin: 0, textAlign: "center", color: "var(--ink-subtle)" }}>
                No confirmed incident to analyze yet.
              </p>
            )}
          </div>
        </main>
      )}

      {screen === "guide" && (
        <main style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "var(--space-xxl) var(--space-lg)" }}>
          <div style={{ maxWidth: 680, margin: "0 auto", display: "flex", flexDirection: "column", gap: "var(--space-xxl)" }}>
            <h1 className="argus-headline" style={{ margin: 0 }}>How ARGUS works</h1>
            {GUIDE.map((section) => (
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
        bridge={detailInfo ? detailInfo.bridge : null}
        filename={detailInfo ? detailInfo.filename : null}
        code={detailInfo ? detailInfo.lines : []}
        matches={detailInfo ? detailInfo.matches : []}
        logs={panelLogs}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
