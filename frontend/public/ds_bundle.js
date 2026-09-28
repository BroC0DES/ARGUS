/* @ds-bundle: {"format":4,"namespace":"ARGUSDesignSystem_7fa82c","components":[{"name":"AgentCard","sourcePath":"components/app/AgentCard.jsx"},{"name":"AppHeader","sourcePath":"components/app/AppHeader.jsx"},{"name":"BlastRadiusPanel","sourcePath":"components/app/BlastRadiusPanel.jsx"},{"name":"ChatPanel","sourcePath":"components/app/ChatPanel.jsx"},{"name":"IncidentReport","sourcePath":"components/app/IncidentReport.jsx"},{"name":"IncidentTimeline","sourcePath":"components/app/IncidentTimeline.jsx"},{"name":"LogStream","sourcePath":"components/app/LogStream.jsx"},{"name":"NavDrawer","sourcePath":"components/app/NavDrawer.jsx"},{"name":"NodeDetailPanel","sourcePath":"components/app/NodeDetailPanel.jsx"},{"name":"StatGrid","sourcePath":"components/app/StatGrid.jsx"},{"name":"StatusStrip","sourcePath":"components/app/StatusStrip.jsx"},{"name":"ThinkingIndicator","sourcePath":"components/app/ThinkingIndicator.jsx"},{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"CitationChip","sourcePath":"components/core/CitationChip.jsx"},{"name":"CodeBlock","sourcePath":"components/core/CodeBlock.jsx"},{"name":"ConfidenceTag","sourcePath":"components/core/ConfidenceTag.jsx"},{"name":"Icon","sourcePath":"components/core/Icon.jsx"},{"name":"StatusDot","sourcePath":"components/core/StatusDot.jsx"},{"name":"TabSwitch","sourcePath":"components/core/TabSwitch.jsx"},{"name":"TextInput","sourcePath":"components/core/TextInput.jsx"},{"name":"ServiceGraph","sourcePath":"components/graph/ServiceGraph.jsx"},{"name":"ServiceNode","sourcePath":"components/graph/ServiceNode.jsx"}],"sourceHashes":{"components/app/AgentCard.jsx":"c09acb049734","components/app/AppHeader.jsx":"e53d7e23166a","components/app/BlastRadiusPanel.jsx":"7712d706eec7","components/app/ChatPanel.jsx":"d7713379ba2d","components/app/IncidentReport.jsx":"f0cafcb43bd0","components/app/IncidentTimeline.jsx":"06553c222484","components/app/LogStream.jsx":"239e76532d32","components/app/NavDrawer.jsx":"0385cd817aea","components/app/NodeDetailPanel.jsx":"959af96c6172","components/app/StatGrid.jsx":"de617f4ff21c","components/app/StatusStrip.jsx":"7bb05d41d855","components/app/ThinkingIndicator.jsx":"6c77efa4dfc9","components/core/Badge.jsx":"b7878a5028b8","components/core/Button.jsx":"045b36a829a3","components/core/CitationChip.jsx":"069e5181a1bd","components/core/CodeBlock.jsx":"38031892882e","components/core/ConfidenceTag.jsx":"efeeb8529662","components/core/Icon.jsx":"541da175844a","components/core/StatusDot.jsx":"2eb69fc0bc8c","components/core/TabSwitch.jsx":"bb3536d25414","components/core/TextInput.jsx":"d711cf611d6b","components/graph/ServiceGraph.jsx":"c67c644a4a39","components/graph/ServiceNode.jsx":"ffb87665324f","ui_kits/console/ConsoleApp.jsx":"2355edc2de3c","ui_kits/console/consoleData.js":"bb82363159fb"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.ARGUSDesignSystem_7fa82c = window.ARGUSDesignSystem_7fa82c || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/app/AgentCard.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * One labeled card inside an agent response (DESIGN.md §9.10). Agent answers
 * render as Root Cause / Evidence / Code / Fix cards, not one paragraph.
 */
function AgentCard({
  label,
  index = 0,
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)",
      background: "var(--surface-1)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-lg)",
      padding: "var(--space-lg)",
      animation: `argus-card-in var(--dur-panel) var(--ease) both`,
      animationDelay: `calc(var(--stagger-card) * ${index})`,
      ...style
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)"
    }
  }, label), children);
}
Object.assign(__ds_scope, { AgentCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/AgentCard.jsx", error: String((e && e.message) || e) }); }

// components/app/IncidentTimeline.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const dotColor = {
  error: "var(--critical)",
  warn: "var(--brand)",
  info: "var(--success)"
};

/** Incident timeline strip (DESIGN.md §9.7 addendum) — first anomaly, escalation, root cause. */
function IncidentTimeline({
  events = [],
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      alignItems: "flex-start",
      ...style
    }
  }), events.map((e, i) => /*#__PURE__*/React.createElement(React.Fragment, {
    key: i
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: "var(--space-xs)",
      minWidth: 108
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 8,
      height: 8,
      borderRadius: "var(--radius-pill)",
      background: dotColor[e.severity] || "var(--ink-tertiary)"
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "argus-caption",
    style: {
      textAlign: "center",
      color: "var(--ink-muted)"
    }
  }, e.label), /*#__PURE__*/React.createElement("span", {
    className: "argus-mono",
    style: {
      fontSize: "var(--text-caption)",
      color: "var(--ink-tertiary)"
    }
  }, e.time)), i < events.length - 1 && /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      height: 1,
      background: "var(--hairline)",
      marginTop: 4
    }
  }))));
}
Object.assign(__ds_scope, { IncidentTimeline });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/IncidentTimeline.jsx", error: String((e && e.message) || e) }); }

// components/app/StatGrid.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Incident stat grid (DESIGN.md §9.7.3). Real CSS Grid, --space-md gutters.
 * Every value is clickable through to its source log line — no number ships
 * without a working source link.
 */
function StatGrid({
  stats = [],
  onStatClick,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "grid",
      gap: "var(--gap-stat-grid)",
      gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
      ...style
    }
  }), stats.map(s => /*#__PURE__*/React.createElement("button", {
    key: s.label,
    onClick: () => onStatClick && onStatClick(s),
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)",
      alignItems: "flex-start",
      textAlign: "left",
      padding: "var(--space-md)",
      background: "var(--surface-2)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-md)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)"
    }
  }, s.label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      fontWeight: 700,
      color: s.tone === "critical" ? "var(--critical)" : "var(--ink)"
    }
  }, s.value))));
}
Object.assign(__ds_scope, { StatGrid });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/StatGrid.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const base = {
  display: "inline-flex",
  alignItems: "center",
  justifyContent: "center",
  gap: "var(--space-xs)",
  fontFamily: "var(--font-ui)",
  fontSize: "var(--text-button)",
  fontWeight: "var(--fw-button)",
  lineHeight: "var(--lh-button)",
  borderRadius: "var(--radius-md)",
  cursor: "pointer",
  transition: "background var(--dur-chrome) var(--ease), border-color var(--dur-chrome) var(--ease), color var(--dur-chrome) var(--ease), opacity var(--dur-chrome) var(--ease)",
  whiteSpace: "nowrap",
  textDecoration: "none"
};
const sizes = {
  sm: {
    padding: "var(--space-xxs) var(--space-sm)",
    height: 28
  },
  md: {
    padding: "var(--space-xs) var(--space-md)",
    height: 32
  },
  lg: {
    padding: "var(--space-sm) var(--space-lg)",
    height: 40
  }
};
const variants = {
  primary: {
    rest: {
      background: "var(--brand)",
      color: "var(--canvas)",
      border: "1px solid var(--brand)"
    },
    hover: {
      background: "var(--brand-hover)",
      borderColor: "var(--brand-hover)"
    }
  },
  secondary: {
    rest: {
      background: "var(--surface-2)",
      color: "var(--ink)",
      border: "1px solid var(--hairline)"
    },
    hover: {
      background: "var(--surface-3)",
      borderColor: "var(--hairline-strong)"
    }
  },
  tertiary: {
    rest: {
      background: "transparent",
      color: "var(--brand)",
      border: "1px solid transparent"
    },
    hover: {
      color: "var(--brand-hover)"
    }
  }
};

/** Primary / secondary / tertiary button. One primary per screen, max (DESIGN.md §7). */
function Button({
  variant = "secondary",
  size = "md",
  disabled = false,
  icon = null,
  iconAfter = null,
  as = "button",
  style,
  children,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const v = variants[variant] || variants.secondary;
  const Tag = as;
  return /*#__PURE__*/React.createElement(Tag, _extends({}, rest, {
    disabled: Tag === "button" ? disabled : undefined,
    "aria-disabled": disabled || undefined,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      ...base,
      ...sizes[size],
      ...v.rest,
      ...(hover && !disabled ? v.hover : null),
      ...(disabled ? {
        color: "var(--ink-tertiary)",
        cursor: "not-allowed",
        opacity: 0.6
      } : null),
      ...style
    }
  }), icon, children, iconAfter);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Icon.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Lucide glyph wrapper. Requires the Lucide UMD script on the page:
 * <script src="https://unpkg.com/lucide@0.544.0/dist/umd/lucide.js"></script>
 * Stroke inherits currentColor, so color comes from the surrounding ink token.
 */
function Icon({
  name,
  size = 16,
  strokeWidth = 1.75,
  style,
  ...rest
}) {
  const ref = React.useRef(null);
  React.useEffect(() => {
    const el = ref.current;
    if (!el || !window.lucide) return;
    el.innerHTML = "";
    const slot = document.createElement("i");
    slot.setAttribute("data-lucide", name);
    el.appendChild(slot);
    window.lucide.createIcons({
      root: el,
      attrs: {
        width: size,
        height: size,
        "stroke-width": strokeWidth
      }
    });
  }, [name, size, strokeWidth]);
  return /*#__PURE__*/React.createElement("span", _extends({}, rest, {
    ref: ref,
    "aria-hidden": "true",
    style: {
      display: "inline-flex",
      width: size,
      height: size,
      flex: "0 0 auto",
      ...style
    }
  }));
}
Object.assign(__ds_scope, { Icon });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Icon.jsx", error: String((e && e.message) || e) }); }

// components/core/CitationChip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Evidence citation chip (DESIGN.md §9.7.5) — clickable to its log line. */
function CitationChip({
  label,
  active = false,
  onClick,
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  return /*#__PURE__*/React.createElement("button", _extends({}, rest, {
    onClick: onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "var(--space-xxs)",
      padding: "var(--space-xxs) var(--space-sm)",
      borderRadius: "var(--radius-pill)",
      background: active ? "var(--tint-brand-10)" : "var(--surface-2)",
      border: `1px solid ${active || hover ? "var(--hairline-strong)" : "var(--hairline)"}`,
      color: active ? "var(--brand)" : hover ? "var(--ink)" : "var(--ink-muted)",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-caption)",
      cursor: "pointer",
      whiteSpace: "nowrap",
      transition: "color var(--dur-chrome) var(--ease), border-color var(--dur-chrome) var(--ease), background var(--dur-chrome) var(--ease)",
      ...style
    }
  }), /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "quote",
    size: 12
  }), label);
}
Object.assign(__ds_scope, { CitationChip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/CitationChip.jsx", error: String((e && e.message) || e) }); }

// components/core/CodeBlock.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Shared code block (DESIGN.md §9.9). Diff variant tints removed/added lines at
 * 8%; text stays --ink — tint alone carries the meaning.
 */
function CodeBlock({
  lines = [],
  diff = false,
  showLineNumbers = true,
  startLine = 1,
  filename = null,
  highlightIndices = [],
  onLineClick,
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const rows = lines.map(l => typeof l === "string" ? {
    text: l
  } : l);
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      position: "relative",
      background: "var(--surface-2)",
      border: "1px solid var(--hairline-tertiary)",
      borderRadius: "var(--radius-sm)",
      padding: "var(--space-md)",
      overflow: "auto",
      ...style
    }
  }), filename && /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)",
      marginBottom: "var(--space-xs)"
    }
  }, filename), /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      lineHeight: "var(--lh-mono)"
    }
  }, rows.map((row, i) => {
    const kind = diff ? row.kind : null;
    const highlighted = !diff && highlightIndices.indexOf(i) !== -1;
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      onClick: onLineClick ? () => onLineClick(i) : undefined,
      style: {
        display: "flex",
        gap: "var(--space-md)",
        background: kind === "add" ? "var(--tint-success-08)" : kind === "remove" ? "var(--tint-critical-08)" : highlighted ? "var(--tint-brand-10)" : "transparent",
        margin: "0 calc(var(--space-md) * -1)",
        padding: "0 var(--space-md)",
        cursor: onLineClick ? "pointer" : "auto"
      }
    }, showLineNumbers && /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--ink-tertiary)",
        userSelect: "none",
        minWidth: "2ch",
        textAlign: "right"
      }
    }, diff ? kind === "add" ? "+" : kind === "remove" ? "−" : startLine + i : startLine + i), /*#__PURE__*/React.createElement("span", {
      style: {
        color: "var(--ink)",
        whiteSpace: "pre"
      }
    }, row.text));
  })), /*#__PURE__*/React.createElement("button", {
    "aria-label": "Copy",
    style: {
      position: "absolute",
      top: "var(--space-xs)",
      right: "var(--space-xs)",
      display: "flex",
      padding: "var(--space-xxs)",
      cursor: "pointer",
      background: "var(--surface-3)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-xs)",
      color: "var(--ink-subtle)",
      opacity: hover ? 1 : 0,
      transition: "opacity var(--dur-chrome) var(--ease)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "copy",
    size: 14
  })));
}
Object.assign(__ds_scope, { CodeBlock });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/CodeBlock.jsx", error: String((e && e.message) || e) }); }

// components/core/ConfidenceTag.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Root-cause confidence tag (DESIGN.md §9.7.4). Never hidden — this is the
 * product's core trust signal.
 */
function ConfidenceTag({
  level = "high",
  style,
  ...rest
}) {
  const high = level === "high";
  return /*#__PURE__*/React.createElement("span", _extends({}, rest, {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "var(--space-xxs)",
      padding: "2px var(--space-xs)",
      borderRadius: "var(--radius-pill)",
      background: high ? "var(--tint-success-08)" : "var(--tint-brand-10)",
      border: "1px solid var(--hairline)",
      color: high ? "var(--success)" : "var(--brand)",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      fontWeight: 500,
      whiteSpace: "nowrap",
      ...style
    }
  }), high ? "High" : "Needs review", /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: high ? "check" : "alert-triangle",
    size: 12
  }));
}
Object.assign(__ds_scope, { ConfidenceTag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/ConfidenceTag.jsx", error: String((e && e.message) || e) }); }

// components/core/ActivityBadge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Whether the underlying anomaly is still producing errors right now, or has
 * gone quiet -- orthogonal to ConfidenceTag (which is about certainty, not
 * recency), so it never touches the score's color or wording: a fixed
 * neutral tone, distinguished only by the pulsing dot (DESIGN.md §9.13 --
 * pulses only when something is happening right now). Renders nothing when
 * there's no activity signal at all (no root cause to time).
 */
function ActivityBadge({
  activity = null,
  lastErrorAgeS = null,
  style,
  ...rest
}) {
  if (!activity) return null;
  const minutes = Math.max(0, Math.round((lastErrorAgeS || 0) / 60));
  const label = activity === "ongoing" ? "ongoing" : `stopped ${minutes} min ago`;
  return /*#__PURE__*/React.createElement(__ds_scope.Badge, _extends({}, rest, {
    tone: "neutral",
    dot: true,
    pulsing: activity === "ongoing",
    style
  }), label);
}
Object.assign(__ds_scope, { ActivityBadge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/ActivityBadge.jsx", error: String((e && e.message) || e) }); }

// components/app/ConfidenceExplainer.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const fmtCount = n => String(Math.round(n * 100) / 100);

/**
 * "Why low confidence?" disclosure. Collapsed by default; shows the
 * backend's own confidence_reason sentence verbatim, and -- only when
 * ambiguity between candidates is the reason -- each competing candidate's
 * raw numbers. Renders nothing when there's nothing to explain. Standalone
 * and data-only (reason/competingCandidates/onCandidateClick are plain
 * props) so other panels, e.g. the Validation tab, can reuse it against
 * their own incident data.
 */
function ConfidenceExplainer({
  reason = null,
  competingCandidates = [],
  onCandidateClick,
  defaultOpen = false,
  style,
  ...rest
}) {
  const [open, setOpen] = React.useState(defaultOpen);
  const [hoverId, setHoverId] = React.useState(null);
  const panelId = React.useId();
  if (!reason && competingCandidates.length === 0) return null;
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)",
      ...style
    }
  }), /*#__PURE__*/React.createElement("button", {
    type: "button",
    "aria-expanded": open,
    "aria-controls": panelId,
    onClick: () => setOpen(o => !o),
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "var(--space-xxs)",
      alignSelf: "flex-start",
      padding: 0,
      background: "none",
      border: "none",
      cursor: "pointer",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "chevron-right",
    size: 12,
    style: {
      transform: open ? "rotate(90deg)" : "none",
      transition: "transform var(--dur-chrome) var(--ease)"
    }
  }), "Why low confidence?"), open && /*#__PURE__*/React.createElement("div", {
    id: panelId,
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-sm)",
      padding: "var(--space-sm) var(--space-md)",
      background: "var(--surface-2)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-sm)"
    }
  }, reason && /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-body-sm)",
      color: "var(--ink-muted)"
    }
  }, reason), competingCandidates.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xxs)"
    }
  }, competingCandidates.map(c => /*#__PURE__*/React.createElement("button", {
    key: c.service,
    type: "button",
    onClick: () => onCandidateClick && onCandidateClick(c.service),
    onMouseEnter: () => setHoverId(c.service),
    onMouseLeave: () => setHoverId(prev => prev === c.service ? null : prev),
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-sm)",
      width: "100%",
      textAlign: "left",
      padding: "var(--space-xxs) var(--space-sm)",
      background: hoverId === c.service ? "var(--surface-3)" : "transparent",
      border: `1px solid ${hoverId === c.service ? "var(--hairline-strong)" : "var(--hairline)"}`,
      borderRadius: "var(--radius-xs)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      color: "var(--brand)"
    }
  }, c.service), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)",
      whiteSpace: "nowrap"
    }
  }, `${fmtCount(c.weighted_errors)} errors · ${Math.round(c.share_of_top * 100)}% of top${c.label ? ` · ${c.label}` : ""}`))))));
}
Object.assign(__ds_scope, { ConfidenceExplainer });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/ConfidenceExplainer.jsx", error: String((e && e.message) || e) }); }

// components/app/IncidentReport.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const sectionLabel = {
  fontFamily: "var(--font-ui)",
  fontSize: "var(--text-caption)",
  color: "var(--ink-subtle)",
  margin: 0
};

/** Incident report panel (DESIGN.md §9.7) — the trust centerpiece. */
function IncidentReport({
  incident = null,
  onRootCauseClick,
  onStatClick,
  onCitationClick,
  onCodeClick,
  onExportPostmortem,
  onServiceClick,
  style,
  ...rest
}) {
  const [copied, setCopied] = React.useState(false);
  const wrap = {
    display: "flex",
    flexDirection: "column",
    gap: "var(--gap-inter)",
    background: "var(--surface-1)",
    border: "1px solid var(--hairline)",
    borderRadius: "var(--radius-lg)",
    padding: "var(--space-lg)",
    ...style
  };
  if (!incident) {
    return /*#__PURE__*/React.createElement("section", _extends({}, rest, {
      style: {
        ...wrap,
        alignItems: "center",
        justifyContent: "center",
        minHeight: 200
      }
    }), /*#__PURE__*/React.createElement("p", {
      style: {
        margin: 0,
        display: "flex",
        alignItems: "center",
        gap: "var(--space-xs)",
        fontFamily: "var(--font-ui)",
        fontSize: "var(--text-headline)",
        fontWeight: "var(--fw-headline)",
        letterSpacing: "var(--ls-headline)",
        color: "var(--success)"
      }
    }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
      name: "check",
      size: 24
    }), " No active incidents"));
  }
  const noConfidentCause = incident.confidentCauseFound === false;
  const lowConfidence = incident.confidence === "low";
  const otherIncidents = (incident.incidents || []).filter(i => i.service && i.service !== incident.service);
  const handleExport = async () => {
    if (!onExportPostmortem) return;
    const ok = await onExportPostmortem(incident);
    if (ok) {
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    }
  };
  return /*#__PURE__*/React.createElement("section", _extends({}, rest, {
    style: wrap
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      justifyContent: "space-between",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)",
      flexWrap: "wrap"
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xs)",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-headline)",
      fontWeight: "var(--fw-headline)",
      lineHeight: "var(--lh-headline)",
      letterSpacing: "var(--ls-headline)",
      color: noConfidentCause ? "var(--brand)" : "var(--critical)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "alert-triangle",
    size: 24
  }), noConfidentCause ? "INVESTIGATED — NO CONFIDENT CAUSE IDENTIFIED" : `INCIDENT — ${incident.service}`), /*#__PURE__*/React.createElement(__ds_scope.ActivityBadge, {
    activity: incident.activity,
    lastErrorAgeS: incident.lastErrorAgeS
  })), onExportPostmortem && /*#__PURE__*/React.createElement(__ds_scope.Button, {
    variant: "secondary",
    size: "sm",
    icon: /*#__PURE__*/React.createElement(__ds_scope.Icon, {
      name: copied ? "check" : "file-down",
      size: 14
    }),
    onClick: handleExport
  }, copied ? "Copied" : "Generate postmortem")), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      maxWidth: "var(--measure-prose)",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-subhead)",
      fontWeight: "var(--fw-subhead)",
      lineHeight: "var(--lh-subhead)",
      letterSpacing: "var(--ls-subhead)",
      color: "var(--ink-muted)"
    }
  }, incident.summary), incident.timeline && incident.timeline.length > 0 && /*#__PURE__*/React.createElement(__ds_scope.IncidentTimeline, {
    events: incident.timeline
  }), /*#__PURE__*/React.createElement(__ds_scope.StatGrid, {
    stats: incident.stats || [],
    onStatClick: onStatClick
  }), lowConfidence && /*#__PURE__*/React.createElement(__ds_scope.ConfidenceExplainer, {
    reason: incident.confidenceReason,
    competingCandidates: incident.competingCandidates || [],
    onCandidateClick: onServiceClick
  }), otherIncidents.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: sectionLabel
  }, "Also detected"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xxs)"
    }
  }, otherIncidents.map(inc => /*#__PURE__*/React.createElement("button", {
    key: inc.service,
    type: "button",
    onClick: () => onServiceClick && onServiceClick(inc.service),
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-sm)",
      width: "100%",
      textAlign: "left",
      padding: "var(--space-xs) var(--space-sm)",
      background: "var(--surface-2)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-sm)",
      cursor: "pointer",
      opacity: inc.isMinor ? 0.7 : 1
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xs)",
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      color: inc.isMinor ? "var(--ink-subtle)" : "var(--brand)",
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap"
    }
  }, inc.service), inc.isMinor && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-tertiary)"
    }
  }, "minor")), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xs)",
      flex: "0 0 auto"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.ConfidenceTag, {
    level: inc.confidence || "high"
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)"
    }
  }, inc.score != null ? inc.score.toFixed(2) : ""), /*#__PURE__*/React.createElement(__ds_scope.ActivityBadge, {
    activity: inc.activity,
    lastErrorAgeS: inc.lastErrorAgeS
  })))))), !noConfidentCause && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: sectionLabel
  }, "Root cause"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)",
      flexWrap: "wrap"
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onRootCauseClick,
    style: {
      padding: 0,
      background: "none",
      border: "none",
      cursor: "pointer",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      color: "var(--brand)"
    }
  }, incident.rootCause), /*#__PURE__*/React.createElement(__ds_scope.ConfidenceTag, {
    level: incident.confidence || "high"
  }))), incident.evidence && incident.evidence.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: sectionLabel
  }, noConfidentCause ? "What was checked" : "Evidence"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexWrap: "wrap",
      gap: "var(--space-xs)"
    }
  }, incident.evidence.map(e => /*#__PURE__*/React.createElement(__ds_scope.CitationChip, {
    key: e.id,
    label: e.label,
    onClick: () => onCitationClick && onCitationClick(e)
  })))), noConfidentCause && incident.ruledOut && /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-body-sm)",
      color: "var(--ink-subtle)"
    }
  }, incident.ruledOut), !noConfidentCause && incident.code && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: sectionLabel
  }, "Relevant code"), /*#__PURE__*/React.createElement(__ds_scope.CodeBlock, {
    lines: incident.code.lines,
    filename: incident.code.filename,
    startLine: incident.code.startLine,
    onClick: onCodeClick,
    style: {
      cursor: onCodeClick ? "pointer" : "auto"
    }
  })), !noConfidentCause && incident.fix && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: sectionLabel
  }, "Recommended fix"), /*#__PURE__*/React.createElement(__ds_scope.CodeBlock, {
    diff: true,
    lines: incident.fix.lines,
    filename: incident.fix.filename
  })));
}
Object.assign(__ds_scope, { IncidentReport });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/IncidentReport.jsx", error: String((e && e.message) || e) }); }

// components/core/StatusDot.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const tones = {
  healthy: "var(--success)",
  active: "var(--brand)",
  critical: "var(--critical)",
  idle: "var(--ink-tertiary)"
};

/**
 * 6px state dot. Pulses only when `pulsing` — i.e. something is happening right
 * now (DESIGN.md §9.13). Healthy, idle and resolved dots stay still.
 */
function StatusDot({
  tone = "healthy",
  pulsing = false,
  size = 6,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({}, rest, {
    className: pulsing ? "argus-pulse" : undefined,
    style: {
      display: "inline-block",
      width: size,
      height: size,
      borderRadius: "var(--radius-pill)",
      flex: "0 0 auto",
      background: tones[tone] || tones.idle,
      ...style
    }
  }));
}
Object.assign(__ds_scope, { StatusDot });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/StatusDot.jsx", error: String((e && e.message) || e) }); }

// components/app/BlastRadiusPanel.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Blast-radius list (DESIGN.md addendum) — services impacted by the root cause, not the trace path. */
function BlastRadiusPanel({
  items = [],
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)",
      ...style
    }
  }), items.map(it => /*#__PURE__*/React.createElement("div", {
    key: it.id,
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: "var(--space-sm)",
      padding: "var(--space-md)",
      background: "var(--surface-1)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-lg)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.StatusDot, {
    tone: it.health === "critical" ? "critical" : it.health === "degraded" ? "active" : "healthy",
    style: {
      marginTop: 5
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xxs)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "argus-body-sm",
    style: {
      color: "var(--ink)"
    }
  }, it.name), /*#__PURE__*/React.createElement("span", {
    className: "argus-caption"
  }, it.note)))));
}
Object.assign(__ds_scope, { BlastRadiusPanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/BlastRadiusPanel.jsx", error: String((e && e.message) || e) }); }

// components/app/StatusStrip.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Header status strip (DESIGN.md §9.2). Always visible, even idle — the tool
 * should look like it's watching before a query is asked.
 */
function StatusStrip({
  services = [],
  onSelect,
  style,
  ...rest
}) {
  const [hoverId, setHoverId] = React.useState(null);
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-sm)",
      ...style
    }
  }), services.map(s => /*#__PURE__*/React.createElement("span", {
    key: s.id,
    style: {
      position: "relative",
      display: "flex"
    }
  }, /*#__PURE__*/React.createElement("button", {
    "aria-label": s.name,
    onClick: () => onSelect && onSelect(s.id),
    onMouseEnter: () => setHoverId(s.id),
    onMouseLeave: () => setHoverId(null),
    style: {
      display: "flex",
      padding: 0,
      background: "none",
      border: "none",
      cursor: "pointer",
      borderRadius: "var(--radius-pill)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.StatusDot, {
    tone: s.health === "critical" ? "critical" : s.health === "degraded" ? "active" : "healthy",
    pulsing: !!s.anomaly
  })), hoverId === s.id && /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      top: "calc(100% + var(--space-xs))",
      left: "50%",
      transform: "translateX(-50%)",
      zIndex: 20,
      display: "flex",
      gap: "var(--space-xs)",
      alignItems: "baseline",
      padding: "var(--space-xs) var(--space-sm)",
      background: "var(--surface-3)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-md)",
      whiteSpace: "nowrap"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink)"
    }
  }, s.name), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)"
    }
  }, s.rate)))));
}
Object.assign(__ds_scope, { StatusStrip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/StatusStrip.jsx", error: String((e && e.message) || e) }); }

// components/app/AppHeader.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** App header (DESIGN.md §9.1). 56px, --surface-1, quiet. */
function AppHeader({
  services = [],
  onSelectService,
  onMenuClick,
  right = null,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("header", _extends({}, rest, {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-lg)",
      height: "var(--header-height)",
      flex: "0 0 auto",
      padding: "0 var(--space-lg)",
      background: "var(--surface-1)",
      borderBottom: "1px solid var(--hairline)",
      ...style
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-md)"
    }
  }, onMenuClick && /*#__PURE__*/React.createElement("button", {
    "aria-label": "Open sections",
    onClick: onMenuClick,
    style: {
      display: "flex",
      padding: "var(--space-xxs)",
      background: "transparent",
      border: "none",
      cursor: "pointer",
      color: "var(--ink-subtle)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "menu",
    size: 18
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-body-sm)",
      fontWeight: 600,
      letterSpacing: "0.12em",
      color: "var(--ink)"
    }
  }, "ARGUS")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-lg)"
    }
  }, right, /*#__PURE__*/React.createElement(__ds_scope.StatusStrip, {
    services: services,
    onSelect: onSelectService
  })));
}
Object.assign(__ds_scope, { AppHeader });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/AppHeader.jsx", error: String((e && e.message) || e) }); }

// components/app/ThinkingIndicator.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const LABELS = ["Analyzing logs…", "Tracing dependencies…", "Reading call sites…", "Ranking candidates…"];

/**
 * Chat "thinking" state (DESIGN.md §9.10). The pulse sells "actively working";
 * the rotating text explains what.
 */
function ThinkingIndicator({
  labels = LABELS,
  interval = 1600,
  style,
  ...rest
}) {
  const [i, setI] = React.useState(0);
  React.useEffect(() => {
    const id = setInterval(() => setI(n => (n + 1) % labels.length), interval);
    return () => clearInterval(id);
  }, [labels, interval]);
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xs)",
      ...style
    }
  }), /*#__PURE__*/React.createElement(__ds_scope.StatusDot, {
    tone: "active",
    pulsing: true,
    size: 8
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)"
    }
  }, labels[i]));
}
Object.assign(__ds_scope, { ThinkingIndicator });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/ThinkingIndicator.jsx", error: String((e && e.message) || e) }); }

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const tones = {
  neutral: {
    color: "var(--ink-subtle)",
    background: "var(--surface-2)",
    border: "var(--hairline)"
  },
  brand: {
    color: "var(--brand)",
    background: "var(--tint-brand-10)",
    border: "var(--hairline)"
  },
  success: {
    color: "var(--success)",
    background: "var(--tint-success-08)",
    border: "var(--hairline)"
  },
  critical: {
    color: "var(--critical)",
    background: "var(--tint-critical-08)",
    border: "var(--hairline)"
  }
};

/** Caption-sized badge: node counts, "needs review", "cited", error labels. */
function Badge({
  tone = "neutral",
  shape = "rect",
  dot = false,
  pulsing = false,
  style,
  children,
  ...rest
}) {
  const t = tones[tone] || tones.neutral;
  return /*#__PURE__*/React.createElement("span", _extends({}, rest, {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "var(--space-xxs)",
      padding: "2px var(--space-xs)",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      lineHeight: "var(--lh-caption)",
      fontWeight: 500,
      color: t.color,
      background: t.background,
      border: `1px solid ${t.border}`,
      borderRadius: shape === "pill" ? "var(--radius-pill)" : "var(--radius-xs)",
      whiteSpace: "nowrap",
      ...style
    }
  }), dot && /*#__PURE__*/React.createElement(__ds_scope.StatusDot, {
    tone: tone === "success" ? "healthy" : tone === "critical" ? "critical" : tone === "brand" ? "active" : "idle",
    pulsing: pulsing
  }), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/app/LogStream.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Monospace log stream (DESIGN.md §9.5). Keeps populating even at idle. */
function LogStream({
  lines = [],
  flashId = null,
  onLineClick,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      flexDirection: "column",
      background: "var(--surface-1)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-lg)",
      padding: "var(--space-lg)",
      overflow: "auto",
      ...style
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--gap-log-line)"
    }
  }, lines.map(l => /*#__PURE__*/React.createElement("div", {
    key: l.id,
    id: `log-${l.id}`,
    onClick: () => onLineClick && onLineClick(l.id),
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: "var(--space-sm)",
      padding: "2px var(--space-xs)",
      margin: "0 calc(var(--space-xs) * -1)",
      borderRadius: "var(--radius-xs)",
      background: l.cited ? "var(--tint-brand-10)" : "transparent",
      animation: flashId === l.id ? "argus-flash 600ms var(--ease)" : undefined,
      cursor: onLineClick ? "pointer" : "default"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.StatusDot, {
    tone: l.severity === "error" ? "critical" : l.severity === "warn" ? "active" : "healthy",
    style: {
      transform: "translateY(-2px)"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      color: "var(--ink-tertiary)",
      flex: "0 0 auto"
    }
  }, l.time), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      lineHeight: "var(--lh-mono)",
      color: l.severity === "error" ? "var(--ink)" : "var(--ink-muted)",
      flex: 1,
      minWidth: 0
    }
  }, l.text), l.cited && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: "brand"
  }, "cited")))));
}
Object.assign(__ds_scope, { LogStream });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/LogStream.jsx", error: String((e && e.message) || e) }); }

// components/app/NavDrawer.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Hamburger-triggered slide-out section drawer. Sits under the header; a scrim
 * covers the rest of the app. Escape or the scrim closes it.
 */
function NavDrawer({
  open = false,
  items = [],
  activeId,
  onSelect,
  onClose,
  style,
  ...rest
}) {
  React.useEffect(() => {
    if (!open) return;
    const onKey = e => {
      if (e.key === "Escape" && onClose) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  return /*#__PURE__*/React.createElement(React.Fragment, null, open && /*#__PURE__*/React.createElement("div", {
    onClick: onClose,
    style: {
      position: "fixed",
      top: "var(--header-height)",
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(1,1,2,0.6)",
      zIndex: 30
    }
  }), /*#__PURE__*/React.createElement("nav", _extends({}, rest, {
    style: {
      position: "fixed",
      top: "var(--header-height)",
      left: 0,
      bottom: 0,
      width: 240,
      zIndex: 31,
      background: "var(--surface-1)",
      borderRight: "1px solid var(--hairline)",
      display: "flex",
      flexDirection: "column",
      padding: "var(--space-md) 0",
      transform: open ? "translateX(0)" : "translateX(-100%)",
      transition: "transform var(--dur-panel) var(--ease)",
      ...style
    }
  }), items.map(it => {
    const active = it.id === activeId;
    return /*#__PURE__*/React.createElement("button", {
      key: it.id,
      onClick: () => {
        onSelect && onSelect(it.id);
        onClose && onClose();
      },
      style: {
        display: "flex",
        alignItems: "center",
        gap: "var(--space-sm)",
        padding: "var(--space-sm) var(--space-lg)",
        background: active ? "var(--surface-2)" : "transparent",
        border: "none",
        borderLeft: `2px solid ${active ? "var(--brand)" : "transparent"}`,
        cursor: "pointer",
        textAlign: "left",
        color: active ? "var(--ink)" : "var(--ink-muted)",
        fontFamily: "var(--font-ui)",
        fontSize: "var(--text-body-sm)"
      }
    }, it.icon && /*#__PURE__*/React.createElement(__ds_scope.Icon, {
      name: it.icon,
      size: 16
    }), /*#__PURE__*/React.createElement("span", {
      style: {
        flex: 1
      }
    }, it.label), it.badge != null && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
      tone: "critical",
      shape: "pill"
    }, it.badge));
  })));
}
Object.assign(__ds_scope, { NavDrawer });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/NavDrawer.jsx", error: String((e && e.message) || e) }); }

// components/app/NodeDetailPanel.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * Node detail panel (DESIGN.md §9.6). Fixed, 360px, --surface-3, --space-lg
 * padding throughout. Closes on × or Escape — never auto-dismiss on scroll.
 * The bridge line and matches connect the code and logs instead of just
 * listing them side by side.
 */
function NodeDetailPanel({
  open = false,
  service,
  health = "healthy",
  anomaly = false,
  bridge = null,
  code = [],
  filename = null,
  matches = [],
  logs = [],
  onClose,
  style,
  ...rest
}) {
  const [highlightLine, setHighlightLine] = React.useState(null);
  const [highlightLogId, setHighlightLogId] = React.useState(null);
  React.useEffect(() => {
    if (!open) return;
    setHighlightLine(null);
    setHighlightLogId(null);
    const onKey = e => {
      if (e.key === "Escape" && onClose) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, service]);
  if (!open) return null;
  const onLogClick = id => {
    const m = matches.find(x => x.logId === id);
    setHighlightLogId(id);
    setHighlightLine(m ? m.lineIndex : null);
  };
  const onCodeLineClick = lineIndex => {
    const m = matches.find(x => x.lineIndex === lineIndex);
    setHighlightLine(lineIndex);
    setHighlightLogId(m ? m.logId : null);
  };
  const citedLogIds = matches.map(m => m.logId);
  const logsWithCite = logs.map(l => ({
    ...l,
    cited: l.cited || citedLogIds.indexOf(l.id) !== -1
  }));
  return /*#__PURE__*/React.createElement("aside", _extends({}, rest, {
    style: {
      position: "fixed",
      top: "var(--header-height)",
      right: 0,
      bottom: 0,
      width: "var(--detail-panel-width)",
      zIndex: 40,
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-lg)",
      background: "var(--surface-3)",
      borderLeft: "1px solid var(--hairline)",
      borderTopLeftRadius: "var(--radius-lg)",
      borderBottomLeftRadius: "var(--radius-lg)",
      padding: "var(--space-lg)",
      overflow: "auto",
      animation: "argus-slide-in-right var(--dur-panel) var(--ease)",
      ...style
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xs)",
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.StatusDot, {
    tone: health === "critical" ? "critical" : health === "degraded" ? "active" : "healthy",
    pulsing: anomaly,
    size: 8
  }), /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-card-title)",
      fontWeight: "var(--fw-card-title)",
      lineHeight: "var(--lh-card-title)",
      letterSpacing: "var(--ls-card-title)",
      color: "var(--ink)",
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap"
    }
  }, service)), /*#__PURE__*/React.createElement("button", {
    "aria-label": "Close",
    onClick: onClose,
    style: {
      display: "flex",
      padding: "var(--space-xxs)",
      cursor: "pointer",
      background: "transparent",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-xs)",
      color: "var(--ink-subtle)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Icon, {
    name: "x",
    size: 14
  }))), bridge && /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-body-sm)",
      lineHeight: "var(--lh-body-sm)",
      color: "var(--ink-muted)"
    }
  }, bridge)), code.length > 0 && /*#__PURE__*/React.createElement(__ds_scope.CodeBlock, {
    lines: code,
    filename: filename,
    highlightIndices: highlightLine != null ? [highlightLine] : [],
    onLineClick: matches.length > 0 ? onCodeLineClick : undefined
  }), logs.length > 0 && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--ink-subtle)"
    }
  }, "Recent log lines"), /*#__PURE__*/React.createElement(__ds_scope.LogStream, {
    lines: logsWithCite,
    flashId: highlightLogId,
    onLineClick: matches.length > 0 ? onLogClick : undefined,
    style: {
      background: "var(--surface-2)",
      borderColor: "var(--hairline-tertiary)",
      padding: "var(--space-md)"
    }
  })));
}
Object.assign(__ds_scope, { NodeDetailPanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/NodeDetailPanel.jsx", error: String((e && e.message) || e) }); }

// components/core/TabSwitch.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Pill tabs (Chat / Report). Inactive = --ink-subtle on transparent. */
function TabSwitch({
  tabs = [],
  value,
  onChange,
  style,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    role: "tablist",
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xxs)",
      ...style
    }
  }), tabs.map(t => {
    const id = typeof t === "string" ? t : t.id;
    const label = typeof t === "string" ? t : t.label;
    const active = id === value;
    return /*#__PURE__*/React.createElement("button", {
      key: id,
      role: "tab",
      "aria-selected": active,
      onClick: () => onChange && onChange(id),
      style: {
        appearance: "none",
        cursor: "pointer",
        padding: "var(--space-xs) var(--space-md)",
        borderRadius: "var(--radius-pill)",
        border: "1px solid transparent",
        background: active ? "var(--surface-2)" : "transparent",
        color: active ? "var(--ink)" : "var(--ink-subtle)",
        fontFamily: "var(--font-ui)",
        fontSize: "var(--text-button)",
        fontWeight: "var(--fw-button)",
        lineHeight: "var(--lh-button)",
        transition: "background var(--dur-chrome) var(--ease), color var(--dur-chrome) var(--ease)"
      }
    }, label);
  }));
}
Object.assign(__ds_scope, { TabSwitch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/TabSwitch.jsx", error: String((e && e.message) || e) }); }

// components/core/TextInput.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Query box / single-line text input. --space-md internal padding (DESIGN.md §7). */
function TextInput({
  value,
  onChange,
  placeholder,
  mono = false,
  disabled = false,
  icon = null,
  trailing = null,
  style,
  ...rest
}) {
  const [focus, setFocus] = React.useState(false);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: "var(--space-xs)",
      background: "var(--surface-2)",
      border: `1px solid ${focus ? "var(--hairline-strong)" : "var(--hairline)"}`,
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)",
      boxShadow: focus ? "0 0 0 2px var(--brand-focus)" : "none",
      transition: "border-color var(--dur-chrome) var(--ease), box-shadow var(--dur-chrome) var(--ease)",
      opacity: disabled ? 0.6 : 1,
      ...style
    }
  }, icon, /*#__PURE__*/React.createElement("input", _extends({}, rest, {
    value: value,
    onChange: onChange,
    placeholder: placeholder,
    disabled: disabled,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      flex: 1,
      minWidth: 0,
      background: "transparent",
      border: "none",
      outline: "none",
      color: "var(--ink)",
      fontFamily: mono ? "var(--font-mono)" : "var(--font-ui)",
      fontSize: mono ? "var(--text-mono)" : "var(--text-body)",
      lineHeight: mono ? "var(--lh-mono)" : "var(--lh-body)"
    }
  })), trailing);
}
Object.assign(__ds_scope, { TextInput });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/TextInput.jsx", error: String((e && e.message) || e) }); }

// components/app/ChatPanel.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/** Chat panel (DESIGN.md §9.10) with composer and idle prompt. */
function ChatPanel({
  messages = [],
  busy = false,
  value = "",
  onChange,
  onSubmit,
  placeholder = "Ask what's happening in your system",
  style,
  ...rest
}) {
  const empty = messages.length === 0 && !busy;
  return /*#__PURE__*/React.createElement("section", _extends({}, rest, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--gap-inter)",
      minHeight: 0,
      flex: 1,
      ...style
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minHeight: 0,
      overflow: "auto",
      display: "flex",
      flexDirection: "column",
      gap: "var(--gap-inter)",
      justifyContent: empty ? "center" : "flex-start"
    }
  }, empty ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      textAlign: "center",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-body)",
      lineHeight: "var(--lh-body)",
      color: "var(--ink-subtle)"
    }
  }, placeholder) : messages.map((m, i) => m.role === "user" ? /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: "flex",
      justifyContent: "flex-end"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      maxWidth: "80%",
      background: "var(--surface-2)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-md)",
      padding: "var(--space-md)",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-body)",
      lineHeight: "var(--lh-body)",
      color: "var(--ink)"
    }
  }, m.text)) : /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-sm)"
    }
  }, (m.cards || []).map((c, j) => /*#__PURE__*/React.createElement(__ds_scope.AgentCard, {
    key: j,
    label: c.label,
    index: j
  }, c.content)))), busy && /*#__PURE__*/React.createElement(__ds_scope.ThinkingIndicator, null)), /*#__PURE__*/React.createElement("form", {
    onSubmit: e => {
      e.preventDefault();
      onSubmit && onSubmit(value);
    },
    style: {
      flex: "0 0 auto"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.TextInput, {
    value: value,
    onChange: onChange,
    placeholder: placeholder,
    trailing: /*#__PURE__*/React.createElement(__ds_scope.Button, {
      variant: "primary",
      size: "sm",
      type: "submit"
    }, "Ask")
  })));
}
Object.assign(__ds_scope, { ChatPanel });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/app/ChatPanel.jsx", error: String((e && e.message) || e) }); }

// components/graph/ServiceNode.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
/**
 * One service in the dependency graph (DESIGN.md §9.3). Identity and edges are
 * fixed — they mirror real indexed services. Only position is user-movable.
 */
function ServiceNode({
  name,
  rate,
  state = "idle",
  health = "healthy",
  anomaly = false,
  settled = false,
  lowConfidence = false,
  selected = false,
  blastRadius = false,
  onClick,
  onPointerDown,
  style,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const root = state === "root";
  const visited = state === "visited";
  const borderColor = root ? "var(--critical)" : visited || hover || selected ? "var(--brand)" : "var(--hairline)";
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    role: "button",
    tabIndex: 0,
    onClick: onClick,
    onPointerDown: onPointerDown,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xs)",
      minWidth: 168,
      padding: "var(--space-md)",
      position: "relative",
      background: "var(--surface-1)",
      border: `1px ${root && lowConfidence ? "dashed" : "solid"} ${borderColor}`,
      borderRadius: "var(--radius-lg)",
      boxShadow: root ? "0 0 12px -4px var(--critical)" : visited || hover || selected ? "var(--glow-brand)" : "none",
      opacity: settled && !root ? "var(--settled-node-opacity)" : 1,
      cursor: "grab",
      userSelect: "none",
      transition: "border-color var(--dur-hop) var(--ease), box-shadow var(--dur-hop) var(--ease), opacity var(--dur-hop) var(--ease)",
      ...style
    }
  }), blastRadius && /*#__PURE__*/React.createElement("span", {
    title: "Affected by the root cause",
    style: {
      position: "absolute",
      top: -5,
      left: -5,
      width: 10,
      height: 10,
      borderRadius: "var(--radius-pill)",
      background: "var(--brand)",
      opacity: 0.45,
      border: "2px solid var(--surface-1)"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-body-sm)",
      lineHeight: "var(--lh-body-sm)",
      fontWeight: root ? 600 : 400,
      color: root ? "var(--ink)" : "var(--ink-muted)"
    }
  }, name), /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: health === "critical" ? "critical" : health === "degraded" ? "brand" : "success",
    shape: "pill",
    dot: true,
    pulsing: anomaly
  }, rate)), root && lowConfidence && /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--brand)"
    }
  }, "needs review"), root && !lowConfidence && /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "var(--space-xxs)",
      fontFamily: "var(--font-ui)",
      fontSize: "var(--text-caption)",
      color: "var(--critical)"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.StatusDot, {
    tone: "critical"
  }), " root cause"));
}
Object.assign(__ds_scope, { ServiceNode });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/graph/ServiceNode.jsx", error: String((e && e.message) || e) }); }

// components/graph/ServiceGraph.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const NODE_W = 184;
const NODE_H = 58;
function center(p) {
  return {
    x: p.x + NODE_W / 2,
    y: p.y + NODE_H / 2
  };
}

/**
 * The workspace canvas (DESIGN.md §9.3a): dotted grid on --canvas, SVG edges,
 * draggable nodes, and a traveling trace pulse. The grid is decorative
 * wayfinding only — it never carries state or color.
 */
function ServiceGraph({
  nodes = [],
  edges = [],
  visited = [],
  rootId = null,
  lowConfidence = false,
  blastRadiusIds = [],
  activeHop = null,
  settled = false,
  selectedId = null,
  onSelectNode,
  style,
  children,
  ...rest
}) {
  const [pos, setPos] = React.useState(() => Object.fromEntries(nodes.map(n => [n.id, {
    x: n.x,
    y: n.y
  }])));
  const [t, setT] = React.useState(1);
  const drag = React.useRef(null);
  React.useEffect(() => {
    setPos(p => Object.fromEntries(nodes.map(n => [n.id, p[n.id] || {
      x: n.x,
      y: n.y
    }])));
  }, [nodes]);
  React.useEffect(() => {
    if (!activeHop) return;
    const reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setT(1);
      return;
    }
    let raf, start;
    const step = ts => {
      if (!start) start = ts;
      const k = Math.min(1, (ts - start) / 200);
      setT(k);
      if (k < 1) raf = requestAnimationFrame(step);
    };
    setT(0);
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [activeHop]);
  const onPointerDown = id => e => {
    e.preventDefault();
    const p = pos[id];
    drag.current = {
      id,
      dx: e.clientX - p.x,
      dy: e.clientY - p.y,
      moved: false
    };
    e.currentTarget.setPointerCapture(e.pointerId);
  };
  const onPointerMove = e => {
    const d = drag.current;
    if (!d) return;
    d.moved = true;
    setPos(p => ({
      ...p,
      [d.id]: {
        x: e.clientX - d.dx,
        y: e.clientY - d.dy
      }
    }));
  };
  const onPointerUp = () => {
    drag.current = null;
  };
  const isVisited = id => visited.indexOf(id) !== -1;
  const edgeState = e => {
    if (rootId && (e.from === rootId || e.to === rootId) && isVisited(e.from) && isVisited(e.to)) return "root";
    return isVisited(e.from) && isVisited(e.to) ? "visited" : "idle";
  };
  let pulse = null;
  if (activeHop && pos[activeHop.from] && pos[activeHop.to]) {
    const a = center(pos[activeHop.from]);
    const b = center(pos[activeHop.to]);
    pulse = {
      x: a.x + (b.x - a.x) * t,
      y: a.y + (b.y - a.y) * t
    };
  }
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    onPointerMove: onPointerMove,
    onPointerUp: onPointerUp,
    style: {
      position: "relative",
      overflow: "hidden",
      background: "var(--canvas)",
      backgroundImage: "radial-gradient(var(--hairline) 1px, transparent 1px)",
      backgroundSize: "var(--grid-dot-pitch) var(--grid-dot-pitch)",
      borderRadius: "var(--radius-lg)",
      border: "1px solid var(--hairline)",
      ...style
    }
  }), /*#__PURE__*/React.createElement("svg", {
    style: {
      position: "absolute",
      inset: 0,
      width: "100%",
      height: "100%",
      pointerEvents: "none"
    }
  }, edges.map((e, i) => {
    const a = pos[e.from],
      b = pos[e.to];
    if (!a || !b) return null;
    const c1 = center(a),
      c2 = center(b);
    const st = edgeState(e);
    return /*#__PURE__*/React.createElement("path", {
      key: i,
      d: `M ${c1.x} ${c1.y} C ${(c1.x + c2.x) / 2} ${c1.y}, ${(c1.x + c2.x) / 2} ${c2.y}, ${c2.x} ${c2.y}`,
      fill: "none",
      stroke: st === "root" ? "var(--critical)" : st === "visited" ? "var(--brand)" : "var(--hairline)",
      strokeOpacity: st === "idle" ? 1 : settled && st === "visited" ? 0.4 : 1,
      strokeWidth: st === "idle" ? 1 : 1.5
    });
  }), pulse && /*#__PURE__*/React.createElement("circle", {
    cx: pulse.x,
    cy: pulse.y,
    r: "4",
    fill: "var(--brand-hover)"
  })), nodes.map(n => {
    const p = pos[n.id] || {
      x: n.x,
      y: n.y
    };
    return /*#__PURE__*/React.createElement(__ds_scope.ServiceNode, {
      key: n.id,
      name: n.name,
      rate: n.rate,
      health: n.health,
      anomaly: n.anomaly,
      state: n.id === rootId ? "root" : isVisited(n.id) ? "visited" : "idle",
      lowConfidence: n.id === rootId && lowConfidence,
      blastRadius: blastRadiusIds.indexOf(n.id) !== -1,
      settled: settled && isVisited(n.id),
      selected: selectedId === n.id,
      onPointerDown: onPointerDown(n.id),
      onClick: () => {
        if (!drag.current || !drag.current.moved) onSelectNode && onSelectNode(n.id);
      },
      style: {
        position: "absolute",
        left: p.x,
        top: p.y,
        width: NODE_W,
        boxSizing: "border-box"
      }
    });
  }), children);
}
Object.assign(__ds_scope, { ServiceGraph });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/graph/ServiceGraph.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/ConsoleApp.jsx
try { (() => {
function ConsoleApp() {
  const D = window.ARGUS_DATA;
  if (!D) return null;
  const {
    AppHeader,
    ServiceGraph,
    LogStream,
    ChatPanel,
    IncidentReport,
    NodeDetailPanel,
    NavDrawer,
    BlastRadiusPanel,
    Button,
    Icon,
    Badge,
    CitationChip,
    ConfidenceTag,
    CodeBlock,
    StatGrid
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
  const flash = id => {
    setFlashId(null);
    setTimeout(() => setFlashId(id), 20);
    const el = document.getElementById("log-" + id);
    if (el) el.parentNode.parentNode.scrollTop = el.offsetTop - 40;
  };
  const runTrace = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
    setVisited([]);
    setRootId(null);
    setSettled(false);
    setActiveHop(null);
    const path = D.tracePath;
    setVisited([path[0]]);
    path.slice(1).forEach((id, i) => {
      timers.current.push(setTimeout(() => {
        setActiveHop({
          from: path[i],
          to: id
        });
        timers.current.push(setTimeout(() => setVisited(v => v.concat(id)), 200));
      }, 260 * i + 120));
    });
    timers.current.push(setTimeout(() => {
      setActiveHop(null);
      setRootId(path[path.length - 1]);
      setSettled(true);
    }, 260 * (path.length - 1) + 420));
  };
  const ask = text => {
    const q = (text || "").trim() || "Why are payments failing?";
    setQuery("");
    setMessages(m => m.concat({
      role: "user",
      text: q
    }));
    setBusy(true);
    setResolved(false);
    runTrace();
    timers.current.push(setTimeout(() => {
      setBusy(false);
      setResolved(true);
      setScreen("report");
      setMessages(m => m.concat({
        role: "agent",
        cards: agentCards()
      }));
    }, 1900));
  };
  const agentCards = () => [{
    label: "Root cause",
    content: /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        alignItems: "center",
        gap: "var(--space-sm)",
        flexWrap: "wrap"
      }
    }, /*#__PURE__*/React.createElement("span", {
      className: "argus-mono",
      style: {
        color: "var(--brand)"
      }
    }, D.incident.rootCause), /*#__PURE__*/React.createElement(ConfidenceTag, {
      level: "high"
    }))
  }, {
    label: "Evidence",
    content: /*#__PURE__*/React.createElement("div", {
      style: {
        display: "flex",
        gap: "var(--space-xs)",
        flexWrap: "wrap"
      }
    }, D.incident.evidence.map(e => /*#__PURE__*/React.createElement(CitationChip, {
      key: e.id,
      label: e.label,
      onClick: () => flash(e.id)
    })))
  }, {
    label: "Relevant code",
    content: /*#__PURE__*/React.createElement(CodeBlock, {
      lines: D.incident.code.lines,
      filename: D.incident.code.filename,
      startLine: 142
    })
  }, {
    label: "Recommended fix",
    content: /*#__PURE__*/React.createElement(CodeBlock, {
      diff: true,
      lines: D.incident.fix.lines,
      filename: D.incident.fix.filename
    })
  }];
  const logs = D.logs.map(l => ({
    ...l,
    cited: resolved ? l.cited : false
  }));
  const detail = selected ? D.services.find(s => s.id === selected) : null;
  const detailCode = detail ? D.serviceCode[detail.id] : null;
  const blastRadiusIds = resolved ? D.blastRadius.map(b => b.id) : [];
  const [exportText, setExportText] = React.useState(null);
  const exportRef = React.useRef(null);
  React.useEffect(() => {
    if (exportText && exportRef.current) {
      exportRef.current.focus();
      exportRef.current.select();
    }
  }, [exportText]);
  const formatPostmortem = incident => {
    const incidentId = "INC-" + Date.now().toString(36).slice(-6).toUpperCase();
    const date = new Date().toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
    const toSeconds = t => t.split(":").reduce((a, v) => a * 60 + parseFloat(v), 0);
    const timeline = incident.timeline || [];
    const firstTime = timeline.length ? timeline[0].time : null;
    const detectedTime = timeline.length ? timeline[timeline.length - 1].time : null;
    const duration = timeline.length > 1 ? Math.max(1, Math.round((toSeconds(detectedTime) - toSeconds(firstTime)) / 60)) + "m" : null;
    const affected = D.blastRadius || [];
    const confidenceLabel = incident.confidence === "low" ? "Needs review" : "High";
    const evidenceLines = (incident.evidence || []).map(e => D.logs.find(l => l.id === e.id)).filter(Boolean).sort((a, b) => a.time < b.time ? -1 : a.time > b.time ? 1 : 0).map(log => `${log.time}  ${log.text}`).join("\n");
    let md = `# ${incidentId} — ${incident.service}\n${date}\n\n`;
    if (incident.confidentCauseFound === false) {
      md += `${incident.summary}\n\n`;
      md += `## What was checked\n\n${incident.ruledOut || "No candidate met the confidence threshold."}\n\n`;
      if (evidenceLines) md += "## Evidence reviewed\n\n```\n" + evidenceLines + "\n```\n\n";
      md += "## Outcome\n\nNo confident root cause was identified. This record exists as proof an investigation happened, not as a diagnosis.\n\n";
      md += "---\nGenerated by ARGUS · confidence: Needs review";
    } else {
      const durationMin = duration ? parseInt(duration, 10) : null;
      const narrative = firstTime ? `At ${firstTime}, ${incident.service} began failing with a ${incident.rootCauseFailureType || "fault"} in ${incident.rootCauseFn ? incident.rootCauseFn + "'s call to " + (incident.rootCauseTarget || "a dependency") : "its dependency"} (see evidence below).` + (durationMin && detectedTime ? ` The cause was identified ${durationMin} minute${durationMin === 1 ? "" : "s"} later, at ${detectedTime}.` : "") : `${incident.service} was traced to ${incident.rootCause}.`;
      md += narrative + "\n\n";
      const impactList = affected.length ? affected.map(a => a.name).join(", ") : "none";
      md += `**Impact:** ${affected.length} downstream service${affected.length === 1 ? "" : "s"} (${impactList}).\n\n`;
      if (evidenceLines) md += "## Evidence\n\n```\n" + evidenceLines + "\n```\n\n";
      if (incident.code) {
        md += `*The ${incident.rootCauseFailureType || "failure"} traced above originates in the code below:*\n\n`;
        md += "## Relevant code\n\n```ts\n" + incident.code.lines.join("\n") + "\n```\n\n";
      }
      if (incident.fix) {
        const diff = incident.fix.lines.map(l => (l.kind === "add" ? "+ " : l.kind === "remove" ? "- " : "  ") + l.text).join("\n");
        md += "## Resolution\n\n```diff\n" + diff + "\n```\n\n";
      }
      md += `---\nGenerated by ARGUS · confidence: ${confidenceLabel}`;
    }
    return md;
  };
  const onExportPostmortem = async incident => {
    const md = formatPostmortem(incident);
    const ok = await copyToClipboard(md);
    if (!ok) setExportText(md);
    return ok;
  };
  const copyToClipboard = text => {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(() => true).catch(() => fallbackCopy(text));
    }
    return Promise.resolve(fallbackCopy(text));
  };
  const fallbackCopy = text => {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    let ok = false;
    try {
      ok = document.execCommand("copy");
    } catch (e) {
      ok = false;
    }
    document.body.removeChild(ta);
    return ok;
  };
  const navItems = [{
    id: "workspace",
    label: "Workspace",
    icon: "layout-grid"
  }, {
    id: "report",
    label: "Report",
    icon: "file-text",
    badge: resolved ? 1 : null
  }, {
    id: "blast",
    label: "Blast Radius",
    icon: "share-2"
  }, {
    id: "guide",
    label: "How it works",
    icon: "help-circle"
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      height: "100vh",
      background: "var(--canvas)"
    }
  }, /*#__PURE__*/React.createElement(AppHeader, {
    services: D.services,
    onSelectService: id => {
      setScreen("workspace");
      setSelected(id);
    },
    onMenuClick: () => setDrawerOpen(true),
    right: /*#__PURE__*/React.createElement(Badge, null, "prod \xB7 us-east-1")
  }), /*#__PURE__*/React.createElement(NavDrawer, {
    open: drawerOpen,
    items: navItems,
    activeId: screen,
    onSelect: setScreen,
    onClose: () => setDrawerOpen(false)
  }), screen === "workspace" && /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      minHeight: 0,
      display: "flex",
      gap: "var(--gap-zone)",
      padding: "var(--space-lg)"
    }
  }, /*#__PURE__*/React.createElement("section", {
    style: {
      flex: "1 1 60%",
      minWidth: 0,
      display: "flex",
      flexDirection: "column",
      gap: "var(--gap-zone)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      flex: "1 1 auto",
      minHeight: 320,
      display: "flex"
    }
  }, /*#__PURE__*/React.createElement(ServiceGraph, {
    nodes: D.services,
    edges: D.edges,
    visited: visited,
    rootId: rootId,
    blastRadiusIds: blastRadiusIds,
    activeHop: activeHop,
    settled: settled,
    selectedId: selected,
    onSelectNode: setSelected,
    style: {
      flex: 1
    }
  }), settled && /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    onClick: runTrace,
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "rotate-ccw",
      size: 14
    }),
    style: {
      position: "absolute",
      right: "var(--space-md)",
      bottom: "var(--space-md)"
    }
  }, "Replay")), /*#__PURE__*/React.createElement(LogStream, {
    lines: logs,
    flashId: flashId,
    onLineClick: flash,
    style: {
      flex: "1 1 160px",
      minHeight: 140
    }
  })), /*#__PURE__*/React.createElement("section", {
    style: {
      flex: "1 1 40%",
      minWidth: 380,
      display: "flex",
      flexDirection: "column",
      minHeight: 0
    }
  }, /*#__PURE__*/React.createElement(ChatPanel, {
    messages: messages,
    busy: busy,
    value: query,
    onChange: e => setQuery(e.target.value),
    onSubmit: ask
  }))), screen === "report" && /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      minHeight: 0,
      overflow: "auto",
      padding: "var(--space-lg)"
    }
  }, /*#__PURE__*/React.createElement(IncidentReport, {
    incident: resolved ? D.incident : null,
    onRootCauseClick: () => {
      setScreen("workspace");
      setSelected("payment");
    },
    onStatClick: s => s.sourceLogIds && (setScreen("workspace"), flash(s.sourceLogIds[0])),
    onCitationClick: e => {
      setScreen("workspace");
      flash(e.id);
    },
    onCodeClick: () => {
      setScreen("workspace");
      setSelected("payment");
    },
    onExportPostmortem: onExportPostmortem,
    style: {
      maxWidth: 760,
      margin: "0 auto"
    }
  })), screen === "blast" && /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      minHeight: 0,
      overflow: "auto",
      padding: "var(--space-lg)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 560,
      margin: "0 auto",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, resolved ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("p", {
    className: "argus-body",
    style: {
      margin: 0
    }
  }, D.blastRadius.length, " downstream services affected by ", /*#__PURE__*/React.createElement("span", {
    className: "argus-mono",
    style: {
      color: "var(--brand)"
    }
  }, "payment-service"), "."), /*#__PURE__*/React.createElement(BlastRadiusPanel, {
    items: D.blastRadius
  })) : /*#__PURE__*/React.createElement("p", {
    className: "argus-body",
    style: {
      margin: 0,
      textAlign: "center",
      color: "var(--ink-subtle)"
    }
  }, "No incident to analyze yet."))), screen === "guide" && /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      minHeight: 0,
      overflow: "auto",
      padding: "var(--space-xxl) var(--space-lg)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 680,
      margin: "0 auto",
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xxl)"
    }
  }, /*#__PURE__*/React.createElement("h1", {
    className: "argus-headline",
    style: {
      margin: 0
    }
  }, "How ARGUS works"), [{
    t: "Workspace",
    items: [{
      l: "Header & status strip",
      d: "56px bar with the ARGUS wordmark and one live dot per service. A dot pulses only while that service has an active anomaly — healthy and idle dots stay still. Click a dot to pan the graph to that service."
    }, {
      l: "Service graph",
      d: "Every real service in the dependency graph, rendered on load before you ask anything — nothing is generated by a query. Only position is draggable; identity and edges come straight from the dependency graph. A node lights --brand as the trace reaches it, holds --critical if it's the confirmed root cause, and shows a dashed border with a \"needs review\" tag when the agent isn't confident."
    }, {
      l: "Log stream",
      d: "The raw evidence, scrolling in real time even at idle. Each line has a severity dot; lines cited by the current report get a brand tint and a \"cited\" tag, right-aligned."
    }, {
      l: "Chat",
      d: "Ask in plain language. Answers render as separate Root Cause / Evidence / Code / Fix cards, never one paragraph, staggered in as each resolves. A pulsing dot plus a rotating label (\"Analyzing logs…\", \"Tracing dependencies…\") shows the agent working."
    }, {
      l: "Node detail panel",
      d: "Click any node to open it. Shows the relevant source code and recent logs for that one service, plus a one-line bridge explaining why they belong together. Click a cited log line to highlight the exact code line it explains, or click the code line to highlight the log back."
    }]
  }, {
    t: "Incident Report",
    items: [{
      l: "Status header",
      d: "Red \"INCIDENT — service name\" the moment a cause is confirmed; green \"No active incidents\" at idle."
    }, {
      l: "Plain-language summary",
      d: "One sentence, no jargon — what happened, stated as fact."
    }, {
      l: "Timeline",
      d: "Dots for first anomaly, escalation and diagnosis, colored with the same severity convention as the log stream."
    }, {
      l: "Stat grid",
      d: "Every number is clickable and jumps straight to the log line that produced it — no number ships without a working source link."
    }, {
      l: "Root cause & confidence",
      d: "The service name links back to the graph. A confidence tag reads \"High\" or \"Needs review\" and is always visible — this is the product's core trust signal, never hidden."
    }, {
      l: "Evidence",
      d: "Citation chips, each clickable through to its source log line."
    }, {
      l: "Relevant code & recommended fix",
      d: "Two separate blocks on purpose: the code the cause lives in, then a diff-styled fix — \"here's where it lives\" before \"here's what to change.\""
    }, {
      l: "Honest failure state",
      d: "If nothing clears the confidence bar, the header turns brand — not red — and says so directly: what was checked and what was ruled out, instead of a fabricated best guess."
    }, {
      l: "Postmortem export",
      d: "One click formats the report already on screen into a markdown document and copies it — pure templating of existing data, no extra reasoning call."
    }]
  }, {
    t: "Blast Radius",
    items: [{
      l: "What it answers",
      d: "Which other services are affected by the root cause — a different question from which ones the agent walked through to find it."
    }, {
      l: "How it's built",
      d: "Computed by walking the same dependency graph the Workspace already shows, outward from the root cause. No new data source."
    }, {
      l: "On the graph",
      d: "Affected nodes get a small brand-tinted corner marker, distinct from the trace-path glow, so the two states can overlap without reading as the same thing."
    }]
  }].map(section => /*#__PURE__*/React.createElement("div", {
    key: section.t,
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, /*#__PURE__*/React.createElement("h2", {
    className: "argus-card-title"
  }, section.t), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-md)"
    }
  }, section.items.map(it => /*#__PURE__*/React.createElement("div", {
    key: it.l,
    style: {
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-xxs)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "argus-body-sm",
    style: {
      color: "var(--ink)"
    }
  }, it.l), /*#__PURE__*/React.createElement("p", {
    className: "argus-body-sm",
    style: {
      margin: 0
    }
  }, it.d)))))))), exportText && /*#__PURE__*/React.createElement("div", {
    onClick: () => setExportText(null),
    style: {
      position: "fixed",
      inset: 0,
      background: "rgba(1,1,2,0.6)",
      zIndex: 50,
      display: "flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation(),
    style: {
      background: "var(--surface-3)",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-lg)",
      padding: "var(--space-lg)",
      width: 520,
      display: "flex",
      flexDirection: "column",
      gap: "var(--space-sm)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("span", {
    className: "argus-card-title"
  }, "Copy postmortem"), /*#__PURE__*/React.createElement("button", {
    onClick: () => setExportText(null),
    "aria-label": "Close",
    style: {
      display: "flex",
      background: "transparent",
      border: "1px solid var(--hairline)",
      borderRadius: "var(--radius-xs)",
      padding: "var(--space-xxs)",
      color: "var(--ink-subtle)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "x",
    size: 14
  }))), /*#__PURE__*/React.createElement("p", {
    className: "argus-caption",
    style: {
      margin: 0
    }
  }, "Automatic copy was blocked by this browser. The text is already selected \u2014 press \u2318/Ctrl+C."), /*#__PURE__*/React.createElement("textarea", {
    ref: exportRef,
    readOnly: true,
    value: exportText,
    style: {
      width: "100%",
      height: 260,
      background: "var(--surface-2)",
      border: "1px solid var(--hairline-tertiary)",
      borderRadius: "var(--radius-sm)",
      color: "var(--ink)",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-mono)",
      padding: "var(--space-md)",
      resize: "vertical",
      boxSizing: "border-box"
    }
  }))), /*#__PURE__*/React.createElement(NodeDetailPanel, {
    open: !!detail,
    service: detail ? detail.name : "",
    health: detail ? detail.health : "healthy",
    anomaly: detail ? !!detail.anomaly : false,
    bridge: detailCode ? detailCode.bridge : null,
    filename: detailCode ? detailCode.filename : null,
    code: detailCode ? detailCode.lines : [],
    matches: detailCode ? detailCode.matches : [],
    logs: D.logs.slice(2, 7),
    onClose: () => setSelected(null)
  }));
}
window.ConsoleApp = ConsoleApp;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/ConsoleApp.jsx", error: String((e && e.message) || e) }); }

// ui_kits/console/consoleData.js
try { (() => {
// Mock data for the ARGUS console UI kit. Services, edges and logs stand in for
// the backend dependency graph and log index.
window.ARGUS_DATA = {
  services: [{
    id: "gw",
    name: "api-gateway",
    rate: "0/hr",
    x: 12,
    y: 12,
    health: "healthy"
  }, {
    id: "orders",
    name: "orders-service",
    rate: "12/hr",
    x: 210,
    y: 12,
    health: "degraded",
    anomaly: true
  }, {
    id: "payment",
    name: "payment-service",
    rate: "41/hr",
    x: 12,
    y: 108,
    health: "critical",
    anomaly: true
  }, {
    id: "ledger",
    name: "ledger-worker",
    rate: "3/hr",
    x: 210,
    y: 108,
    health: "healthy"
  }, {
    id: "notify",
    name: "notify-worker",
    rate: "0/hr",
    x: 12,
    y: 204,
    health: "healthy"
  }, {
    id: "pgbouncer",
    name: "pgbouncer",
    rate: "0/hr",
    x: 210,
    y: 204,
    health: "healthy"
  }],
  edges: [{
    from: "gw",
    to: "orders"
  }, {
    from: "orders",
    to: "payment"
  }, {
    from: "orders",
    to: "notify"
  }, {
    from: "payment",
    to: "ledger"
  }, {
    from: "pgbouncer",
    to: "payment"
  }],
  tracePath: ["gw", "orders", "payment"],
  blastRadius: [{
    id: "orders",
    name: "orders-service",
    health: "degraded",
    note: "queued retries backing up"
  }, {
    id: "gw",
    name: "api-gateway",
    health: "degraded",
    note: "elevated p99 latency from retries"
  }, {
    id: "ledger",
    name: "ledger-worker",
    health: "healthy",
    note: "ledger entries deferred"
  }],
  logs: [{
    id: "l1",
    time: "14:18:02.004",
    text: "charge attempt order=ord_8802 gateway=stripe",
    severity: "info"
  }, {
    id: "l2",
    time: "14:18:02.311",
    text: "gateway.charge latency 2984ms (p99 threshold 1200ms)",
    severity: "warn"
  }, {
    id: "l3",
    time: "14:22:07.318",
    text: "gateway.charge timeout after 3000ms order=ord_8871",
    severity: "error",
    cited: true
  }, {
    id: "l4",
    time: "14:22:07.402",
    text: "retry 1/3 order=ord_8871",
    severity: "warn"
  }, {
    id: "l5",
    time: "14:22:08.115",
    text: "charge failed order=ord_8871 code=GATEWAY_TIMEOUT",
    severity: "error",
    cited: true
  }, {
    id: "l6",
    time: "14:22:08.220",
    text: "ledger entry deferred order=ord_8871",
    severity: "info"
  }, {
    id: "l7",
    time: "14:22:09.006",
    text: "circuit breaker half-open payment->stripe",
    severity: "warn"
  }, {
    id: "l8",
    time: "14:22:11.441",
    text: "charge failed order=ord_8872 code=GATEWAY_TIMEOUT",
    severity: "error"
  }],
  incident: {
    service: "payment-service",
    summary: "Card charges started timing out at 14:18 when gateway latency passed the 3s client timeout, and the retry path gave up before the gateway recovered.",
    timeline: [{
      time: "14:18:02",
      label: "First anomaly",
      severity: "warn"
    }, {
      time: "14:22:07",
      label: "Escalated",
      severity: "error"
    }, {
      time: "14:24:40",
      label: "Root cause identified",
      severity: "info"
    }],
    confidentCauseFound: true,
    rootCauseFn: "charge()",
    rootCauseTarget: "the payment gateway",
    rootCauseFailureType: "timeout",
    stats: [{
      label: "Failed charges",
      value: "1,284",
      tone: "critical",
      sourceLogIds: ["l5"]
    }, {
      label: "Error rate",
      value: "41/hr",
      sourceLogIds: ["l8"]
    }, {
      label: "First seen",
      value: "14:18:02",
      sourceLogIds: ["l2"]
    }, {
      label: "Services touched",
      value: "3",
      sourceLogIds: ["l3"]
    }],
    rootCause: "payment-service · charge() gateway timeout",
    confidence: "high",
    evidence: [{
      id: "l3",
      label: "log:14:22:07.318"
    }, {
      id: "l5",
      label: "log:14:22:08.115"
    }, {
      id: "l2",
      label: "log:14:18:02.311"
    }],
    code: {
      filename: "services/payment/charge.ts",
      startLine: 142,
      lines: ["export async function charge(order: Order) {", "  const res = await gateway.charge(order);", "  if (!res.ok) throw new GatewayError(res.code);", "  return res;", "}"]
    },
    fix: {
      filename: "services/payment/charge.ts",
      lines: [{
        text: "  const res = await gateway.charge(order);",
        kind: "remove"
      }, {
        text: "  const res = await gateway.charge(order, { timeout: 8_000 });",
        kind: "add"
      }, {
        text: "  if (!res.ok) throw new GatewayError(res.code);",
        kind: "context"
      }, {
        text: "  await retryWithBackoff(() => gateway.charge(order), { tries: 5 });",
        kind: "add"
      }]
    }
  },
  noConfidentIncident: {
    service: "orders-service",
    summary: "Order submission latency rose for nine minutes with no clear trigger; three candidate services were checked and none met the confidence threshold.",
    timeline: [{
      time: "09:04:11",
      label: "First anomaly",
      severity: "warn"
    }, {
      time: "09:13:02",
      label: "Investigation closed",
      severity: "info"
    }],
    confidentCauseFound: false,
    ruledOut: "Ruled out: pgbouncer connection saturation (pool had headroom) and notify-worker backlog (queue depth normal). No service's error pattern matched the latency signature closely enough to call.",
    stats: [{
      label: "Peak p99",
      value: "1.9s"
    }, {
      label: "Duration",
      value: "9m"
    }, {
      label: "Candidates checked",
      value: "3"
    }],
    evidence: [{
      id: "l1",
      label: "log:09:04:11.002"
    }, {
      id: "l2",
      label: "log:09:09:44.118"
    }]
  },
  serviceCode: {
    payment: {
      filename: "services/payment/charge.ts",
      bridge: "This service threw the timeout seen in the cited logs below.",
      lines: ["const res = await gateway.charge(order);", "if (!res.ok) throw new GatewayError(res.code);"],
      matches: [{
        logId: "l3",
        lineIndex: 0
      }, {
        logId: "l5",
        lineIndex: 1
      }]
    },
    orders: {
      filename: "services/orders/submit.ts",
      bridge: "This service calls payment.charge directly, so its retry loop is where the timeout surfaces.",
      lines: ["const charge = await payment.charge(order);", "return { id: order.id, charge };"],
      matches: [{
        logId: "l4",
        lineIndex: 0
      }]
    }
  }
};
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/console/consoleData.js", error: String((e && e.message) || e) }); }

__ds_ns.AgentCard = __ds_scope.AgentCard;

__ds_ns.AppHeader = __ds_scope.AppHeader;

__ds_ns.BlastRadiusPanel = __ds_scope.BlastRadiusPanel;

__ds_ns.ChatPanel = __ds_scope.ChatPanel;

__ds_ns.IncidentReport = __ds_scope.IncidentReport;

__ds_ns.ConfidenceExplainer = __ds_scope.ConfidenceExplainer;

__ds_ns.IncidentTimeline = __ds_scope.IncidentTimeline;

__ds_ns.LogStream = __ds_scope.LogStream;

__ds_ns.NavDrawer = __ds_scope.NavDrawer;

__ds_ns.NodeDetailPanel = __ds_scope.NodeDetailPanel;

__ds_ns.StatGrid = __ds_scope.StatGrid;

__ds_ns.StatusStrip = __ds_scope.StatusStrip;

__ds_ns.ThinkingIndicator = __ds_scope.ThinkingIndicator;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.CitationChip = __ds_scope.CitationChip;

__ds_ns.CodeBlock = __ds_scope.CodeBlock;

__ds_ns.ConfidenceTag = __ds_scope.ConfidenceTag;

__ds_ns.ActivityBadge = __ds_scope.ActivityBadge;

__ds_ns.Icon = __ds_scope.Icon;

__ds_ns.StatusDot = __ds_scope.StatusDot;

__ds_ns.TabSwitch = __ds_scope.TabSwitch;

__ds_ns.TextInput = __ds_scope.TextInput;

__ds_ns.ServiceGraph = __ds_scope.ServiceGraph;

__ds_ns.ServiceNode = __ds_scope.ServiceNode;

})();
