"""Bounded CPU ablation: frozen E5 + the same MLP, adding round1 development data."""
import argparse
import importlib.metadata
import json
import shutil
import time
from pathlib import Path

import numpy as np
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from pipeline import (FEATURE_VERSION, ClassifierHead, Reviewer, features_for_samples,
                      file_hash, load_splits, metrics, read_jsonl, save_classifier,
                      target_labels, write_json)


def validation_result(groups, predict):
    result = {name: metrics(samples, predict(features)) for name, (samples, features) in groups.items()}
    result["selection_score"] = (result["old_validation"]["macro_f1"] + result["new_validation"]["macro_f1"]) / 2
    return result


def choose(results, baseline_old_f1):
    eligible = [r for r in results if r["old_validation"]["macro_f1"] >= baseline_old_f1 - .02]
    return max(eligible, key=lambda r: (r["selection_score"], -r["old_validation"]["score_mae"]))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, required=True)
    p.add_argument("--old-data", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--threads", type=int, default=2)
    a = p.parse_args()
    if a.output.exists(): raise FileExistsError("Refusing to overwrite experiment")
    old, old_hashes = load_splits(a.old_data)
    augmented, augmented_hashes = load_splits(a.data_dir)
    if old_hashes["test"] != augmented_hashes["test"]: raise ValueError("Old test changed")
    if len(augmented["train"]) != len(old["train"]) + 144: raise ValueError("Unexpected training set")
    a.output.mkdir(parents=True)
    start = time.perf_counter()
    protocol = {"feature_version": FEATURE_VERSION, "encoder_frozen": True, "seed": 42,
                "selection": "mean of old/new validation macro-F1; old validation regression at most 0.02 vs released baseline",
                "candidates": ["released-v1", "old-only-mlp64-a0.01", "augmented-mlp64-a0.01", "augmented-mlp64-a0.1", "augmented-mlp64-a1.0"],
                "validation_locked_before_test": True, "holdout_used": False,
                "data_hashes": augmented_hashes, "baseline_classifier_sha256": file_hash(a.baseline / "classifier.npz"),
                "pipeline_sha256": file_hash(Path(__file__).with_name("pipeline.py")),
                "train_script_sha256": file_hash(Path(__file__)),
                "not_a_pair_v2_experiment": True}
    write_json(a.output / "protocol.json", protocol)
    baseline = Reviewer(a.baseline, device="cpu", threads=a.threads)
    if baseline.manifest["feature_version"] != FEATURE_VERSION: raise ValueError("Expected v1 MLP baseline")
    if baseline.manifest["classifier_sha256"] != "268e14e927fcd94d6ffa89f9cc0524691e5d18567d7f995355eb8aa1be0e5105":
        raise ValueError("Use the released Colab classifier as baseline")
    features_dir = a.output / "features"
    features_dir.mkdir()

    def encode(name, samples):
        print(f"Encoding {name}: {len(samples)} CV-JD pairs", flush=True)
        features, records = features_for_samples(samples, baseline.encoder)
        np.savez_compressed(features_dir / (name + ".npz"), x=features, y=target_labels(samples))
        return features, records

    # Exactly the v1 features. Neither provenance nor human/rule labels enter encode().
    x_old, _ = encode("old_train", old["train"])
    added = read_jsonl(a.data_dir / "new_train.jsonl")
    x_new, _ = encode("new_train", added)
    x_aug = np.concatenate([x_old, x_new])
    y_old, y_aug = target_labels(old["train"]), target_labels(augmented["train"])
    new_val = read_jsonl(a.data_dir / "new_validation.jsonl")
    x_val_old, _ = encode("old_validation", old["validation"])
    x_val_new, _ = encode("new_validation", new_val)
    groups = {"old_validation": (old["validation"], x_val_old), "new_validation": (new_val, x_val_new)}
    results = [{"name": "released-v1", **validation_result(groups, baseline.head.predict)}]
    models = {}
    candidates = [("old-only-mlp64-a0.01", x_old, y_old, .01)]
    candidates += [(f"augmented-mlp64-a{alpha}", x_aug, y_aug, alpha) for alpha in (.01, .1, 1.0)]
    for name, x, y, alpha in candidates:
        model = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(64,), alpha=alpha,
                              max_iter=250, early_stopping=False, random_state=42))
        with threadpool_limits(limits=a.threads):
            model.fit(x, y, mlpclassifier__sample_weight=compute_sample_weight("balanced", y))
            result = {"name": name, **validation_result(groups, model.predict)}
        models[name] = model
        candidate_path = a.output / name
        candidate_path.mkdir()
        save_classifier(candidate_path / "classifier.npz", model.steps[0][1], model.steps[1][1])
        np.testing.assert_array_equal(ClassifierHead(candidate_path / "classifier.npz").predict(x_val_new), model.predict(x_val_new))
        results.append(result)
        write_json(a.output / "validation_candidates.json", results)
        print(f"{name}: old/new F1 {result['old_validation']['macro_f1']:.4f}/{result['new_validation']['macro_f1']:.4f}; mean {result['selection_score']:.4f}", flush=True)
    chosen = choose(results, results[0]["old_validation"]["macro_f1"])
    write_json(a.output / "selection_locked.json", {"selected": chosen["name"], "selection_result": chosen,
               "protocol_sha256": file_hash(a.output / "protocol.json"), "test_features_not_yet_computed": True})
    print("Selection locked:", chosen["name"], flush=True)
    # Historical test is evaluated after the decision; do not retune from the result.
    x_test, records = encode("old_test", old["test"])
    with threadpool_limits(limits=a.threads):
        base_pred = baseline.head.predict(x_test)
        selected_pred = base_pred if chosen["name"] == "released-v1" else models[chosen["name"]].predict(x_test)
        base_train_pred = baseline.head.predict(x_aug)
        train_pred = base_train_pred if chosen["name"] == "released-v1" else models[chosen["name"]].predict(x_aug)
    write_json(a.output / "historical_test_comparison.json", {"baseline": metrics(old["test"], base_pred),
               "selected": metrics(old["test"], selected_pred), "selected_name": chosen["name"],
               "test_sha256": old_hashes["test"], "old_test_previously_observed": True,
               "external_real_world_validation": False, "new_holdout_evaluated": False})
    offset = 0
    with (a.output / "historical_test_predictions.jsonl").open("w", encoding="utf-8") as stream:
        for sample in old["test"]:
            n = len(sample["requirements"])
            stream.write(json.dumps({"sample_id": sample["sample_id"], "baseline": base_pred[offset:offset+n].tolist(),
                                    "selected": selected_pred[offset:offset+n].tolist(),
                                    "requirement_ids": [r["id"] for r in sample["requirements"]]}, ensure_ascii=False) + "\n")
            offset += n
    artifact = a.output / "selected_artifact"
    artifact.mkdir()
    source = a.baseline if chosen["name"] == "released-v1" else a.output / chosen["name"]
    shutil.copy2(source / "classifier.npz", artifact / "classifier.npz")
    shutil.copytree(a.baseline / "encoder", artifact / "encoder")
    shutil.copy2(a.baseline / "THIRD_PARTY.md", artifact / "THIRD_PARTY.md")
    trained_on_augmented = chosen["name"].startswith("augmented-")
    actual_hashes = augmented_hashes if trained_on_augmented else old_hashes
    manifest = dict(baseline.manifest)
    manifest.update(classifier_sha256=file_hash(artifact / "classifier.npz"), selected_classifier=chosen["name"],
                    data_hashes=actual_hashes, n_train_requirements=len(y_aug) if trained_on_augmented else len(y_old),
                    n_validation_requirements=sum(len(x) for _, x in groups.values()),
                    training_method="Frozen released E5 + same MLP; candidate selected on development validation only" if chosen["name"] != "released-v1" else baseline.manifest["training_method"],
                    experiment="augmentation-r1", training_data_sha256=actual_hashes["train"],
                    selection_dataset_hashes=augmented_hashes, trained_on_augmented=trained_on_augmented,
                    versions={n: importlib.metadata.version(n) for n in ("torch", "transformers", "scikit-learn", "numpy")},
                    elapsed_seconds=time.perf_counter()-start,
                    human_reviewed_all=False, dataset_manifest_sha256=file_hash(a.data_dir / "manifest.json"),
                    limitations="Partially human-audited synthetic expansion; unresolved labels excluded. Historical test previously observed; new holdout untouched.")
    write_json(artifact / "manifest.json", manifest)
    write_json(a.output / "training_metrics.json", {"selected_on_training": metrics(augmented["train"], train_pred),
                                                   "released_on_training": metrics(augmented["train"], base_train_pred)})
    print("Completed:", a.output.resolve(), flush=True)


if __name__ == "__main__": main()
