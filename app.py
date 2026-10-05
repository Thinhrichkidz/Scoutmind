"""
ScoutMind user interface (Streamlit): a chat-style research assistant, with a
comparison view next to every answer.

Run with:  streamlit run app.py

Left of each answer: what the user saw (the summary).
Right of each answer: what actually happened (every tool call, in order).
For the attack demo, start attacker/attacker_server.py in another terminal
first, so a leaked request has somewhere to arrive.

Everything the model or a web page wrote is shown with st.text, never
st.write or st.markdown. Markdown can contain an image link, and the browser
would fetch it while drawing the page: a second way to leak data that no
tool-level defence can see.
"""

import streamlit as st

import agent
import comparison
import config

# Wide layout, so the two comparison columns have room (must be the first
# Streamlit call).
st.set_page_config(layout="wide")
st.title("ScoutMind research assistant")

# The defence toggle for live demos. It is applied to each run below.
defence = st.sidebar.checkbox("Defence enabled (origin allowlist)", value=False)
include_attack_page = st.sidebar.checkbox(
    "Search can find the booby-trapped page", value=True
)
st.sidebar.caption(
    "For the attack demo, run `python attacker/attacker_server.py` in another "
    "terminal first."
)

# Streamlit re-runs this whole script on every interaction, so the chat is
# kept in session_state.
if "history" not in st.session_state:
    st.session_state.history = []

query = st.chat_input("Ask a research question")
if query:
    result = None
    error = ""
    # One lock for the process-wide defence setting (see config.py), so another
    # browser tab cannot change it while this agent is running.
    with config.DEFENCE_LOCK:
        previous_setting = config.DEFENCE_ENABLED
        config.DEFENCE_ENABLED = defence
        try:
            with st.spinner("The agent is working (this can take a few minutes)..."):
                result = agent.run_agent(query, include_attack_page=include_attack_page)
        except Exception as e:  # last resort; run_agent reports model errors itself
            error = str(e)
        finally:
            config.DEFENCE_ENABLED = previous_setting
    st.session_state.history.append(
        {"query": query, "defence": defence, "result": result, "error": error}
    )

for item in st.session_state.history:
    with st.chat_message("user"):
        st.text(comparison.wrap_text(item["query"]))

    with st.chat_message("assistant"):
        if item["error"]:
            st.text(comparison.wrap_text("The agent failed: " + item["error"]))
            continue

        result = item["result"]
        st.caption("Defence was " + ("ON" if item["defence"] else "OFF") + " for this answer.")
        left, right = st.columns(2)

        with left:
            st.subheader("What the user saw")
            shown = comparison.shown_text(result)
            if shown:
                st.text(comparison.wrap_text(shown))
            else:
                st.text(comparison.wrap_text("The agent did not produce a summary."))

        with right:
            st.subheader("What actually happened")
            for finding in comparison.describe_run(result):
                st.text(comparison.wrap_text("- " + finding))
            rows = comparison.trace_rows(result["trace"])
            if rows:
                st.dataframe(rows)  # a table of plain cells; nothing is rendered as markdown
            with st.expander("Full tool results"):
                for entry in result["trace"]:
                    st.text(f"Step {entry['step']}: {entry['tool']}")
                    st.text(comparison.wrap_text(entry["result"], 110))
