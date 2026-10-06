# ScoutMind report: corrections part 2 (coverage + referencing)

**Why this file exists.** `report_corrections_v2.md` fixed the report's
biggest problem — it described completed work (the formal measured
experiment, the three interfaces) as outstanding. This file fixes the
remaining criteria-based gaps found in a full pass against the assignment
brief: one topic-coverage gap, one thin defence category, an orphan
citation, and two placeholder URLs. Apply both files together.

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

## Section 6 — add a short paragraph after 6.2 "Why defend the channel rather than the injection"

The brief names four defence categories: *input and output filtering,
privilege separation, human-in-the-loop confirmation, capability and
information-flow control.* Your report covers capability/information-flow
control (the allowlist, CaMeL) and output filtering (8.2) well, and
privilege separation explicitly as unimplemented future work. Input
filtering is never discussed. Insert:

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

## Still needs a human, not an AI

`10.4 Individual contributions` still reads `[Name 1]: [files owned...]
[Name 2]: [files owned...]`. Fill in actual names, student IDs, the files
each of you owns, and the report sections each of you wrote — this is
exactly the kind of thing a marker checks against your peer-assessment
forms, so it needs to be accurate, not just non-empty.
