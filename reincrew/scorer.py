"""Rule-based baseline scorer.

PRESERVED from the original repo (acpajay-7/local_mosel_reincrew/scorer.py):
normalize() and score_answer() logic and the 60/25/15 weighting are unchanged.
The original 5 hard-coded QUESTIONS now live in data/seed_questions.json.
Limitation (same as original): concept phrase groups, not true semantic understanding;
unsupported_claims / contradictions are not detected in rule mode.
"""
import re
from typing import Any

WEIGHTS = {"correctness": 0.60, "depth": 0.25, "completeness": 0.15}


def normalize(text: str) -> str:
    text = text.lower().replace("machine-learning", "machine learning")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def score_answer(question: dict[str, Any], answer: str) -> dict[str, Any]:
    text = normalize(answer)
    if not text:
        return {
            "correctness_score": 0, "knowledge_depth_score": 0, "completeness_score": 0,
            "final_score": 0, "status": "incorrect",
            "explanation": "No transcript was produced; check microphone/audio quality and retry.",
            "confidence": "low", "unsupported_claims": [], "contradictions": [], "matched_concepts": [],
            "scoring_mode": "rule_based",
        }
    groups = question["concepts"]
    matched = [c for c, phrases in groups.items() if any(normalize(p) in text for p in phrases)]
    correctness = round(100 * len(matched) / max(1, len(groups)))
    depth_matches = [t for t in question.get("depth", []) if normalize(t) in text]
    depth = round(100 * min(1, len(depth_matches) / 3))
    word_count = len(text.split())
    completeness = min(100, round(word_count / 35 * 100))
    final = round(correctness * WEIGHTS["correctness"] + depth * WEIGHTS["depth"] + completeness * WEIGHTS["completeness"])
    if correctness >= 75 and completeness >= 35:
        status = "complete"
    elif correctness >= 25:
        status = "partial"
    else:
        status = "incorrect"
    missing = [n.replace("_", " ") for n in groups if n not in matched]
    explanation = f"Matched {len(matched)} of {len(groups)} core concept groups. "
    if missing:
        explanation += "Concepts that may need clarification: " + ", ".join(missing) + ". "
    if depth_matches:
        explanation += "Additional depth terms found: " + ", ".join(depth_matches) + "."
    else:
        explanation += "Add an example, technical detail, or limitation to demonstrate deeper understanding."
    return {
        "correctness_score": correctness, "knowledge_depth_score": depth,
        "completeness_score": completeness, "final_score": final, "status": status,
        "explanation": explanation, "confidence": "medium" if word_count >= 8 else "low",
        "unsupported_claims": [], "contradictions": [], "matched_concepts": matched,
        "scoring_mode": "rule_based",
    }
