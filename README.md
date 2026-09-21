# Scoutmind

Scoutmind is a cybersecurity project scaffold for exploring attacks and defences around an AI research agent. The planned experiment compares normal research behaviour, adversarial scenarios, and behaviour with defensive controls enabled.

The sample research material covers solar trends, wind energy, and electric vehicle battery costs. A separate internal document provides a place for synthetic sensitive data in controlled experiments.

## Current status

The folder structure is in place. Python modules, test files, sample data, logs, result files, and `requirements.txt` are currently empty placeholders. Agent behaviour, attack scenarios, defensive controls, and experiment execution still need to be implemented; no experiment results are available yet.

## Project structure

```text
scoutmind/
├── agent.py                         # Planned research agent
├── tools.py                         # Planned tools available to the agent
├── defence.py                       # Planned defensive controls
├── config.py                        # Planned shared configuration
├── run_experiments.py               # Planned experiment runner
├── data/
│   ├── pages/                       # Local research page fixtures
│   │   ├── solar_trends_2026.html
│   │   ├── wind_energy_report.html
│   │   └── ev_battery_costs.html
│   └── internal_docs/
│       └── q3_cost_roadmap.txt       # Synthetic internal document fixture
├── attacker/
│   ├── attacker_server.py           # Planned local attack simulation server
│   └── attacker_log.txt             # Placeholder for simulation logs
├── tests/
│   ├── test_normal_task.py          # Planned baseline behaviour tests
│   ├── test_attack.py               # Planned adversarial scenario tests
│   └── test_defence.py              # Planned defensive control tests
├── results/
│   ├── attack_results.csv           # Placeholder for attack experiment results
│   └── defence_results.csv          # Placeholder for defence experiment results
├── report/
│   ├── notes/                      # Experiment observations and analysis
│   └── references/                 # Supporting research and citations
├── requirements.txt                # Python dependencies, to be selected
├── README.md
├── LICENSE
├── .gitattributes
└── .gitignore
```

Empty directories such as `report/notes/` and `report/references/` are not tracked by Git until files are added.

## Planned experiment workflow

1. Populate the local research pages and synthetic internal document.
2. Implement the agent, its tools, and shared configuration.
3. Establish a normal research task and record baseline behaviour.
4. Implement a controlled adversarial scenario, such as prompt injection in a research page, and observe the agent's response.
5. Add defensive controls and repeat the same scenario.
6. Save measurements in `results/` and document findings in `report/`.

The comparison should capture normal task completion, attack success, and whether defensive controls preserve legitimate research behaviour. Specific metrics and CSV columns remain to be defined.

## Development setup

Install Python 3, then create a virtual environment from the project root. A required Python version has not yet been selected.

On Windows with PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS or Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The dependency file is currently empty, so these commands only prepare an environment. Runtime configuration, test commands, and experiment commands will be documented when their implementations are available.

## Experiment scope

Use local fixtures and synthetic internal data for the attack simulations. Keep experiment configuration and observations alongside the results so baseline, attack, and defence runs can be compared consistently.

## License

This project is licensed under the [MIT License](LICENSE).
