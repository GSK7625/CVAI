"""Retrain the MLP using the existing E5 encoder, identical retrieval and R1 splits."""
import argparse
from pathlib import Path
import shutil
import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from pipeline import (CONTEXT_VERSION, FEATURE_VERSION, Reviewer, ClassifierHead, features_for_samples,
                      file_hash, load_splits, read_jsonl, save_classifier, target_labels, write_json)
from retrieved_context import model_inputs
from train_retrieval_mlp import report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("base-dir", "data-dir", "output-dir"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    base, out = args.base_dir, args.output_dir
    if out.exists():
        raise FileExistsError(out)
    splits, hashes = load_splits(args.data_dir)
    train, val = splits["train"], splits["validation"]
    reviewer = Reviewer(base, device=args.device, batch_size=32)
    if reviewer.manifest["feature_version"] != FEATURE_VERSION or reviewer.manifest["data_hashes"] != hashes:
        raise ValueError("Use the R1 retrieval artifact and the same data splits")
    x, records = features_for_samples(train, reviewer.encoder)
    train_x = model_inputs(train, x, records)
    y = target_labels(train)
    scaler = StandardScaler().fit(train_x)
    # Equalize the aggregate influence of five dense 384-D embedding blocks.
    # The three cosine scores and categorical evidence signals keep unit scaling.
    scaler.scale_[:x.shape[1] - 3] *= np.sqrt((x.shape[1] - 3) / 5)
    mlp = MLPClassifier(hidden_layer_sizes=(64,), alpha=0.1, max_iter=250, random_state=42)
    with threadpool_limits(limits=2):
        mlp.fit(scaler.transform(train_x), y, sample_weight=compute_sample_weight("balanced", y))
    vx, records = features_for_samples(val, reviewer.encoder)
    val_x = model_inputs(val, vx, records)
    predictions = mlp.predict(scaler.transform(val_x))
    provenance = {(r["sample_id"], r["requirement_id"]): r["evidence_spans"]
                  for r in read_jsonl(args.data_dir / "label_provenance.jsonl")}
    previous = report(val, provenance, records, reviewer.head.predict(vx))
    candidate = report(val, provenance, records, predictions)
    better = candidate["macro_f1"] > previous["macro_f1"] and candidate["score_mae"] <= previous["score_mae"]
    out.mkdir(parents=True)
    save_classifier(out / "classifier.npz", scaler, mlp)
    np.testing.assert_array_equal(ClassifierHead(out / "classifier.npz").predict(val_x), predictions)
    shutil.copytree(base / "encoder", out / "encoder")
    shutil.copy2(base / "THIRD_PARTY.md", out)
    sources = ("retrieved_context.py", "evidence_features.py", "jd_parser.py", "jd_parser_v2.py")
    manifest = dict(reviewer.manifest, feature_version=CONTEXT_VERSION, selected_classifier="context-mlp64",
                    classifier_sha256=file_hash(out / "classifier.npz"), feature_dimension=train_x.shape[1],
                    base_classifier_sha256=reviewer.manifest["classifier_sha256"],
                    feature_code_hashes={s: file_hash(Path(__file__).with_name(s)) for s in sources})
    write_json(out / "manifest.json", manifest)
    write_json(out / "comparison.json", dict(previous=previous, candidate=candidate, selected="candidate" if better else "previous",
               selection="higher validation macro-F1 and equal or lower validation score MAE"))
    print(f'Validation macro-F1 {previous["macro_f1"]:.4f} -> {candidate["macro_f1"]:.4f}', flush=True)


if __name__ == "__main__":
    main()
