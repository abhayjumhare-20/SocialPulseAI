from pathlib import Path
import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "datasets"

TRAIN_FILE = DATA_DIR / "train.parquet"
TEST_FILE = DATA_DIR / "test.parquet"
MODEL_FILE = BASE_DIR / "sentiment_model.joblib"

LABEL_MAP = {
    0: "negative",
    1: "neutral",
    2: "positive"
}

print("Loading datasets...")

train_df = pd.read_parquet(TRAIN_FILE)
test_df = pd.read_parquet(TEST_FILE)

for name, df in [("Training", train_df), ("Testing", test_df)]:
    if not {"text", "label"}.issubset(df.columns):
        raise ValueError(f"{name} dataset must contain text and label columns.")

    if df["text"].isna().any():
        raise ValueError(f"{name} dataset contains missing text.")

    if not set(df["label"].unique()).issubset(LABEL_MAP):
        raise ValueError(f"{name} dataset contains unknown labels.")

X_train = train_df["text"].astype(str)
y_train = train_df["label"].map(LABEL_MAP)

X_test = test_df["text"].astype(str)
y_test = test_df["label"].map(LABEL_MAP)

print(f"Training examples: {len(X_train)}")
print(f"Testing examples: {len(X_test)}")
print("\nTraining sentiment model...")

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=50000,
        min_df=2,
        sublinear_tf=True,
        strip_accents="unicode"
    )),
    ("classifier", LogisticRegression(
        max_iter=1500,
        class_weight="balanced",
        solver="lbfgs"
    ))
])

model.fit(X_train, y_train)

print("\nEvaluating model on separate test dataset...")

predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\n===================================")
print("SOCIALPULSE AI MODEL EVALUATION")
print("===================================")
print(f"Test Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    labels=["negative", "neutral", "positive"],
    target_names=["Negative", "Neutral", "Positive"],
    digits=3,
    zero_division=0
))

print("Confusion Matrix:")
print(confusion_matrix(
    y_test,
    predictions,
    labels=["negative", "neutral", "positive"]
))

print("\nSaving trained model...")

joblib.dump(model, MODEL_FILE, compress=3)

print(f"\nModel saved successfully: {MODEL_FILE}")
print("Training and evaluation completed!")
