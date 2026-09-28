STRONG_AT = 0.6

REASONS = {
    "evidence":  ("the evidence was strong", "there were only a few errors"),
    "dominance": ("only one possible cause was left", "several services looked equally likely"),
    "relevance": ("matching code was found", "the code found was only a loose match"),
}


def b(x):
    return f"**{x}**"


def join(items, oxford=False):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    sep = ", and " if oxford else " and "
    return ", ".join(items[:-1]) + sep + items[-1]


def _fmt_count(n):
    """394 not 394.0, but keep a fraction (e.g. from WARNING_WEIGHT) if there
    is one."""
    n = round(n, 2)
    return str(int(n)) if float(n).is_integer() else str(n)


def confidence_reason(incident, conf, competing_candidates, divisor):
    """Short, structured reason for the diagnosis object / incidents entries
    -- separate from explain()'s long narrative paragraph below. Plain
    f-strings from the run's real values only: no LLM, no hardcoded service
    names, nothing beyond `incident`, `conf`, `competing_candidates`, and the
    evidence divisor passed in by the caller. None when confidence is high --
    there's nothing to explain away.

    competing_candidates is only non-empty when low confidence is caused by
    ambiguity (see query_pipeline._competing_candidates), so its length alone
    tells us which of the three "low" reasons applies: 2+ plausible roots,
    one root with thin evidence, or one root with only a weak code match.
    """
    if conf["label"] == "high":
        return None
    if not incident.get("root"):
        return "No errors were found in the last 5 minutes."
    if len(competing_candidates) > 1:
        pieces = [f"{c['service']} ({_fmt_count(c['weighted_errors'])} errors)" for c in competing_candidates]
        verb = "are both" if len(pieces) == 2 else "are all"
        return f"{join(pieces)} {verb} plausible root causes, so ARGUS cannot tell which one started this."
    if conf["signals"]["evidence"] < 1.0:
        return (f"{incident['root']} had only {incident['root_errors']} errors, "
                f"below the {divisor} needed for full evidence weight.")
    if conf["signals"]["relevance"] < STRONG_AT:
        return "The code found only loosely matches the errors."
    return None


def explain(r):
    n = len(r["failing_services"])
    root, cands, syms = r["root"], r["candidates"], r["symptoms"]
    label, score = r["label"], r["score"]
    conf = b(f"{label} ({score:.2f})")

    if n == 0:
        return (f"ARGUS checked every service and found {b('no errors')} in the "
                f"last 5 minutes, so it did {b('not name a cause')}.")

    if len(cands) > 1:
        return (f"ARGUS saw errors in {b(str(n) + ' services')}, and "
                f"{b(str(len(cands)) + ' of them')} ({join([b(c) for c in cands])}) "
                f"depend on nothing that was failing. Any of them could have started "
                f"this, so ARGUS did {b('not name a single cause')}. Confidence is {conf}.")

    parts = []
    if syms:
        many = len(syms) > 1
        parts.append(
            f"ARGUS saw errors in {b(str(n) + ' services')}, but "
            f"{'most were just' if many else 'one was just a'} "
            f"{b('victims' if many else 'victim')}.")
        parts.append(
            f"{join([b(s) for s in syms])} {'all depend' if many else 'depends'} on "
            f"{b(root)}, and {b(root)} was failing too. "
            f"So {'their' if many else 'its'} errors were most likely caused by {b(root)}.")
    else:
        parts.append(f"ARGUS saw errors in {b('1 service')}.")

    parts.append(
        f"{b(root)} depends on nothing that was failing, and it had "
        f"{b(str(r['root_errors']) + ' errors in 5 minutes')}, "
        f"so ARGUS named it the {b('root cause')}.")

    good, bad = [], []
    for key in ("evidence", "dominance", "relevance"):
        s = r["signals"][key]
        if s >= STRONG_AT:
            good.append(REASONS[key][0])
        else:
            bad.append(REASONS[key][1])
    primary, secondary = (good, bad) if label == "high" else (bad, good)
    if not primary:
        primary, secondary = secondary, []
    sentence = f"Confidence is {conf} because {join(primary, oxford=True)}"
    if secondary:
        sentence += f", though {join(secondary, oxford=True)}"
    parts.append(sentence + ".")

    if r.get("is_eval") and not r.get("match"):
        parts.append(f"The planted bug was in {b(r['expected'])}, so this answer was {b('wrong')}.")

    if r.get("activity") == "stopped" and r.get("last_error_age_s") is not None:
        minutes = round(r["last_error_age_s"] / 60)
        parts.append(f"The last error was {minutes} minutes ago, so this may already be over.")

    return " ".join(parts)
