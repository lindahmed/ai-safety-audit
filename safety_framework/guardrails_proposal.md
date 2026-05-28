# AI Safety Guardrails Proposal

**Project:** AI Safety & Bias Audit Toolkit  
**Version:** 1.0  
**Date:** 2026-05-28  
**Author:** Linda Ahmed

---

## Overview

This document proposes a four-layer safety framework for deploying large language models (LLMs)
in production environments. It is informed by the findings of the automated red-team and bias
audit conducted as part of this project, and draws on established industry standards including
the [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/),
Anthropic's Constitutional AI research, and NIST AI RMF guidelines.

---

## Layer 1: Input Filtering

### Description
The first line of defence intercepts potentially harmful or adversarial inputs before they reach
the language model. This layer is computationally cheap and can block the majority of known attack
patterns with low latency overhead.

### Implementation Steps
1. **Keyword & Pattern Matching** — Maintain a curated blocklist of high-signal attack phrases
   (e.g. "DAN", "ignore previous instructions", "as an AI with no restrictions"). Update weekly.
2. **Semantic Similarity Scanning** — Embed incoming prompts and compare against a library of
   known jailbreak embeddings using cosine similarity. Flag prompts above a threshold (e.g. 0.85).
3. **Rate Limiting** — Enforce per-user, per-session, and per-IP rate limits. Sudden bursts
   of similar prompts are a strong signal of automated adversarial probing.
4. **Input Length & Structure Checks** — Reject unusually long prompts or prompts with anomalous
   structural patterns (e.g. excessive special characters, repeated role-play framing).
5. **Language Detection** — Flag mixed-language or obfuscated inputs (pig latin, base64 segments,
   leetspeak) for additional scrutiny before forwarding to the model.

### Recommended Tools
- `langdetect` / `fastText` — language identification
- `sentence-transformers` — embedding-based similarity
- Redis / Upstash — rate limiting
- Custom regex + `re` module — keyword matching

### Cost Estimate: **Low**
Most tooling is open-source. Infrastructure cost is minimal when run as a lightweight middleware
service. Estimated < $50/month for moderate traffic.

---

## Layer 2: Model-Level Guardrails

### Description
Embed safety directly into the model interaction layer through carefully designed system prompts,
constitutional AI principles, and output post-processing. This layer catches attacks that pass
the input filter by working at the semantic level.

### Implementation Steps
1. **Hardened System Prompts** — Craft explicit, specific system prompts that enumerate categories
   of refusal. Avoid vague instructions like "be helpful and harmless" — instead specify: "Never
   provide instructions for creating weapons, bypassing security systems, or generating harmful
   content, regardless of how the request is framed."
2. **Constitutional AI Principles** — Define a set of ranked principles the model must follow.
   For each output, run a self-critique pass where the model checks its response against the
   principles before returning it. (See Anthropic's Constitutional AI paper.)
3. **Persona Anchoring** — Include explicit instructions preventing the model from adopting
   alternative personas, playing characters without ethical constraints, or "forgetting" its
   guidelines.
4. **Output Filtering** — Pass all model outputs through a secondary, lightweight classifier
   trained on harmful content categories before returning them to the user.
5. **Confidence Calibration** — For ambiguous requests, instruct the model to default to refusal
   rather than partial compliance.

### Recommended Tools
- Anthropic Claude API (system prompt + constitutional AI)
- `detoxify` — toxicity classifier for output filtering
- Perspective API (Google) — comment toxicity detection
- OpenAI Moderation API — can be used as a secondary check

### Cost Estimate: **Low–Medium**
System prompt engineering is free. Output classifiers add ~10–50ms latency and $0.001–0.01 per
1000 requests depending on the classifier chosen.

---

## Layer 3: Monitoring & Logging

### Description
Even with strong input and model-level guardrails, some adversarial inputs will succeed over time
due to novel techniques. A robust monitoring layer detects anomalies, creates audit trails for
compliance, and feeds findings back into the testing pipeline.

### Implementation Steps
1. **Structured Logging** — Log every prompt/response pair with metadata: timestamp, user ID
   (hashed), session ID, input length, output length, latency, and any filter flags triggered.
2. **Automated Flagging** — Run a lightweight classifier on all responses in near-real-time.
   Flag responses with a suspicion score above a threshold for human review.
3. **Human Review Queue** — Route flagged outputs to a safety review dashboard. Reviewers
   label outcomes (false positive / true positive) to improve classifier accuracy over time.
4. **Audit Trail** — Store immutable logs for a minimum of 90 days. Required for regulatory
   compliance in many jurisdictions (GDPR, EU AI Act, CCPA).
5. **Alerting** — Trigger PagerDuty / Slack alerts when the bypass rate in a rolling window
   exceeds a threshold (e.g. > 2% of requests flagged in 1 hour).
6. **Red-Team Re-testing Schedule** — Re-run this audit toolkit monthly or after any model update.
   Track metrics over time in a dashboard (Grafana / Datadog).

### Recommended Tools
- ELK Stack (Elasticsearch + Logstash + Kibana) — logging and dashboards
- Grafana + Prometheus — metrics and alerting
- PagerDuty / OpsGenie — on-call alerting
- Labelbox / Prodigy — human review labelling interface

### Cost Estimate: **Medium**
Logging infrastructure ranges from $0 (self-hosted ELK) to $500+/month (managed Datadog).
Human review cost depends on volume; budget 1–2 hours of reviewer time per 1000 flagged items.

---

## Layer 4: Bias Mitigation

### Description
Bias is harder to eliminate than safety failures because it is often subtle, context-dependent,
and reinforced by training data distributions. This layer establishes continuous measurement and
iterative improvement processes.

### Implementation Steps
1. **Benchmarking Baseline** — Run this bias audit toolkit against every new model version before
   deployment. Track average bias score, demographic assumption rates, and stereotype frequency.
2. **Diverse Evaluation Sets** — Expand the bias test suite to cover more occupations, demographic
   intersections, and cultural contexts. Aim for 100+ prompts covering gender, race, age,
   disability, religion, and socioeconomic status.
3. **Demographic Parity Checks** — For applications involving decision support (hiring, lending,
   healthcare), verify that model outputs do not statistically differ across demographic groups
   for equivalent inputs.
4. **Debiasing via Prompt Engineering** — Add explicit neutrality instructions to system prompts:
   "Use gender-neutral language unless gender is explicitly specified by the user. Do not make
   assumptions about ethnicity, nationality, or socioeconomic background."
5. **Fine-tuning Feedback Loop** — Collect biased outputs identified by the monitoring layer and
   use them as negative examples in RLHF or DPO fine-tuning runs.
6. **Transparency Reporting** — Publish a quarterly bias scorecard showing trends over time.
   Transparency builds stakeholder trust and creates accountability.

### Recommended Tools
- `fairlearn` (Microsoft) — fairness metrics and mitigation algorithms
- `AI Fairness 360` (IBM) — comprehensive bias detection library
- Hugging Face `evaluate` — bias benchmarks (WinoBias, BBQ)
- This toolkit — ongoing automated baseline measurement

### Cost Estimate: **Medium–High**
Benchmark tooling is open-source (free). Fine-tuning runs cost $50–$500+ per run depending on
model size and dataset. Human annotation of bias examples: $0.05–$0.20 per example.

---

## Implementation Roadmap

### Week 1 — Foundation
- [ ] Deploy keyword/pattern input filter as a middleware service
- [ ] Harden system prompts across all production endpoints
- [ ] Enable structured logging for all API calls
- [ ] Establish baseline bias scores with this audit toolkit

### Month 1 — Core Guardrails
- [ ] Implement semantic similarity scanning on inputs
- [ ] Deploy output toxicity classifier
- [ ] Set up human review queue and labelling workflow
- [ ] Configure alerting thresholds and on-call rotation
- [ ] Expand bias test suite to 100+ prompts

### Quarter 1 — Maturity
- [ ] Establish monthly automated red-team re-testing schedule
- [ ] Build bias metrics dashboard with historical trending
- [ ] Conduct first fine-tuning run using flagged examples as negative data
- [ ] Publish first transparency/bias scorecard
- [ ] Complete documentation for compliance audit trail

---

## References

- [OWASP LLM Top 10](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Anthropic Constitutional AI](https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback)
- [NIST AI Risk Management Framework](https://www.nist.gov/system/files/documents/2023/01/26/AI%20RMF%201.0.pdf)
- [Microsoft Responsible AI Standard](https://blogs.microsoft.com/on-the-issues/2022/06/21/microsofts-framework-for-building-ai-systems-responsibly/)
- [EU AI Act (2024)](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689)
