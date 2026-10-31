# ReinCrew - AI Personalized Interview Platform (Streamlit)

Built on top of your repo `acpajay-7/local_mosel_reincrew`. **Read "Status" first - it says what was and was not verified.**

## Status (honest)
| Area | Status |
|---|---|
| Core logic: scoring, question bank, selection, DB, reports, mode isolation | **Tested** - 41 `unittest` tests pass (network mocked) |
| Streamlit UI (`app.py`) | **Syntax-checked only. Never run.** Streamlit was not installable where this was built. Expect small bugs on first run - send me the traceback and we fix it step by step |
| Webcam preview, browser text-to-speech | Written, **untested** (needs a real browser) |
| Microphone recording (`st.audio_input`) + Faster-Whisper | Written, **untested** |
| OpenRouter / DeepSeek calls | Written, **untested against the live service** |
| Ollama calls | Written, **untested against a live Ollama** |
| "Zero network requests" in Local Mode | Code refuses non-loopback URLs (tested). **Network-level proof is still your job** - see below |
| Video recording | **Not implemented.** Webcam is a live preview only. Audio is recorded per question, transcribed, then discarded |
| Continuous WebRTC conferencing | Not implemented (question-by-question recording, as agreed) |

## What changed vs your repo
- Your repo is **FastAPI**; this is a **Streamlit** app (as you requested). `app.py`/`templates/` of the old project are not used.
- **Preserved:** your 5 questions (stored in `data/seed_questions.json`, `source=original`) and `score_answer()` / `normalize()` and the 60/25/15 weights (`reincrew/scorer.py`, logic unchanged).
- `local_ai.py` extended: same Ollama prompt idea + loopback-only guard + availability check. `final_score` is recomputed with the 60/25/15 weights in every mode so scores are comparable.
- Your repo contained **no OpenRouter interviewer file**, so API mode is **new code**, not a preserved one. If you have that code elsewhere, send it and I'll merge it.
- 23 new starter questions (Data Science, Web, CS, Cybersecurity, Cloud, Mechanical, Business, HR) were written by me. **Review them** (`source=seed`). Streams with few questions will report a shortage rather than borrowing unrelated questions.

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env             # then edit .env (Mac/Linux: cp)
streamlit run app.py
```
Open http://localhost:8501 (camera/mic work on localhost; remote hosting needs HTTPS - Streamlit Cloud provides it).

### Local AI mode (Ollama)
1. Install Ollama (https://ollama.com/download), then `ollama pull qwen2.5:3b`, keep it running.
2. Choose **Local AI Mode** in the app. The Config page shows whether the model is found. If not, the **rule-based scorer** is used and each result is labelled `rule_based_fallback`. It never silently switches to an API.
3. First transcription downloads the Faster-Whisper model (`base.en`) - do this once while online.

### API mode
Put `OPENROUTER_API_KEY` in `.env` (or Streamlit secrets). Model: `deepseek/deepseek-chat`. Answers are sent to OpenRouter. Without a key the app shows a warning and uses rule-based scoring.

### Hybrid mode
Local scoring during the interview, then **one** batched OpenRouter call at the end (cached by content hash). Needs the API key. **Not offline.** If the API call fails, local scores are kept and flagged.

## Verify Local Mode makes no external calls (do this yourself)
Logs prove nothing. Install models first, then: (1) disconnect Wi-Fi / block outbound traffic with Windows Firewall, run a full Local-mode interview; (2) optionally watch with Wireshark or `netstat -b` during the interview and confirm only `127.0.0.1:11434` appears. Record the results.

## Question bank
Stored in SQLite (`data/reincrew.db`, created on first run, seeded once). Admin page (set `ADMIN_PASSWORD`): approve/edit/reject/delete, add questions. AI-generated questions are validated, de-duplicated, saved as **pending**, and are never used until an admin approves. Only questions and reference answers are saved - never candidate answers.
The data layer is isolated in `reincrew/db.py` (plain SQL) so PostgreSQL can replace it later.

## Privacy
Candidate data is keyed by email; history shows only the email used in the current browser session. "Delete my data" removes a candidate's profile, answers and reports; Admin has a 90-day purge. There is **no login system** - do not use for real hiring decisions without adding authentication.

## Deploy to Streamlit Community Cloud
1. Push to GitHub (`.env` and the DB are git-ignored). 2. share.streamlit.io -> New app -> `app.py`. 3. App settings -> Secrets: add `OPENROUTER_API_KEY` and `ADMIN_PASSWORD`.
**Cloud limits:** disk is ephemeral, so SQLite data resets on restart - use a hosted PostgreSQL for real persistence (requires porting `db.py`). A Ollama running on your PC is **not reachable** from Streamlit Cloud; Local mode there needs a self-hosted server with Ollama (then `OLLAMA_URL` must still be loopback - the guard blocks remote hosts by design, so deploy the app and Ollama on the same machine).

## Tests
```bash
python -m unittest discover -s tests -t .       # or: pip install pytest && pytest
```

## Layout
`app.py` UI · `reincrew/` (`scorer, db, selector, question_bank, engine, local_ai, api_ai, prompts, transcription, report, profile, streams, config`) · `data/seed_questions.json` (+`build_seed.py`) · `tests/`

## Troubleshooting
- *Camera blocked:* use localhost or HTTPS; allow permissions. - *No transcript:* install `faster-whisper`, check mic, or type the answer. - *Ollama not reachable:* start Ollama, `ollama list`. - *Shortage note:* add questions for that stream in Admin.

## Updated candidate interview experience
The candidate-facing interview page now uses a browser voice component (`frontend/index.html`):
- Candidate clicks **Start interview** once on the review screen.
- The browser requests camera/microphone permission; this permission prompt is controlled by the browser and must be accepted.
- ReinCrew speaks each question, then starts microphone recording automatically.
- When the candidate stops speaking for about 2.8 seconds, the recording is stopped and sent to Faster-Whisper for transcription.
- The transcript is evaluated and saved automatically, then the next question loads. No keyboard key or per-question submit button is required.
- A 120-second maximum recording guard and a **Finish answer now** button are available. A typed-answer fallback appears if microphone access or transcription fails.

**Important limitations:** silence detection can submit early if the candidate pauses for several seconds mid-answer; speak continuously or use **Finish answer now** when done. Browser speech synthesis may be blocked or unavailable on some devices; the question remains visible and recording still starts. This component records audio only. Camera is a local preview and is not recorded or uploaded. Test on HTTPS (or localhost) in Chrome/Edge and confirm browser camera/microphone permissions before deployment.


## v2 interview flow (one-to-one)
Candidate clicks **Start interview** once. After that the app runs itself: the interviewer greets by name, speaks each question, listens, detects the end of the answer (about 3 s pause), transcribes, evaluates, says a short acknowledgement and asks the next question. After the last answer the report appears. One persistent browser component keeps mic/camera/voice permission for the whole interview. If nothing is heard it asks again (twice), then offers a typed answer. Sidebar navigation is hidden during the interview.
Default local model is now `qwen2.5:3b` (the 0.6B model was too weak to grade reliably). `think:false` is sent so reasoning models answer JSON directly.
Verification note: backend tests pass (43). The Streamlit UI and browser voice component could not be run in the build environment (no network / browser) - test once on localhost in Chrome or Edge.
