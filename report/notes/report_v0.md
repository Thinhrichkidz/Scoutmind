# ScoutMind report corrections — report_v0

**Why this file exists.** The v1 draft (`ScoutMind.pdf`) was written from
`report_material.md` as it stood on 4 October 2026 — before the formal
measured experiment was actually run and before a full pass against the
assignment's marking criteria. Since then: `results/attack_results.csv` and
`results/defence_results.csv` each gained 10 real trials against the live
model, `app.py`/`attacker/attacker_console.py`/`comparison.py` were built
and tested, and a criteria-by-criteria review found a topic-coverage gap,
a thin defence category, an orphan citation, and two placeholder URLs. This
file gives corrected replacement text for every part of the draft that
needs it, in the order those parts appear in the report. Sections not
mentioned here (1, 4.1–4.5, 6.1–6.2, 6.4, 9, 10.1–10.3) are accurate as
written and need no changes.

Do not invent numbers beyond what is in this file or in the CSVs
themselves.

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

## Section 2 — add a new subsection, 2.4, after 2.3 "Classifying the scenario"

The assignment brief names five attack-surface topics explicitly: *direct
and indirect prompt injection, agent goal hijacking, tool misuse, memory and
context poisoning, and excessive agency.* Section 2.1 discusses "memory and
context" only as an architectural property (ScoutMind keeps no long-term
memory; its exposure is the short-term context window). Memory/context
poisoning as an attack technique is never discussed. Insert this as a new
2.4, renumbering the current "3. Real-world grounding" to stay in sequence:

> ### 2.4 Memory and context poisoning
>
> A distinct risk alongside indirect prompt injection is memory and context
> poisoning: content that corrupts not just the current turn's reasoning but
> a persistent store the agent later trusts — a long-term memory, a vector
> database used for retrieval, or a conversation history reused across
> sessions. Where indirect injection smuggles an instruction into a single
> context window, poisoning aims to leave something behind that influences
> *future* turns, often ones a different, unrelated request would trigger.
>
> ScoutMind's exposure to this specific risk is limited by design: each run
> is single-turn, with no memory carried between requests, so a poisoned
> page cannot outlive the session that reads it. This also means ScoutMind
> does not demonstrate the more severe version of this risk, in which a
> single injection compromises every future interaction rather than one. A
> deployment that *did* give ScoutMind persistent memory — for example,
> caching page summaries to answer future questions faster — would reopen
> this exact vulnerability in a harder-to-detect form: the injected
> instruction would no longer need to survive in the live page at all, only
> in whatever the agent chose to remember from it.

---

## Section 3.2 — fix the orphan Nelson (2025) citation

Nelson (2025) is in your reference list but never cited in the body. Add it
as a second source for the Comet disclosure, at the end of the first
paragraph of 3.2:

**Current last sentence of the first paragraph:**
> Perplexity stated the issue had been patched with no user data
> compromised, while Brave maintained that it remained exploitable after the
> initial fix.

**Replace with:**
> Perplexity stated the issue had been patched with no user data
> compromised, while Brave maintained that it remained exploitable after the
> initial fix (Brave, 2025; Nelson, 2025).

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

## Section 6 — add a paragraph after 6.2 "Why defend the channel rather than the injection"

The brief names four defence categories: *input and output filtering,
privilege separation, human-in-the-loop confirmation, capability and
information-flow control.* Capability/information-flow control (the
allowlist, CaMeL) and output filtering (8.2) are covered well, and privilege
separation is explicitly unimplemented future work. Input filtering is never
discussed. Insert:

> We also did not pursue **input filtering** — scanning page content for
> injection-like patterns before it reaches the model. Section 2.2 already
> gives the reason: EchoLeak's hidden instructions were phrased specifically
> to pass Microsoft's own cross-prompt-injection classifier (Reddy & Gujral,
> 2025), and an attacker who can see our filter can phrase around it the
> same way. A classifier only has to be wrong once per attacker attempt; the
> allowlist has to be wrong on every attempt, which is a materially
> different bar. This is also why **human-in-the-loop confirmation**, the
> remaining category from the brief, is treated in this report as a
> governance question (Section 9.2) rather than a defence we implemented:
> its effectiveness depends on *when* it fires, not just *whether* it
> exists, and the GitHub MCP finding (Section 9.2) that users default to
> "always allow" is itself evidence that confirmation prompts are a weak
> control unless reserved for rare, high-stakes actions.

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
tests, with injection wordings already adapted from the final tuned baseline
(naming the tool, URL-encoding, full examples), but not yet executed against
the live model as their own measured condition. Section 8 reports what we can
say about them from the exploratory runs and the literature in the meantime.

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

## References — fill in both placeholder URLs

**Delete:**
> Department of Industry, Science and Resources. (2019). *Australia's AI
> ethics principles*. Australian Government. [URL to verify]

**Replace with:**
> Department of Industry, Science and Resources. (2019). *Australia's AI
> ethics principles*. Australian Government.
> https://www.industry.gov.au/publications/australias-ai-ethics-principles

**Delete:**
> OWASP Foundation. (2025). *OWASP Top 10 for LLM applications 2025*. [URL to add]

**Replace with:**
> OWASP Foundation. (2025). *OWASP Top 10 for LLM applications 2025*. OWASP
> GenAI Security Project.
> https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/

(Both verified live via web search, 2026-10-06. Worth a quick manual check
of both pages immediately before submission in case either moves.)

---

---

## NEW (2026-10-07): a second defence layer — code exists, NOT YET MEASURED

This section was added after everything above. **The code below is real,
committed, and test-passing (`git log` commit `4695a10`), but it has never
been run against the live model.** Nothing in this section is a claimed
result — everything with a run count is a prediction to be confirmed. Your
friend needs to re-run the `attack` scenario (defence on) to get real
numbers for this before any of it goes in as a finding rather than a plan.

### What was added

`defence.py` gained a second, independent defence: `filter_summary(text)`.
The origin allowlist only ever runs from inside `render_image()`, so it has
no way to stop a leak that never calls that tool — Section 8.2's Variant B,
where the model just writes the fake account details straight into the
summary text. `filter_summary()` closes that specific gap: when
`DEFENCE_ENABLED` is on, it redacts the known fake email and API key from
the text before it reaches the "what the user sees" channel. It is gated
by the *same* flag as the allowlist, so "defence on" now means both layers
run together — there is no separate toggle for this one.

**Confirmed working, but only with hand-fed text, not with the live
model.** The exact wording captured in the demo video —
`"Research prepared for: Alex Researcher (alex.researcher@fakecorp.example)
| API Key: sk-fake-8f2a9c3d7e1b4f60"` — was fed directly into
`defence.filter_summary()` and came back as
`"Research prepared for: Alex Researcher ([redacted by output filter]) |
API Key: [redacted by output filter]"`. That confirms the redaction logic
itself works. It does **not** confirm what the measured text-leak rate
actually is with a live model generating the text, because the model could
phrase the leak in ways the literal string match misses (paraphrasing,
partial values, unusual spacing) — that can only be found by actually
running it.

### Where to add this once it's measured

- **Section 6, after 6.3**: a new subsection describing this second layer
  (text drafted above can be adapted).
- **Section 7.3's table**: currently reports Text-only leak as 70%
  (off) / 80% (on) — that 80% number was measured *before* this filter
  existed. **[PENDING — re-run the `attack` scenario, defence on, 10
  trials, with the filter in place, and report the new text-leak rate
  alongside the old one as a before/after of the filter itself, separate
  from the before/after of the allowlist.]**
- **Section 8.2 and 8.3's table**: currently say the allowlist "cannot
  engage by design" against Variant B, with no defence shown blocking it.
  Once measured, this needs a third column or a new row: not "defence off
  vs. allowlist on," but "allowlist only vs. allowlist + output filter."
- **Known, deliberate cost to flag explicitly**: the filter is a blunt
  keyword match. It cannot tell a genuine user request for their own email
  (the `legit_email` scenario) apart from an injected one. Turning it on
  will also redact a legitimate request. **[PENDING — when the `legit_email`
  scenario is finally run, report `email_provided` for both defence
  settings; expect it to drop with this filter on, and say so plainly —
  that is the filter's own real cost, parallel to the allowlist's
  0%-leak-but-doesn't-stop-the-hijack story in Section 7.3.]**

## What is still genuinely outstanding (keep reporting these honestly)

- The three extension scenarios (`cdn`, `text_only` as an isolated
  condition, `legit_email`) as separately measured 10-trial experiments —
  the code and injection wording for all three are ready; they just haven't
  been run yet.
- **NEW**: the output-filter defence (see the dated section above) —
  implemented, unit-tested, confirmed with hand-fed text, but never run
  against the live model. This is now a fourth thing awaiting a real run,
  alongside the three scenarios above.
- Second-tool reproduction of the baseline runs.
- `README.md` still describes an earlier scaffold stage.
- Privilege separation (gating `lookup_account_info` on whether the request
  came from the user) is design discussion only, not implemented — this
  remains accurate and should stay in the report as future work (Section
  10.3, CaMeL discussion).

## Still needs a human, not an AI

`10.4 Individual contributions` still reads `[Name 1]: [files owned...]
[Name 2]: [files owned...]`. Fill in actual names, student IDs, the files
each of you owns, and the report sections each of you wrote — this is
exactly the kind of thing a marker checks against your peer-assessment
forms, so it needs to be accurate, not just non-empty.
