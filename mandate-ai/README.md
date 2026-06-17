# MANDATE | 代言权

AI代理表达的来源、代表性与授权审计系统。

当前版本实现了 `REAL_GROUP` 模式的来源追踪与意见遗漏检测。系统使用 `MockProvider` 和本地规则，不调用真实 LLM，不需要 API Key。

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

页面支持逐行输入原始意见，或上传 CSV。CSV 至少包含：

```text
source_id,text
```

可选字段：

```text
participant_id,consent_id
```

演示数据在 `data/demo/` 中。

## Test

```bash
pytest
```

## Current Scope

Implemented:

- Typed Pydantic v2 schemas with validation.
- YAML-backed authorization rule evaluation.
- Deterministic `MockProvider`.
- Rule-based atomic claim extraction.
- Local TF-IDF source retrieval with a pure-Python fallback when scikit-learn is unavailable.
- Rule-based support classification.
- Quantifier and degree-word risk checks.
- Source evidence bundles for front-end display.
- Rule-based `OpinionUnit` extraction from original source records.
- Topic clustering for original opinions.
- Omission detection with `COVERED`, `WEAKENED`, `DISTORTED`, and `OMITTED`.
- Detection of minority but normatively salient voices.
- "VOICES LOST IN SUMMARY" display for real original viewpoints omitted from the AI summary.
- Deterministic authorization boundary assessment.
- Structured representation passport export as JSON, Markdown, and HTML.
- Conservative faithful revision generation.
- Streamlit source tracing page for `REAL_GROUP`.
- Demo data under `data/demo/`.

Not implemented yet:

- Real LLM prompts or provider integrations.
- Downloaded embedding model execution.
- Production-grade semantic clustering.
- PDF export or signed credential issuance.
- Authentication, persistence, and upload storage workflows.
- Formal legal authorization determinations.
- Personal and synthetic-group modes.
