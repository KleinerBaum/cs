# .agent/PLANS.md

Wenn eine Aufgabe >30–60 Minuten wirkt oder mehrere Module betrifft:
1) Erstelle zuerst ein ExecPlan in `.agent/execplans/<slug>.md`
2) Implementiere in kleinen, reviewbaren Schritten
3) Nach jeder Milestone: short verification + commit (wenn im Tool/Flow möglich)

Definition of Done:
- App startet: `streamlit run app.py`
- Keine ImportErrors
- `python -m compileall .` ok
