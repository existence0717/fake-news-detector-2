# I2C3 (IICCC) — Product Requirements Document & Technical Roadmap

**Document Version:** 1.0  
**Last Updated:** March 1, 2026  
**Purpose:** Step-by-step plan to evolve the current prototype into a production-ready AI misinformation detection system

---

## Part 1: Current State Assessment

### ✅ What You Have Built (Working)

| Component | Status | Notes |
|-----------|--------|-------|
| **Dashboard** | ✅ Working | Streamlit UI, metrics, filters, charts, live threat stream |
| **Listener** | ✅ Working | Polls YouTube, RSS feeds, Google Trends, Hacker News |
| **Risk Scoring** | ✅ Working | Panic, credibility, virality, keyword, composite scores |
| **AI Classification** | ✅ Working | Groq + Llama 3.1 for text → verdict (DEEPFAKE, SCAM, etc.) |
| **Database** | ✅ Working | SQLite (`content_log`), basic schema |
| **Virality Logic** | ✅ Working | YouTube views/hour, spike thresholds (100 views/hr, 50K views) |

### ❌ Gaps vs. Full PRD

| Requirement | Current State | Target State |
|-------------|---------------|--------------|
| **Platforms** | YouTube, RSS, HN, Trends | + Facebook, Instagram, WhatsApp (metadata) |
| **Deepfake Detection** | Text-only (LLM guess) | Image/video/audio analysis |
| **Multilingual** | English only | Hindi, Tamil, Telugu, Bengali, etc. |
| **Database** | SQLite | MySQL (scalable) |
| **ML Layer** | LLM API only | BERT/transformer fine-tuned models |
| **Explainability** | None | Audit logs, feature importance |
| **Dissemination Control** | None | Hold/delay/alert based on verdict |
| **Alert Generation** | None | Multilingual, neutral, factual alerts |
| **News API** | Key loaded, not used | Integrate for verified/non-verified sources |

---

## Part 2: Phased PRD — Step-by-Step Plan

### Phase 0: Stabilize & Clean (1–2 days)

**Goal:** Fix known issues, standardize naming, improve dev workflow.

| Step | Task | Details |
|------|------|---------|
| 0.1 | Rename `listerner.py` → `listener.py` | Fix typo; update imports/references |
| 0.2 | Use `keys.env` consistently | Confirm `load_dotenv("keys.env")` works; add `keys.env.example` |
| 0.3 | Add `.env` to `.gitignore` | Already present; verify `keys.env` is excluded |
| 0.4 | Use News API | You load `NEWS_API_KEY` but never call it; add a `scan_news_api()` in listener |
| 0.5 | Centralize config | Move RSS URLs, keywords, thresholds into `config.py` |

**Deliverable:** Cleaner codebase, News API integrated, config externalized.

---

### Phase 1: Data & Architecture Upgrade (3–5 days)

**Goal:** Migrate to MySQL, enrich schema, support real-time ingestion.

| Step | Task | Details |
|------|------|---------|
| 1.1 | MySQL setup | Install MySQL, create DB `i2c3`, user, tables |
| 1.2 | Schema design | Add columns: `credibility_score`, `virality_score`, `deepfake_score`, `corroboration_score`, `source_type`, `language` |
| 1.3 | Migration script | `sqlite_to_mysql.py` to migrate `fake_news.db` → MySQL |
| 1.4 | DB abstraction | Create `db.py` with `get_connection()`, `insert_content()`, `get_recent_threats()` |
| 1.5 | Listener + Dashboard | Switch from SQLite to MySQL via `db.py` |

**Schema (proposed):**

```sql
CREATE TABLE content_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    platform VARCHAR(50),
    source_type ENUM('official', 'media', 'citizen', 'anonymous'),
    title TEXT,
    url VARCHAR(500) UNIQUE,
    image_url VARCHAR(500),
    views INT DEFAULT 0,
    tags TEXT,
    panic_score FLOAT,
    credibility_score FLOAT,
    virality_score FLOAT,
    keyword_score FLOAT,
    deepfake_score FLOAT DEFAULT NULL,
    corroboration_score FLOAT DEFAULT NULL,
    composite_risk FLOAT,
    verdict VARCHAR(50),
    virality_vd FLOAT,
    language VARCHAR(10) DEFAULT 'en',
    ai_explanation TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_verdict (verdict),
    INDEX idx_timestamp (timestamp),
    INDEX idx_composite_risk (composite_risk)
);
```

**Deliverable:** MySQL-backed system with richer schema.

---

### Phase 2: Feed Selection Logic (2–3 days)

**Goal:** Implement formal spike detection and high-risk keyword prioritization.

| Step | Task | Details |
|------|------|---------|
| 2.1 | Spike detection | Track volume/engagement over sliding window; flag when `> 100K views in 30 min` or `> 2x baseline volume` |
| 2.2 | Keyword config | Move keywords to `config.py`; add categories: panic, political, disaster, crime, etc. |
| 2.3 | Priority queue | When spike + keyword match → process first; else process in round-robin |
| 2.4 | Baseline metrics | Store hourly aggregates per platform; use for spike thresholds |

**Deliverable:** Content selected by spike + keywords as per PRD.

---

### Phase 3: Multilingual & Enhanced AI (4–6 days)

**Goal:** Support Indian languages and improve classification.

| Step | Task | Details |
|------|------|---------|
| 3.1 | Language detection | Use `langdetect` or `fasttext` to detect language (Hindi, Tamil, Telugu, etc.) |
| 3.2 | Multilingual prompts | Update Groq prompt to handle Hinglish and regional languages |
| 3.3 | Keyword expansion | Add high-risk keywords in Hindi/regional scripts (e.g., `मौत`, `धमाका`) |
| 3.4 | BERT/transformer (optional) | Fine-tune `xlm-roberta` or `indic-bert` on labeled fake/real news; use as secondary signal |
| 3.5 | Explainability | Log `reason` from LLM; store in `ai_explanation`; show in dashboard |

**Deliverable:** Multi-language support, optional BERT, explainable outputs.

---

### Phase 4: Deepfake & Media Analysis (5–7 days)

**Goal:** Add real image/video/audio checks (not just text).

| Step | Task | Details |
|------|------|---------|
| 4.1 | Image deepfake | Use pre-trained model (e.g., `FakeImageDetector`, `DeepfakeDetection`) or API (e.g., Microsoft Video Indexer) |
| 4.2 | Thumbnail checks | For YouTube/news: download thumbnail → run deepfake model → `deepfake_score` |
| 4.3 | Video (later) | Start with frame sampling; run image model on key frames |
| 4.4 | Audio (later) | Use models for synthetic voice detection |
| 4.5 | Metadata checks | Detect EXIF/upload-date mismatches, resolution anomalies |

**Deliverable:** `deepfake_score` populated for images; placeholder for video/audio.

---

### Phase 5: WhatsApp & Social Meta (3–5 days)

**Goal:** Integrate WhatsApp metadata and social signals (no content scraping).

| Step | Task | Details |
|------|------|---------|
| 5.1 | WhatsApp Business API | If available: forward count, spread velocity, origin diversity (metadata only) |
| 5.2 | Fallback: CrowdTangle / Meta API | For Facebook/Instagram: engagement spikes, share velocity |
| 5.3 | WhatsApp risk formula | `whatsapp_risk = f(forward_count, spread_velocity, origin_diversity)` |
| 5.4 | Schema | Add `forward_count`, `origin_diversity`, `whatsapp_risk_score` |

**Note:** WhatsApp integration often requires business/enterprise approval. Start with Meta/CrowdTangle if easier.

**Deliverable:** WhatsApp/metadata risk score where APIs are available.

---

### Phase 6: Controlled Dissemination & Alerts (3–4 days)

**Goal:** Implement PRD actions and alert generation.

| Step | Task | Details |
|------|------|---------|
| 6.1 | Dissemination rules | Likely True → publish; Unverified → delay + label; Likely False/Deepfake → hold + advisory |
| 6.2 | Alert template | Neutral, short, factual; variables: `{title}`, `{verdict}`, `{risk}`, `{source}` |
| 6.3 | Multilingual alerts | Use translation API or templates in Hindi, Tamil, etc. |
| 6.4 | Alert channel | Log to DB; optionally webhook/email/Slack |
| 6.5 | Dashboard | Add “Pending Dissemination” and “Alerts Generated” sections |

**Deliverable:** Action engine + multilingual alerts.

---

### Phase 7: Production Readiness (2–3 days)

**Goal:** Deployable, maintainable system.

| Step | Task | Details |
|------|------|---------|
| 7.1 | Docker | `Dockerfile` for listener + dashboard; `docker-compose` with MySQL |
| 7.2 | Environment | Use env vars for DB, API keys, thresholds |
| 7.3 | Health checks | `/health` endpoint or periodic DB/API checks |
| 7.4 | Rate limiting | Respect API quotas; backoff on errors |
| 7.5 | Streamlit Cloud | Ensure `keys.env` → Streamlit secrets; MySQL accessible from Cloud |

**Deliverable:** Docker setup, env-based config, basic monitoring.

---

## Part 3: Technical Implementation Checklist

### Immediate (Midsem Break — ~2 weeks)

| Priority | Task | Est. Time |
|----------|------|-----------|
| P0 | Phase 0: Stabilize & Clean | 1–2 days |
| P0 | Phase 1: MySQL migration | 2–3 days |
| P1 | Phase 2: Spike + keyword logic | 2 days |
| P1 | Phase 3: Multilingual + explainability | 3–4 days |
| P2 | Phase 6: Dissemination + alerts (basic) | 2–3 days |

### Post–Midsem

| Priority | Task |
|----------|------|
| P2 | Phase 4: Deepfake detection |
| P2 | Phase 5: WhatsApp/social metadata |
| P3 | Phase 7: Docker, production deploy |

---

## Part 4: AI & ML Best Practices

1. **Separate config from code** — All thresholds, keywords, API endpoints in `config.py` or env.
2. **Log inputs/outputs** — Store prompt, model, response, and `ai_explanation` for audits.
3. **Version models** — Track which model/version produced each verdict.
4. **Fallbacks** — If LLM/API fails, use rule-based fallback (e.g., keyword-only).
5. **Evaluation** — Maintain a small labeled test set; measure precision/recall for verdicts.
6. **Explainability** — Always return a short reason; surface it in the dashboard.

---

## Part 5: File Structure (Recommended)

```
I2C3 Project/
├── config.py          # Keywords, URLs, thresholds, env vars
├── db.py              # MySQL connection, CRUD
├── listener.py        # Main ingestion loop (renamed from listerner)
├── risk_scoring.py    # RiskScorer class (unchanged)
├── dissemination.py   # NEW: Hold/delay/alert logic
├── alerts.py          # NEW: Multilingual alert generation
├── dashboard.py       # Streamlit UI
├── utils.py           # Logging, helpers
├── keys.env.example   # Template for API keys
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── PRD_Technical_Roadmap.md  # This document
└── logs/
```

---

## Part 6: Quick Wins (Do First)

1. Add `scan_news_api()` to listener using your existing News API key.
2. Create `config.py` and move `RISK_KEYWORDS`, `RSS_FEEDS`, thresholds there.
3. Add `ai_explanation` column to DB and display it in the dashboard.
4. Fix listener filename: `listerner.py` → `listener.py`.

---

## Summary

| Phase | Focus | Timeline |
|-------|-------|----------|
| 0 | Stabilize, fix typos, use News API, config | 1–2 days |
| 1 | MySQL, schema, DB abstraction | 2–3 days |
| 2 | Spike detection, keyword prioritization | 2 days |
| 3 | Multilingual, explainability | 3–4 days |
| 4 | Deepfake (image first) | 5–7 days |
| 5 | WhatsApp/social metadata | 3–5 days |
| 6 | Dissemination + alerts | 2–3 days |
| 7 | Docker, production | 2–3 days |

**Total for full system:** ~3–4 weeks.  
**Midsem focus:** Phases 0, 1, 2, 3, 6 (core experience + architecture).

Good luck with the midsem break build.
