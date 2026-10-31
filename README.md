# PayIntel AI — Historical RFP Portfolio Gap Analysis

KSBL Option B prototype. All bank names, RFPs and portfolio documents are fictional. The tool counts distinct historical RFPs per requested capability, compares explicit documented portfolio capabilities, and recommends missing capabilities for human review. **It does not forecast future demand.**

## Windows setup

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If heavy RAG packages take too long, first install `streamlit pandas openpyxl requests PyMuPDF python-docx pytest` and launch the baseline. `rag_engine.py` contains optional ChromaDB semantic retrieval, while the baseline relies on deterministic normalized capability matching and cited source filenames. Ollama `llama3.2:3b` powers optional natural-language summaries only.

## Evaluation

Run `.\.venv\Scripts\python.exe -m pytest -q` and execute `evaluation.ipynb`. The gold labels are synthetic ground truth, not real-world validation. Evaluate accuracy and error rates on additional held-out samples before claiming production readiness.

## Five-minute demo

0:00–0:40 Explain missed opportunities from scattered historical RFPs.
0:40–1:20 Show synthetic 15 RFPs and 5 product files.
1:20–2:30 Click Analyze and show distinct-RFP demand counts.
2:30–3:30 Show missing portfolio capabilities and supporting filenames.
3:30–4:15 Export Excel and explain human review.
4:15–5:00 Show notebook tests, limitations and privacy safeguards.

## Hosting note

A Streamlit Community Cloud deployment requires publishing this repository and may have resource constraints. The app's baseline works without Ollama or ChromaDB; optional local Ollama is not accessible from public cloud hosting. Do not upload confidential data.
