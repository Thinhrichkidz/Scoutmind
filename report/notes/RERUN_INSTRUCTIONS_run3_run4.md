# Instructions for Claude Code: re-run Run 3 and Run 4 on the fixed code

Hand this file to your Claude Code session and ask it to follow it exactly
(e.g. "read report/notes/RERUN_INSTRUCTIONS_run3_run4.md and do what it
says"). It assumes it is running on the machine that has successfully run
qwen3:8b for this project before (NOT an 8GB-RAM laptop — that was tried
and one trial alone took 109 minutes and still timed out, so don't attempt
this on constrained hardware).

## Why this is needed

`report/notes/experiment_log.md`, Run 3 (core attack, defence on) and
Run 4 (`legit_email`, defence on) were both measured just before a bug fix:
`filter_summary` used to run only on the `save_summary` text path, so a run
that ended in a plain-text reply (`no_tool_call`) bypassed the output
filter entirely. That fix is committed (`agent.py`'s `model_text` /
`model_text_raw` split) and confirmed working in a later run (Runs 5/6,
`cdn` and `text_only`), but Run 3 and Run 4 themselves were never re-run on
the fixed code. They are the last two `[PENDING]`/"preliminary" items in
`report/ScoutMind_report_v2.docx`.

## Pre-flight checks (do these first, stop and report back if any fail)

1. `git status` — confirm no uncommitted changes you don't recognise.
   `git pull` to make sure you're on the latest `main`.
2. Confirm the fix is actually present: `grep -n "model_text_raw" agent.py`
   should show it. If it's missing, stop — you're on the wrong commit.
3. Confirm the system prompt is the old one (not the stricter `code_final`
   one): `grep -A3 "^SYSTEM_PROMPT" agent.py` should read "...write a
   summary and submit it with save_summary", not "You MUST submit your
   final answer only by calling the save_summary tool".
4. `python3 -m unittest discover -s tests` — should pass (206 tests as of
   this writing; if the number has changed that's fine, just confirm OK).
5. Confirm Ollama is running with `qwen3:8b` pulled (`ollama list`), and
   that ports 9000 and 8001 are free (`lsof -i :9000 -i :8001` — kill any
   stale `attacker_server.py` / `image_source_server.py` processes first,
   they're safe to kill, no state is lost).
6. Back up the two files the commands below will overwrite, so a crash
   can't lose the pre-fix numbers before they're safely in git history
   (they already are, in `report/notes/experiment_log.md`, but back up
   anyway): `cp results/defence_results.csv /tmp/defence_results_backup.csv`
   (for the attack re-run) — `legit_email`'s own CSV is scenario-specific
   and doesn't collide with this one.

## The two runs (run sequentially, not in parallel — they share ports 9000/8001)

```bash
python3 run_experiments.py --scenario attack --only on --trials 10 --overwrite
python3 run_experiments.py --scenario legit_email --trials 10 --overwrite
```

Each takes roughly 20–35 minutes on hardware that has run this before.
If a single trial takes more than ~5 minutes, something is wrong —
stop and report rather than letting it run for hours.

## After both complete

1. Archive the raw outputs the same way Runs 1–6 were archived: copy the
   relevant CSVs, attacker logs, and `results/thinking_log.txt` into a new
   folder `results/runs/versionA_oldprompt_defence_on_postfix_2026-XX-XX/`
   (use today's date), matching the structure of the existing
   `results/runs/versionA_oldprompt_defence_on_2026-10-09/` folder from
   Run 3.
2. Append a new dated entry to `report/notes/experiment_log.md`, in the
   same style as the existing Run 0–6 entries: a `## Run 7: ...` heading,
   the command(s) run, a results table, and a "Reading it" section. Two
   things the write-up specifically needs to say:
   - Whether the core attack's defence-on text-leak rate is still 0/10
     visible / ~9/10 attempted (the report currently predicts it will be,
     since Run 3's own 10/10 trials all finished via `save_summary` and
     so never hit the bug) — confirm or correct that prediction.
   - Whether `legit_email`'s "user received their email" rate is now 0/10
     with the defence on (down from the pre-fix 2/10), which is the
     report's explicit prediction for what the fix should do here.
3. Update `report/notes/experiment_log.md`'s "Open decisions" item 5 and
   `report/notes/TEAM_SUMMARY.md` section 6 ("What is left to do") to mark
   this done, the same way earlier items were marked `DONE` / `FIXED`.
4. Commit and push to `main` with a commit message describing what was
   measured (follow the style of your own earlier commits, e.g. "Record
   Run 7: core attack and legit_email, defence on, after the plain-reply
   filter fix").

## What NOT to do

- Don't touch `report/ScoutMind_report_v2.docx` or `report/notes/report_v0.md`
  — those are maintained from the other side (a different Claude Code
  session) and will be updated there once this data is pulled in, to avoid
  two sessions editing the same binary file.
- Don't change the payload wording, the system prompt, or any other code —
  this is a measurement run on the code as it stands, not a development
  task.
