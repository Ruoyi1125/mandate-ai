# MANDATE | 代言权

AI代理表达的来源、代表性与授权审计系统。

第一阶段只建立稳定、清晰、可扩展的 Python 项目骨架。当前版本使用 `MockProvider`，不调用真实 LLM，不需要 API Key。

## Requirements

- Python 3.11
- Streamlit
- Pydantic v2
- pandas
- scikit-learn
- sentence-transformers
- Plotly
- PyYAML
- pytest

## Installation

```bash
cd mandate-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

## Test

```bash
pytest
```

## Phase-One Scope

Implemented:

- Typed Pydantic v2 schemas with validation.
- YAML-backed authorization rule evaluation.
- Deterministic `MockProvider`.
- Minimal pipeline orchestration.
- Minimal Streamlit page for `REAL_GROUP`.
- Unit tests for schemas, authorization, and pipeline.

Not implemented yet:

- Real LLM prompts or provider integrations.
- Real embedding model execution.
- Production clustering and omission detection.
- PDF export or signed credential issuance.
- Authentication, persistence, and upload storage workflows.
