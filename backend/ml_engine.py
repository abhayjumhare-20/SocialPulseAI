
import re
import joblib
from pathlib import Path
from collections import Counter

# Load the trained SocialPulse AI sentiment model
MODEL_PATH = Path(__file__).resolve().parent / "sentiment_model.joblib"

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "Trained sentiment model not found. "
        "Run: python train_model.py from the backend folder."
    )

MODEL = joblib.load(MODEL_PATH)
# Compatibility fix for LogisticRegression model loading
MODEL.named_steps["classifier"].multi_class = "auto"


def clean_text(text):
    text = re.sub(r"https?://\S+|www\.\S+", " ", str(text))
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def analyze_comments(texts):
    cleaned = [clean_text(t) for t in texts if clean_text(t)]

    if not cleaned:
        return []

    preds = MODEL.predict(cleaned)
    probs = MODEL.predict_proba(cleaned)

    return [
        {
            "text": t,
            "sentiment": str(p),
            "confidence": round(float(max(pr)), 3)
        }
        for t, p, pr in zip(cleaned, preds, probs)
    ]


def make_recommendations(comments):
    negatives = [
        c["text"].lower()
        for c in comments
        if c["sentiment"] == "negative"
    ]

    joined = " ".join(negatives)

    rules = [
        (
            ["delivery", "shipping", "late"],
            "Delivery delays",
            "Review fulfilment timelines, identify bottlenecks, and publish realistic delivery updates.",
            "Fewer delivery-related complaints",
            "high"
        ),
        (
            ["quality", "broken", "defect", "damage"],
            "Product quality",
            "Audit product quality, investigate recurring defects, and strengthen pre-dispatch checks.",
            "Improved product satisfaction",
            "high"
        ),
        (
            ["support", "response", "ignored", "service"],
            "Customer support",
            "Set response-time targets, triage unresolved tickets, and provide clear support channels.",
            "Faster issue resolution",
            "medium"
        ),
        (
            ["price", "expensive", "cost"],
            "Pricing concerns",
            "Review value communication and compare pricing with customer expectations and competitors.",
            "Clearer value perception",
            "medium"
        ),
        (
            ["crash", "bug", "error", "update"],
            "Technical reliability",
            "Reproduce reported issues, prioritize high-frequency bugs, and communicate fixes.",
            "More reliable user experience",
            "high"
        )
    ]

    found = []

    for words, title, action, outcome, priority in rules:
        if any(w in joined for w in words):
            found.append({
                "problem_title": title,
                "problem_description": "Repeated negative comments mention: "
                    + ", ".join(w for w in words if w in joined),
                "priority": priority,
                "suggested_action": action,
                "expected_outcome": outcome
            })

    if not found and negatives:
        found.append({
            "problem_title": "General negative feedback",
            "problem_description": "Negative feedback is present but does not match a specific issue category.",
            "priority": "medium",
            "suggested_action": "Review representative negative comments, group them by root cause, and respond transparently to users.",
            "expected_outcome": "Better understanding of audience concerns"
        })

    if not negatives:
        found.append({
            "problem_title": "Maintain positive engagement",
            "problem_description": "No negative comments were identified in this sample.",
            "priority": "low",
            "suggested_action": "Continue the practices receiving positive feedback and monitor future responses.",
            "expected_outcome": "Sustain audience trust"
        })

    return found


def keywords(comments, limit=8):
    words = []

    stop = {
        "this", "that", "with", "have", "your", "from", "they",
        "them", "very", "just", "about", "what", "when", "where",
        "will", "would", "could", "should", "there", "their",
        "then", "been", "were", "are", "the", "and", "for",
        "you", "not", "but", "was", "too", "its"
    }

    for c in comments:
        if c["sentiment"] == "negative":
            words += [
                w for w in re.findall(r"[a-z]{4,}", c["text"].lower())
                if w not in stop
            ]

    return [
        {"word": w, "count": n}
        for w, n in Counter(words).most_common(limit)
    ]
