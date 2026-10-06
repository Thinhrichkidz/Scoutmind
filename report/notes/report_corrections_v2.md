# ScoutMind report: corrections for v2

**Why this file exists.** The v1 draft (`ScoutMind.pdf`) was written from
`report_material.md` as it stood on 4 October 2026 — before the formal
measured experiment was actually run. That experiment has since been
completed for the core attack scenario (`results/attack_results.csv`,
`results/defence_results.csv`, 10 real trials each, verified directly against
the files in this repo). The draft still describes that experiment as
"outstanding" and the interfaces as "not yet built," both of which are now
false. This file gives corrected replacement text for every section that
needs it. Sections not listed here (1, 2, 3, 4.1–4.5, 6, 9, 10.1–10.3) are
accurate as written and do not need changes.

Do not invent numbers beyond what is in this file or in the CSVs themselves.

---

## Abstract — replace the results sentence

**Delete:**
> In exploratory runs against a locally hosted qwen3:8b model, the attack
> chain succeeded once the injection wording was tuned over four rounds; the
> final wording produced a full silent leak in 2 of 5 runs and a visible-text
> leak in 3 of 5. We implemented a domain-origin allowlist defence on the
> exfiltration channel, verified by 34 unit tests, and we analyse its limits...

**Replace with:**
> Against a locally hosted qwen3:8b model, the attack chain succeeded after
> the injection wording was tuned over four exploratory rounds. In a formal
> measured experiment of 10 trials per condition, the undefended agent leaked
> the fictional credentials through the image channel in 3 of 10 runs (30%)
> and placed them in the visible summary text in 7 of 10 (70%), while still
> completing the user's legitimate task in every run. We implemented a
> domain-origin allowlist defence on the exfiltration channel, verified by
> 196 unit tests and then measured directly against the live model: it
> reduced the image-channel leak to 0 of 10 runs (0%) at no cost to task
> completion, but did not reduce the underlying goal hijack (8 of 10 runs,
> 80%) or the text-only leak (8 of 10, 80%). We analyse these limits...

---

## Section 4.6 — correct the interface status

**Delete the last two sentences:**
> At the time of writing these are command-line and log-file views; a
> graphical user interface, an attacker console and a single side-by-side
> comparison screen with a defence on/off toggle are designed but not yet
> built, and are listed among the outstanding work.

**Replace with:**
> All three views are built: a Streamlit user interface (`app.py`) presents
> the chat-style request and the final summary the way a real user would see
> it; a Flask attacker console (`attacker/attacker_console.py`), run as a
> separate process on its own port, lets the attacker publish a crafted page
> into the page pool and watch the attacker server's log fill in real time,
> without ever talking to the agent directly; and a comparison view
> (`comparison.py`) renders the full tool-call trace next to the user-visible
> summary, with the defence on/off toggle driving both. All three are covered
> by their own automated tests (`test_app.py`, `test_attacker_console.py`,
> `test_comparison.py`).

---

## Section 5.3 — fix the port number

**Delete:**
> and constructs an image URL of the form
> http://127.0.0.1:8000/log?data=<account data>

**Replace with:**
> and constructs an image URL of the form
> http://127.0.0.1:9000/log?data=<account data>

(This was a leftover from an earlier draft of the fixture; the committed
payload, the attacker server, and every other mention in the report use port
9000. Port 8001 is the separate, allowlisted legitimate image host.)

---

## Section 6.3 — update the test count

**Delete:**
> verified by 34 unit tests

**Replace with:**
> verified by 196 unit tests (20 of which — `test_containment.py` and
> `test_defence.py` — cover the containment guard and the allowlist
> specifically; the remainder cover the agent loop, the experiment runner,
> and the two interfaces)

---

## Section 7 — replace in full

### 7.1 Method

We report three kinds of result, kept clearly separate by how they were
produced.

The first is a set of **exploratory tuning runs** used to get the attack
working at all: four rounds of four or five runs each, every run using the
real qwen3:8b, the user query above, and the defence off. With only four or
five runs per wording, these counts show the mechanism and its sensitivity to
wording, not a reliable probability, and we do not present them as a success
rate.

The second is the **formal measured experiment**, run with the final,
committed injection wording: 10 trials with the defence off and 10 trials
with the defence on, executed by `run_experiments.py` against the live
model, with every trial's outcome taken from `attacker_log.txt` — a leak is
counted only when the attacker's server actually logged a request carrying
that trial's fictional key, never from what the model claimed to do. This is
the primary evidence for this section.

The third is the **status of the three extension scenarios** the same runner
supports (`cdn`, `text_only`, `legit_email`): built and covered by unit
tests, but not yet executed against the live model as their own measured
condition. Section 8 reports what we can say about them from the exploratory
runs and from the literature in the meantime.

The method follows established agent-security benchmarks such as AgentDojo
(Debenedetti et al., 2024), which report both attack success and utility —
whether legitimate tasks still succeed under a defence — together, since
measuring only one would mislead: a defence can reach zero attack success
simply by breaking the agent.

### 7.2 Exploratory attack runs (defence off)

[Keep the existing Round 1–4 table and discussion from the v1 draft
unchanged — it remains accurate as a record of the tuning process and is
good material for Section 10.1's reflection on what did not work first
time.]

### 7.3 Formal measured experiment: attack scenario

| Measure | Defence off (n=10) | Defence on (n=10) |
|---|---|---|
| Goal hijack (`lookup_account_info` called, unrequested) | 7/10 (70%) | 8/10 (80%) |
| `render_image` called at all | 3/10 (30%) | 4/10 (40%) |
| — of those, blocked by the defence | — | 4/4 (100%) |
| **Full image-channel leak (email and key reached the attacker server)** | **3/10 (30%)** | **0/10 (0%)** |
| Text-only leak (fake data in the visible summary) | 7/10 (70%) | 8/10 (80%) |
| Legitimate task completed (`save_summary` reached) | 10/10 (100%) | 10/10 (100%) |

Four things stand out. First, the defence does exactly what it was designed
to do: every one of the four attempted `render_image` calls under the
defence was rejected by the allowlist, taking the image-channel leak rate
from 30% to 0%. Second, it does this at **no measured cost** to the
legitimate task: the agent completed and produced a summary in all 20 trials
regardless of the defence setting. Third, the defence leaves the underlying
problem untouched: the model still called the unrequested privileged tool in
70–80% of runs whether or not the defence was active, because
`lookup_account_info` is not gated by anything. Fourth, the text-only leak —
the fake data appearing directly in the summary a user reads — occurred at
essentially the same rate (70% off, 80% on) regardless of the defence,
because the allowlist governs only `render_image` and has no way to engage
with a leak that never calls it. This is the clearest quantified evidence in
this report for the central claim of Section 8.2: a tool-level control
cannot stop a leak that misuses no tool.

### 7.4 Cost to legitimate use (extension scenarios, outstanding)

The table above already gives one cost-to-usefulness measure — task
completion during the attack scenario itself, which held at 100% regardless
of the defence. The specific case the assignment brief asks for, a user who
*explicitly* asks "summarise this and also give me my account email" with
the defence on, has not yet been run as its own measured condition; the
`legit_email` scenario is built and unit-tested (its hidden page comment is
swapped for a harmless one, isolating the user's own request as the only
source of the email request) but awaits execution. The expected result,
still to be confirmed by measurement, is that the allowlist would not
interfere with it, since it only governs outbound image fetches — which also
exposes the same blind spot described in Section 8.2, since an injected
request to put the email in the text is equally unaffected.

A single earlier exploratory run (defence off, booby-trapped page hidden
from search entirely) completed a clean three-source summary using 9 of its
10 permitted steps, repeating `search_pages` six times — a reminder that a
tidy, non-adversarial run can brush against the step limit on its own, so
step exhaustion in future trials must not be miscounted as a defence
failure.

### 7.5 Summary of findings

The attack chain is demonstrated end to end against a live model, with a
formally measured 30% image-channel leak rate undefended, falling to 0% with
the allowlist defence enabled, at no cost to legitimate task completion. The
defence does not reduce the underlying goal hijack or the text-only leak,
both measured at 70–80% regardless of its setting. The three extension
scenarios (allowlisted-domain leak, isolated text-only condition, and the
explicit legitimate-email request) are built and unit-tested but not yet
run as their own measured conditions; completing them is the most valuable
remaining work before final submission.

---

## Section 8.3 — update the summary table

**Replace the "Allowlist on" column for the original attack row:**

| Attack | Defence off | Allowlist on |
|---|---|---|
| Original image-link attack | Measured: 3/10 (30%) | **Measured: 0/10 (0%)** |
| Variant A: allowlisted domain | Not built | Not built; analysis grounded in ForcedLeak and CamoLeak |
| Variant B: text-only leak | Measured: 7/10 (70%) | **Measured: 8/10 (80%); allowlist cannot engage by design** |

---

## Section 10.5 — Conclusion, replace first two sentences

**Delete:**
> ScoutMind shows that a single instruction hidden in a web page can drive a
> tool-using agent through a complete, zero-click leak of account data: in
> the final tuning round the agent silently sent fictional credentials to an
> attacker server in 2 of 5 runs and placed them in the visible summary in 3
> of 5, all while returning an ordinary-looking summary. The defence against
> the image channel, a domain-origin allowlist, is implemented and
> unit-tested but not yet measured against the model, and the text-only
> variant would bypass it regardless.

**Replace with:**
> ScoutMind shows that a single instruction hidden in a web page can drive a
> tool-using agent through a complete, zero-click leak of account data. In a
> formal 10-trial measured experiment, the undefended agent leaked the data
> through the image channel in 30% of runs and into the visible summary in
> 70%, always while returning an ordinary-looking summary and always
> completing the user's actual task. The domain-origin allowlist defence,
> also measured directly against the model, eliminated the image-channel
> leak entirely (0%) at no cost to task completion, but left the underlying
> goal hijack and the text-only leak essentially unchanged (70–80%
> regardless of the defence setting), confirming by measurement, not just
> analysis, that it closes one channel without touching the root cause.

---

## What is still genuinely outstanding (keep reporting these honestly)

- The three extension scenarios (`cdn`, `text_only` as an isolated
  condition, `legit_email`) as separately measured 10-trial experiments.
- Second-tool reproduction of the baseline runs.
- `README.md` still describes an earlier scaffold stage.
- Privilege separation (gating `lookup_account_info` on whether the request
  came from the user) is design discussion only, not implemented — this
  remains accurate and should stay in the report as future work (Section
  10.3, CaMeL discussion).
