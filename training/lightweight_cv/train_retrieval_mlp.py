"""Compare frozen E5 and contrastively tuned E5 using identical MLP heads."""
import argparse
import json
import random
import shutil
from pathlib import Path

import numpy as np
import torch
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight
from threadpoolctl import threadpool_limits

from jd_parser import detect_skills
from pipeline import (ClassifierHead, E5Encoder, FEATURE_VERSION, LABELS, MODEL_ID, chunk_cv,
                      features_for_samples, file_hash, load_splits, metrics, read_jsonl,
                      save_classifier, target_labels, write_json)

REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
ROOT = Path(__file__).resolve().parent


def gold_lines(row, provenance):
    by_id = {}
    for a in row["target"]["assessments"]:
        spans = provenance.get((row["sample_id"], a["id"]), [a["evidence"]] if a["evidence"] else [])
        if any(not s or s not in row["cv_text"] for s in spans):
            raise ValueError(f'Invalid evidence in {row["sample_id"]} {a["id"]}')
        lines = list(dict.fromkeys(line.strip() for s in spans for line in s.splitlines() if line.strip()))
        if bool(lines) != (a["status"] != "not_evidenced"):
            raise ValueError("Evidence and label disagree")
        by_id[a["id"]] = lines
    return by_id


def make_triplets(rows, provenance, encoder, retrieval):
    """Prefer nearby annotated passages for another skill in the same CV as negatives."""
    ranked = {(r["sample_id"], r["requirement_id"]): [x["text"] for x in r["retrieved"]] for r in retrieval}
    triples = set()
    for row in rows:
        chunks = [c["text"] for c in chunk_cv(row["cv_text"], encoder.tokenizer)]
        evidence = gold_lines(row, provenance)
        for req in row["requirements"]:
            query, rid = req["text"], req["id"]
            positives = [c for c in chunks if any(s in c for s in evidence[rid])]
            if any(not any(s in c for c in positives) for s in evidence[rid]):
                raise ValueError("Positive span does not align with a retrieval chunk")
            target_skills = {s for _, _, s in detect_skills(query)}
            other = {s for key, lines in evidence.items() if key != rid for s in lines}
            candidates = ranked[row["sample_id"], rid] + chunks
            negatives = [c for c in candidates if c not in positives and any(s in c for s in other)
                         and (skills := {s for _, _, s in detect_skills(c)}) and skills.isdisjoint(target_skills)]
            if negatives:
                triples.update((query, p, negatives[0]) for p in positives)
    if not triples:
        raise ValueError("No train triplets")
    return sorted(triples)


def tune(encoder, triples):
    for block in encoder.model.encoder.layer[-2:]:
        block.requires_grad_(True)
    params = [p for p in encoder.model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=1e-5)
    examples = triples.copy()
    random.Random(42).shuffle(examples)
    encoder.model.train()
    for start in range(0, len(examples), 16):
        q, p, n = zip(*examples[start:start + 16])
        queries = encoder.embed_batch(["query: " + s for s in q])
        docs = encoder.embed_batch(["passage: " + s for s in (*p, *n)])
        pos, neg = docs.chunk(2)
        logits = torch.stack([(queries * v).sum(-1) for v in (pos, neg)], dim=1) / 0.05
        loss = torch.nn.functional.cross_entropy(logits, torch.zeros(len(q), dtype=torch.long, device=encoder.device))
        if not torch.isfinite(loss):
            raise ValueError("Non-finite retrieval loss")
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        optimizer.step()
    encoder.model.requires_grad_(False).eval()


def report(rows, provenance, records, predicted):
    result = metrics(rows, predicted)
    gold = {(r["sample_id"], k): spans for r in rows for k, spans in gold_lines(r, provenance).items()}
    found = total = full = supported = 0
    for r in records:
        spans = gold[r["sample_id"], r["requirement_id"]]
        if spans:
            count = sum(any(s in c["text"] for c in r["retrieved"]) for s in spans)
            found += count
            total += len(spans)
            full += count == len(spans)
            supported += 1
    result.update(span_recall_at_3=found / total if total else None, gold_spans=total,
                  complete_evidence_at_3=full / supported if supported else None, supported_requirements=supported)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--pdf-dir", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    args = ap.parse_args()
    out = args.output_dir
    splits, hashes = load_splits(args.data_dir)
    train, val = splits["train"], splits["validation"]
    source = args.data_dir / "label_provenance.jsonl"
    provenance = {(r["sample_id"], r["requirement_id"]): r["evidence_spans"] for r in read_jsonl(source)}
    torch.manual_seed(42)
    encoder = E5Encoder(revision=REVISION, device=args.device, batch_size=32)
    out.mkdir(parents=True, exist_ok=False)
    y = target_labels(train)
    results = {}
    triples = []
    for name in ("frozen", "tuned"):
        print(f"Training {name} E5 + MLP", flush=True)
        if name == "tuned":
            tune(encoder, triples)
        x, records = features_for_samples(train, encoder)
        if name == "frozen":
            triples = make_triplets(train, provenance, encoder, records)
            with (out / "retrieval_train.jsonl").open("w", encoding="utf8") as f:
                for q, p, n in triples:
                    print(json.dumps(dict(query=q, positive=p, negative=n), ensure_ascii=False), file=f)
        scaler = StandardScaler().fit(x)
        mlp = MLPClassifier(hidden_layer_sizes=(64,), alpha=0.1, max_iter=250, random_state=42)
        with threadpool_limits(limits=2):
            mlp.fit(scaler.transform(x), y, sample_weight=compute_sample_weight("balanced", y))
        vx, records = features_for_samples(val, encoder)
        labels = mlp.predict(scaler.transform(vx))
        results[name] = report(val, provenance, records, labels)
        dest = out / name
        dest.mkdir()
        save_classifier(dest / "classifier.npz", scaler, mlp)
        np.testing.assert_array_equal(ClassifierHead(dest / "classifier.npz").predict(vx), labels)
        enc_dir = dest / "encoder"
        encoder.model.save_pretrained(enc_dir, safe_serialization=True)
        encoder.tokenizer.save_pretrained(enc_dir)
        for path in [encoder.path / "README.md", *encoder.path.glob("LICENSE*")]:
            if path.is_file():
                shutil.copy2(path, enc_dir / ("UPSTREAM_MODEL_CARD.md" if path.name == "README.md" else path.name))
        shutil.copy2(ROOT / "THIRD_PARTY.md", dest)
        write_json(dest / "manifest.json", dict(feature_version=FEATURE_VERSION, mode="full", labels=list(LABELS),
                   encoder=MODEL_ID, encoder_revision=REVISION, encoder_frozen=name == "frozen",
                   selected_classifier="mlp64", data_hashes=hashes, provenance_sha256=file_hash(source),
                   classifier_sha256=file_hash(dest / "classifier.npz"), feature_dimension=x.shape[1],
                   encoder_file_hashes={p.name: file_hash(p) for p in enc_dir.iterdir() if p.is_file()}))
        write_json(dest / "validation.json", results[name])
        print(name, results[name]["macro_f1"], results[name]["span_recall_at_3"], flush=True)
    selected = max(results, key=lambda k: results[k]["macro_f1"])
    write_json(out / "comparison.json", dict(validation=results, selected=selected, train_triplets=len(triples),
               selection="highest validation macro-F1; frozen on tie", seed=42))
    from evaluate_jake import evaluate
    evaluate(out / selected, args.pdf_dir, out / "pdf_evaluation.json", args.device)


if __name__ == "__main__":
    main()
