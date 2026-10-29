"""Train only the supervised head; select C on validation, never on test."""
import argparse
import importlib.metadata
import shutil
import time
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score
from sklearn.neural_network import MLPClassifier
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from pipeline import (ClassifierHead, E5Encoder, FEATURE_VERSION, LABELS, MODEL_ID, features_for_samples,
                      file_hash, load_splits, metrics, save_classifier, target_labels, threshold_predict, write_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda"])
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists():
        raise FileExistsError("Thư mục output đã tồn tại. Chọn run name mới để giữ nguyên kết quả cũ.")
    splits, hashes = load_splits(args.data_dir)
    train, validation = splits["train"], splits["validation"]
    if args.smoke:
        train, validation = train[:40], validation[:20]
    if set(target_labels(train)) != set(LABELS):
        raise ValueError("Train phải có đủ ba nhãn")
    args.output_dir.mkdir(parents=True)
    started = time.perf_counter()
    encoder = E5Encoder(device=args.device, batch_size=32 if args.device == "cuda" else 8, threads=args.threads)
    print("E5 revision:", encoder.revision, flush=True)
    print("Đang encode train...", flush=True)
    x_train, _ = features_for_samples(train, encoder)
    print("Đang encode validation...", flush=True)
    x_val, val_records = features_for_samples(validation, encoder)
    y_train = target_labels(train)
    # A similarity-only baseline. Thresholds are selected on validation, never test.
    similarity = x_val[:, -3]
    cuts = np.unique(np.r_[-1.01, np.quantile(similarity, np.linspace(0, 1, 21)), 1.01])
    baseline_f1, baseline_thresholds = -1.0, None
    for low in cuts:
        for high in cuts[cuts >= low]:
            prediction = threshold_predict(similarity, low, high)
            f1 = f1_score(target_labels(validation), prediction, labels=list(LABELS), average="macro", zero_division=0)
            if f1 > baseline_f1:
                baseline_f1, baseline_thresholds = f1, [float(low), float(high)]
    baseline = metrics(validation, threshold_predict(similarity, *baseline_thresholds))
    candidates = [(f"logreg-C{c}", LogisticRegression(C=c, solver="lbfgs", max_iter=3000,
                    class_weight="balanced", random_state=42)) for c in (0.1, 1.0, 10.0)]
    candidates += [(f"mlp64-alpha{alpha}", MLPClassifier(hidden_layer_sizes=(64,), alpha=alpha,
                    max_iter=250, early_stopping=False, random_state=42)) for alpha in (0.01, 0.1)]
    results, best, best_name, best_f1 = [], None, None, -1.0
    for name, classifier in candidates:
        model = make_pipeline(StandardScaler(), classifier)
        fit_args = {"mlpclassifier__sample_weight": compute_sample_weight("balanced", y_train)} if isinstance(classifier, MLPClassifier) else {}
        with threadpool_limits(limits=args.threads):
            model.fit(x_train, y_train, **fit_args)
        result = {"classifier": name, **metrics(validation, model.predict(x_val))}
        results.append(result)
        print(f"{name}: validation macro-F1={result['macro_f1']:.4f}; MAE={result['score_mae']:.2f}", flush=True)
        if result["macro_f1"] > best_f1:
            best, best_name, best_f1 = model, name, result["macro_f1"]
    scaler, classifier = best.steps[0][1], best.steps[1][1]
    save_classifier(args.output_dir / "classifier.npz", scaler, classifier)
    np.testing.assert_array_equal(ClassifierHead(args.output_dir / "classifier.npz").predict(x_val), best.predict(x_val))
    # This diagnostic uses gold only AFTER retrieval. It is not an input feature.
    supports = { (s["sample_id"], a["id"]): a["evidence"] for s in validation for a in s["target"]["assessments"] if a["evidence"] }
    hits = sum(any(evidence in c["text"] for c in r["retrieved"])
               for r in val_records if (evidence := supports.get((r["sample_id"], r["requirement_id"]))))
    write_json(args.output_dir / "validation_metrics.json", {
        "candidates": results, "selected_classifier": best_name,
        "retrieval_gold_excerpt_recall_at_3": hits / len(supports) if supports else None,
        "retrieval_support": len(supports), "human_reviewed": False,
        "cosine_baseline": {"thresholds": baseline_thresholds, **baseline},
    })
    # Deployment includes the pinned encoder, not a link to a Colab cache.
    encoder.model.save_pretrained(args.output_dir / "encoder", safe_serialization=True)
    encoder.tokenizer.save_pretrained(args.output_dir / "encoder")
    license_path = encoder.path / "README.md"
    if license_path.exists():
        shutil.copy2(license_path, args.output_dir / "encoder" / "UPSTREAM_MODEL_CARD.md")
    for license_path in encoder.path.glob("LICENSE*"):
        shutil.copy2(license_path, args.output_dir / "encoder" / license_path.name)
    shutil.copy2(Path(__file__).with_name("THIRD_PARTY.md"), args.output_dir / "THIRD_PARTY.md")
    manifest = {
        "feature_version": FEATURE_VERSION, "mode": "smoke" if args.smoke else "full", "encoder": MODEL_ID,
        "encoder_revision": encoder.revision, "encoder_frozen": True,
        "training_method": "Frozen E5; scaler(train only); logreg/MLP64 selected on validation macro-F1",
        "selected_classifier": best_name, "data_hashes": hashes, "labels": list(LABELS),
        "n_train_requirements": len(y_train), "n_validation_requirements": len(x_val),
        "feature_dimension": x_train.shape[1], "classifier_sha256": file_hash(args.output_dir / "classifier.npz"),
        "encoder_file_hashes": {p.name: file_hash(p) for p in (args.output_dir / "encoder").iterdir() if p.is_file()},
        "baseline_thresholds": baseline_thresholds,
        "versions": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "scikit-learn", "numpy")},
        "elapsed_seconds": time.perf_counter() - started,
        "limitations": "Controlled synthetic data; not validated on real CVs. Retrieved excerpts are not verified semantic evidence.",
    }
    write_json(args.output_dir / "manifest.json", manifest)
    print("SMOKE XONG — chưa đánh giá test" if args.smoke else "FULL XONG — classifier và encoder đã lưu", flush=True)
    print(args.output_dir.resolve(), flush=True)


if __name__ == "__main__":
    main()
