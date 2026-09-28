// Full plain-English deep-dive for one incident report. Opened by the
// "Details" button on the Report screen (see ConsoleApp.jsx). Pure frontend:
// every sentence below is a template filled from fields POST /query already
// returns (see backend/query_pipeline.py run_query()'s return dict) -- no
// new backend call, no LLM call, nothing invented. Where a field is empty,
// every section says so plainly instead of guessing.
//
// Design: docs/superpowers/specs/2026-09-28-details-panel-design.md
import React from "react";

const NA = "Not available in the current investigation data.";

// ---- small prose helpers ---------------------------------------------------
const join2 = (items) => {
  if (items.length <= 1) return items.join("");
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return items.slice(0, -1).join(", ") + ", and " + items[items.length - 1];
};

function severityOf(r) {
  if (r.answer_type !== "incident") return "No incident";
  return r.confidence === "high" ? "Critical" : "Uncertain";
}

function summaryProse(r) {
  if (r.answer_type === "healthy") {
    return r.mode === "specific"
      ? `${r.target} has no errors right now -- there's nothing to diagnose here.`
      : "Nothing in the system currently has real errors -- there's nothing to diagnose.";
  }
  if (r.answer_type === "unknown_service") {
    return `"${r.target}" doesn't match any service ARGUS knows about, so it couldn't be checked.`;
  }
  if (r.answer_type !== "incident" || !r.root_cause_service) {
    return NA;
  }
  const cascading = (r.affected_nodes || []).length > 0;
  const confWord = r.confidence === "high" ? "high-confidence" : "low-confidence";
  const failure = r.failure_type ? ` with a ${r.failure_type} fault` : "";
  const cascadeNote = cascading
    ? ` This is a cascading failure -- ${r.affected_nodes.length} other service${r.affected_nodes.length === 1 ? " depends" : "s depend"} on ${r.root_cause_service}, so their errors are a side effect, not a separate problem.`
    : " No other service is affected by this yet.";
  const scoreNote = r.diagnosis && typeof r.diagnosis.score === "number"
    ? ` ARGUS is ${r.confidence === "high" ? "confident" : "not confident"} in this diagnosis (score ${r.diagnosis.score.toFixed(2)} of 1.00).`
    : "";
  return `This is a ${confWord} incident. ${r.root_cause_service} is failing${failure}.${cascadeNote}${scoreNote}`;
}

function rootCauseProse(r) {
  if (r.answer_type !== "incident" || !r.confident_cause_found) {
    return "Root cause could not be conclusively established from the available evidence.";
  }
  const d = r.diagnosis || {};
  const errCount = d.root_errors != null ? d.root_errors : null;
  const volume = errCount != null ? ` It had ${errCount} error${errCount === 1 ? "" : "s"} in the last 5 minutes, ${errCount >= 15 ? "well above" : "against"} the evidence ARGUS requires for full confidence.` : "";
  return `${r.root_cause_service} is named the root cause because, among every service currently failing, it's the only one that isn't itself depending on something else that's also failing -- everything downstream of it is failing too, but nothing it depends on is.${volume}`;
}

function pathProse(r) {
  const path = r.trace_path || [];
  const affected = r.affected_nodes || [];
  if (!path.length) return NA;
  const entry = path[0];
  const root = path[path.length - 1];
  const routeNote = path.length > 1
    ? `The failure enters the system at ${entry} and bottoms out at ${root} -- that's where it actually originates.`
    : `${root} is where the failure originates; nothing else sits between it and the entry point.`;
  const impactNote = affected.length
    ? ` ${affected.length} other service${affected.length === 1 ? " is" : "s are"} affected as a result: ${join2(affected.map((a) => a.name))}, each because ${affected.length === 1 ? "it calls" : "they call"} ${root} directly or indirectly -- none of them has a separate problem of its own.`
    : " No other service is affected.";
  return routeNote + impactNote;
}

function timelineProse(r) {
  const t = r.timeline || [];
  if (!t.length) return NA;
  if (t.length === 1) return `The only recorded event is "${t[0].label}" at ${t[0].time}.`;
  return `The first sign of trouble was "${t[0].label}" at ${t[0].time}; ARGUS's investigation concluded with "${t[t.length - 1].label}" at ${t[t.length - 1].time}.`;
}

function evidenceProse(r) {
  const logs = r.evidence_logs || [];
  if (!logs.length) return "No specific log lines were cited to support this diagnosis.";
  const services = [...new Set(logs.map((l) => l.service))];
  return `ARGUS's diagnosis is backed by ${logs.length} log line${logs.length === 1 ? "" : "s"}, ${services.length === 1 ? `all from ${services[0]}` : `from ${join2(services)}`}. These are the ones that most directly support the diagnosis:`;
}

function relevanceBucket(v) {
  if (v == null) return null;
  if (v >= 0.6) return "closely matches";
  if (v >= 0.3) return "loosely matches";
  return "only weakly matches";
}

function codeProse(r) {
  if (!r.relevant_code) {
    return "ARGUS didn't find code that clearly matches this failure -- there's nothing to show here beyond the log evidence above.";
  }
  const d = r.diagnosis || {};
  const bucket = relevanceBucket(d.raw_relevance);
  const relNote = bucket
    ? ` Match strength: the retrieved code ${bucket} the error text (relevance ${d.raw_relevance.toFixed(2)} of 1.00)${bucket === "only weakly matches" ? " -- treat this as a starting point, not certainty" : ""}.`
    : "";
  return `The code below, from ${r.root_cause_service}'s own source, is what ARGUS matched against the errors above.${relNote}`;
}

function trustChecks(r) {
  const logsOk = (r.evidence_logs || []).length > 0;
  const graphOk = (r.trace_path || []).length > 0;
  const codeOk = !!r.relevant_code;
  const fixPresent = !!r.recommended_fix;
  return [
    { key: "LOG", ok: logsOk, label: "LOG VERIFIED",
      sentence: logsOk
        ? `Every log line cited above is a real line ARGUS read from the log file (${r.evidence_logs.length} cited), not invented.`
        : "No log lines were cited for this answer -- there's nothing to verify." },
    { key: "GRAPH", ok: graphOk, label: "GRAPH VERIFIED",
      sentence: graphOk
        ? `${r.root_cause_service || "The service"} and the path ${(r.trace_path || []).join(" → ")} both exist in the real dependency graph ARGUS built from your code.`
        : "No failure path was established for this answer -- there's nothing to verify." },
    { key: "CODE", ok: codeOk, label: "CODE VERIFIED",
      sentence: codeOk
        ? `The file and line numbers shown below are real, current lines in ${r.root_cause_service}'s own source, not guessed.`
        : "No matching code was retrieved for this answer -- there's nothing to verify." },
    { key: "FIX", ok: fixPresent, label: "FIX VERIFIED", notApplicable: !fixPresent,
      sentence: fixPresent
        ? "The proposed change below was checked against the retrieved source before being shown -- its removed/context lines are copied verbatim from the real code."
        : "Not applicable -- ARGUS didn't have a close enough code match to propose a fix this time." },
  ];
}

function confidenceProse(r) {
  const d = r.diagnosis || {};
  if (r.answer_type !== "incident") return null;
  if (d.confidence_reason) return d.confidence_reason;
  return r.confidence === "high"
    ? "Evidence volume was strong and there was only one plausible cause."
    : "The evidence available doesn't clear ARGUS's bar for a high-confidence answer.";
}

function fixProse(r) {
  if (!r.recommended_fix) {
    return `ARGUS did not find a code change it could confidently recommend for this incident.${r.root_cause_service ? ` A developer should review ${r.root_cause_service}'s code directly.` : ""}`;
  }
  const adds = r.recommended_fix.lines.filter((l) => l.kind === "add").length;
  const removes = r.recommended_fix.lines.filter((l) => l.kind === "remove").length;
  return `ARGUS proposes the following change to ${r.recommended_fix.filename} -- ${removes} line${removes === 1 ? "" : "s"} removed, ${adds} line${adds === 1 ? "" : "s"} added, checked against the real source before being shown.`;
}

function safetyBullets(r) {
  const out = [];
  if (r.answer_type !== "incident") {
    out.push("There's no active incident here, so no fix safety concerns apply.");
    return out;
  }
  if (r.confidence === "low") {
    out.push("Confidence is low -- more investigation is recommended before acting on this diagnosis.");
  } else {
    out.push("Confidence is high, so no further investigation should be necessary before you start looking at the code.");
  }
  const affected = r.affected_nodes || [];
  if (affected.length) {
    out.push(`${affected.length} other service${affected.length === 1 ? "" : "s"} depend${affected.length === 1 ? "s" : ""} on ${r.root_cause_service} and should recover automatically once it's fixed: ${join2(affected.map((a) => a.name))}.`);
  }
  if (!r.recommended_fix) {
    out.push("No fix was proposed, so there's nothing to review yet -- treat the evidence above as a pointer to the right file, not a ready patch.");
  }
  return out;
}

function nextActions(r) {
  if (r.answer_type === "healthy") return [`Nothing to do -- ${r.mode === "specific" ? r.target : "the system"} has no active errors right now.`];
  if (r.answer_type === "unknown_service") return [`Double-check the service name "${r.target}" -- it doesn't match anything in the current dependency graph.`];
  if (r.answer_type !== "incident" || !r.root_cause_service) return ["Gather more evidence -- ARGUS didn't have enough to name a cause."];
  const out = [];
  if (r.relevant_code) out.push(`Review ${r.root_cause_service}'s code shown above (${r.relevant_code.filename}).`);
  if ((r.evidence_logs || []).length) out.push(`Check the ${r.evidence_logs.length} cited log line${r.evidence_logs.length === 1 ? "" : "s"} for the exact failure pattern.`);
  if ((r.affected_nodes || []).length) out.push(`Confirm ${join2(r.affected_nodes.map((a) => a.name))} recover${r.affected_nodes.length === 1 ? "s" : ""} once ${r.root_cause_service} is fixed.`);
  if (r.recommended_fix) out.push("Review the recommended fix above before applying it -- ARGUS never applies fixes itself.");
  else out.push("No automatic fix was proposed -- write and test a fix yourself before deploying.");
  if (r.confidence === "low") out.push("Investigate further before treating this as settled -- confidence is low.");
  return out.slice(0, 5);
}

// ---- layout pieces ----------------------------------------------------------
const sectionLabelStyle = { fontFamily: "var(--font-ui)", fontSize: "var(--text-caption)", color: "var(--ink-subtle)", margin: 0, textTransform: "uppercase", letterSpacing: "0.04em" };
const proseStyle = { margin: 0, fontFamily: "var(--font-ui)", fontSize: "var(--text-body-sm)", lineHeight: 1.55, color: "var(--ink)" };

function Section({ n, title, children }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-sm)", padding: "var(--space-md) 0", borderTop: n === 1 ? "none" : "1px solid var(--hairline)" }}>
      <p style={sectionLabelStyle}>{n}. {title}</p>
      {children}
    </div>
  );
}

export default function DetailsModal({ response: r, ollamaModel, onClose, onCitationClick, onServiceClick }) {
  const { Icon, CodeBlock, CitationChip, ConfidenceTag, ActivityBadge } = window.ARGUSDesignSystem_7fa82c;
  if (!r) return null;
  const d = r.diagnosis || {};
  const checks = trustChecks(r);
  const confSentence = confidenceProse(r);
  const model = ollamaModel || "mistral";

  return (
    <div
      role="dialog" aria-modal="true"
      onClick={onClose}
      style={{ position: "fixed", inset: 0, background: "rgba(1,1,2,0.65)", zIndex: 60, display: "flex", alignItems: "center", justifyContent: "center", padding: "var(--space-lg)" }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background: "var(--surface-3)", border: "1px solid var(--hairline)", borderRadius: "var(--radius-lg)",
          padding: "var(--space-lg)", width: "min(780px, 100%)", maxHeight: "86vh", overflow: "auto",
          display: "flex", flexDirection: "column", gap: "var(--space-xs)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", position: "sticky", top: 0, background: "var(--surface-3)", paddingBottom: "var(--space-sm)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-sm)" }}>
            <span className="argus-card-title">Incident details</span>
            {r.answer_type === "incident" && <ConfidenceTag level={r.confidence || "high"} />}
            {d.activity && <ActivityBadge activity={d.activity} lastErrorAgeS={d.last_error_age_s} />}
          </div>
          <button onClick={onClose} aria-label="Close" style={{ display: "flex", background: "transparent", border: "1px solid var(--hairline)", borderRadius: "var(--radius-xs)", padding: "var(--space-xxs)", color: "var(--ink-subtle)", cursor: "pointer" }}>
            <Icon name="x" size={14} />
          </button>
        </div>

        <Section n={1} title="Incident summary">
          <p style={proseStyle}><strong>Severity:</strong> {severityOf(r)}</p>
          <p style={proseStyle}>{summaryProse(r)}</p>
        </Section>

        <Section n={2} title="Exact root cause">
          <p style={proseStyle}>
            <strong>Service:</strong> {r.root_cause_service || NA}
            {" · "}<strong>Function:</strong> {r.root_cause_function || NA}
            {" · "}<strong>Failure type:</strong> {r.failure_type || NA}
            {" · "}<strong>Confidence:</strong> {r.answer_type === "incident" ? (r.confidence === "high" ? "HIGH" : "LOW") : "N/A"}
          </p>
          <p style={proseStyle}>{rootCauseProse(r)}</p>
        </Section>

        <Section n={3} title="Failure path & blast radius">
          <p style={proseStyle}>{pathProse(r)}</p>
          {(r.trace_path || []).length > 0 && (
            <div className="argus-mono" style={{ fontSize: "var(--text-mono)", color: "var(--brand)", whiteSpace: "pre" }}>
              {r.trace_path.join("\n     ↓\n")}
              {"\n     ↓\nROOT CAUSE"}
            </div>
          )}
          {(r.affected_nodes || []).length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xxs)" }}>
              {r.affected_nodes.map((a) => (
                <button key={a.id} onClick={() => onServiceClick && onServiceClick(a.id)} style={{ textAlign: "left", background: "var(--surface-2)", border: "1px solid var(--hairline)", borderRadius: "var(--radius-sm)", padding: "var(--space-xs) var(--space-sm)", cursor: "pointer" }}>
                  <span className="argus-mono" style={{ color: "var(--brand)" }}>{a.name}</span>
                  <span className="argus-body-sm" style={{ marginLeft: "var(--space-sm)", color: "var(--ink-subtle)" }}>{a.note}</span>
                </button>
              ))}
            </div>
          )}
        </Section>

        <Section n={4} title="Incident timeline">
          <p style={proseStyle}>{timelineProse(r)}</p>
          {(r.timeline || []).length > 0 && (
            <div className="argus-body-sm" style={{ display: "flex", flexDirection: "column", gap: "var(--space-xxs)" }}>
              {r.timeline.map((e, i) => (
                <span key={i}><span className="argus-mono" style={{ color: "var(--ink-subtle)" }}>{e.time}</span> — {e.label}</span>
              ))}
            </div>
          )}
        </Section>

        <Section n={5} title="Evidence">
          <p style={proseStyle}>{evidenceProse(r)}</p>
          {(r.evidence_logs || []).length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xxs)" }}>
              {r.evidence_logs.map((l) => (
                <CitationChip key={l.id} label={`${l.time} · ${l.service} · ${l.severity} · ${l.text}`} onClick={() => onCitationClick && onCitationClick(l)} style={{ justifyContent: "flex-start", textAlign: "left" }} />
              ))}
            </div>
          )}
        </Section>

        <Section n={6} title="Code responsible">
          <p style={proseStyle}>{codeProse(r)}</p>
          {r.relevant_code && (
            <>
              <p style={proseStyle}><strong>File:</strong> {r.relevant_code.filename} {r.root_cause_function ? <>{"→ "}<strong>Function:</strong> {r.root_cause_function}{" "}</> : null}{" → "}<strong>Lines:</strong> {r.relevant_code.start_line}–{r.relevant_code.start_line + r.relevant_code.lines.length - 1}</p>
              <CodeBlock lines={r.relevant_code.lines} filename={r.relevant_code.filename} startLine={r.relevant_code.start_line} />
            </>
          )}
        </Section>

        <Section n={7} title="Why should I trust this?">
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xs)" }}>
            {checks.map((c) => (
              <p key={c.key} style={proseStyle}>
                <span style={{ color: c.notApplicable ? "var(--ink-subtle)" : c.ok ? "var(--success)" : "var(--critical)" }}>
                  {c.notApplicable ? "—" : c.ok ? "✓" : "✗"} {c.label}
                </span>
                {" — "}{c.sentence}
              </p>
            ))}
          </div>
          {r.answer_type === "incident" && (
            <p style={proseStyle}><strong>Confidence: {r.confidence === "high" ? "HIGH" : "LOW"}</strong> — {confSentence}</p>
          )}
        </Section>

        <Section n={8} title="Recommended fix">
          <p style={proseStyle}>{fixProse(r)}</p>
          {r.recommended_fix && <CodeBlock diff lines={r.recommended_fix.lines} filename={r.recommended_fix.filename} />}
          <p style={{ ...proseStyle, fontWeight: 600, color: "var(--brand)" }}>RECOMMENDATION — DEVELOPER REVIEW REQUIRED</p>
        </Section>

        <Section n={9} title="Fix safety check">
          {safetyBullets(r).map((s, i) => <p key={i} style={proseStyle}>{s}</p>)}
        </Section>

        <Section n={10} title="Next actions">
          <div style={{ display: "flex", flexDirection: "column", gap: "var(--space-xxs)" }}>
            {nextActions(r).map((a, i) => <p key={i} style={proseStyle}>{"☐ "}{a}</p>)}
          </div>
        </Section>

        <Section n={11} title="ARGUS investigation flow">
          <p style={proseStyle}>This is the same pipeline that produced this report — the code decided the root cause and confidence; the model only wrote the explanation above.</p>
          <div className="argus-mono" style={{ fontSize: "var(--text-mono)", color: "var(--ink-subtle)", whiteSpace: "pre" }}>
            {`LOGS\n  ↓\nANOMALY DETECTION\n  ↓\nTF-IDF CODE RETRIEVAL\n  ↓\nDEPENDENCY GRAPH\n  ↓\n${model}\n  ↓\nCLAIM VALIDATION\n  ↓\nVERIFIED RCA`}
          </div>
        </Section>

        <p className="argus-caption" style={{ color: "var(--ink-tertiary)", margin: "var(--space-sm) 0 0" }}>
          ARGUS does not guarantee zero hallucinations. This view shows only what the system actually computed, and says so plainly wherever it didn't have enough evidence.
        </p>
      </div>
    </div>
  );
}
