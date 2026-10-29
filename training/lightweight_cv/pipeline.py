"""Frozen multilingual E5 retrieval, a small supervised head, deterministic scoring.

No target, provenance, weight or sample/group ID enters the learned features.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

import numpy as np

MODEL_ID = "intfloat/multilingual-e5-small"
LABELS = ("met", "partial", "not_evidenced")
VALUES = {"met": 1.0, "partial": 0.5, "not_evidenced": 0.0}
FEATURE_VERSION = "e5-top3-classifier-v1"
TOP_K = 3
CHUNK_TOKENS = 192
MAX_CV_CHARS = 30_000


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_input(sample):
    cv = sample.get("cv_text")
    requirements = sample.get("requirements")
    if not isinstance(cv, str) or not cv.strip() or len(cv) > MAX_CV_CHARS:
        raise ValueError(f"cv_text phải có nội dung và không quá {MAX_CV_CHARS} ký tự")
    if not isinstance(requirements, list) or not 1 <= len(requirements) <= 20:
        raise ValueError("Cần 1–20 yêu cầu JD")
    ids = []
    for req in requirements:
        if not isinstance(req, dict):
            raise ValueError("Mỗi yêu cầu phải là object")
        if not isinstance(req.get("id"), str) or not 1 <= len(req["id"]) <= 40:
            raise ValueError("ID yêu cầu không hợp lệ")
        if not isinstance(req.get("text"), str) or not req["text"].strip() or len(req["text"]) > 500:
            raise ValueError("Nội dung yêu cầu phải dài 1–500 ký tự")
        if type(req.get("weight")) is not int or not 1 <= req["weight"] <= 5:
            raise ValueError("Weight phải là số nguyên 1–5")
        ids.append(req["id"])
    if len(set(ids)) != len(ids):
        raise ValueError("Trùng ID yêu cầu")


def load_splits(data_dir):
    """Fail on leakage before flattening requirements into training examples."""
    data_dir = Path(data_dir)
    splits = {name: read_jsonl(data_dir / f"{name}.jsonl") for name in ("train", "validation", "test")}
    seen = {key: set() for key in ("sample_id", "cv_group", "jd_group", "cv_content", "jd_content")}
    for name, rows in splits.items():
        if not rows:
            raise ValueError(f"Split rỗng: {name}")
        current = {key: set() for key in seen}
        for row in rows:
            validate_input(row)
            for key in ("sample_id", "cv_group", "jd_group"):
                if not isinstance(row.get(key), str) or not row[key]:
                    raise ValueError(f"Thiếu {key}")
                if key == "sample_id" and row[key] in current[key]:
                    raise ValueError("Trùng sample_id")
                current[key].add(row[key])
            current["cv_content"].add(" ".join(row["cv_text"].lower().split()))
            current["jd_content"].add(json.dumps(sorted(
                (" ".join(r["text"].lower().split()), r["weight"]) for r in row["requirements"])))
            gold = row["target"]["assessments"]
            expected = {r["id"] for r in row["requirements"]}
            if len(gold) != len(expected) or {a["id"] for a in gold} != expected:
                raise ValueError("Target phải có đúng một nhãn cho từng ID")
            for assessment in gold:
                status, evidence = assessment["status"], assessment["evidence"]
                if status not in LABELS:
                    raise ValueError("Nhãn không hợp lệ")
                if status == "not_evidenced":
                    if evidence is not None:
                        raise ValueError("not_evidenced phải có evidence=null")
                elif not isinstance(evidence, str) or not evidence.strip() or evidence not in row["cv_text"]:
                    raise ValueError("Gold evidence không có trong CV")
        for key in seen:
            if current[key] & seen[key]:
                raise ValueError(f"Leakage {key} ở split {name}")
            seen[key].update(current[key])
    hashes = {name: file_hash(data_dir / f"{name}.jsonl") for name in splits}
    return splits, hashes


def chunk_cv(text, tokenizer):
    """Keep original spans including negation; never silently truncate a full CV."""
    chunks = []
    for match in re.finditer(r"[^\r\n]+", text):
        line = match.group()
        if not line.strip():
            continue
        offsets = tokenizer(line, add_special_tokens=False, return_offsets_mapping=True)["offset_mapping"]
        for start in range(0, len(offsets), CHUNK_TOKENS - 32):
            stop = min(start + CHUNK_TOKENS, len(offsets))
            begin_char, end_char = offsets[start][0], offsets[stop - 1][1]
            excerpt = line[begin_char:end_char]
            if excerpt.strip():
                chunks.append({"text": excerpt, "start": match.start() + begin_char,
                               "end": match.start() + end_char})
            if stop == len(offsets):
                break
    if not chunks or len(chunks) > 256:
        raise ValueError("CV cần có nội dung, tối đa 256 đoạn; hãy kiểm tra text đã trích xuất")
    return chunks


class E5Encoder:
    def __init__(self, model_path=None, revision="main", device="cpu", batch_size=8, threads=2):
        import torch
        from huggingface_hub import snapshot_download
        from transformers import AutoModel, AutoTokenizer

        torch.set_num_threads(threads)
        path = Path(model_path) if model_path else Path(snapshot_download(
            MODEL_ID, revision=revision,
            allow_patterns=["config.json", "tokenizer*.json", "special_tokens_map.json", "model.safetensors",
                            "sentencepiece.bpe.model", "README.md", "LICENSE*"],
        ))
        self.path, self.revision = path, path.name if not model_path else revision
        self.tokenizer = AutoTokenizer.from_pretrained(path, use_fast=True, local_files_only=True)
        if not self.tokenizer.is_fast:
            raise ValueError("Cần fast tokenizer để giữ nguyên vị trí đoạn CV")
        self.model = AutoModel.from_pretrained(path, local_files_only=True).to(device).eval()
        self.model.requires_grad_(False)
        self.device, self.batch_size = device, batch_size

    def encode(self, texts):
        import torch

        vectors = []
        with torch.inference_mode():
            for start in range(0, len(texts), self.batch_size):
                batch = self.tokenizer(texts[start:start + self.batch_size], padding=True,
                                       truncation=False, return_tensors="pt")
                if batch["input_ids"].shape[1] > 512:
                    raise ValueError("Đầu vào E5 vượt 512 tokens; không tự cắt mất nội dung")
                batch = {key: value.to(self.device) for key, value in batch.items()}
                hidden = self.model(**batch).last_hidden_state
                mask = batch["attention_mask"].unsqueeze(-1)
                pooled = (hidden * mask).sum(1) / mask.sum(1)
                normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
                vectors.append(normalized.cpu().numpy().astype(np.float32))
        return np.concatenate(vectors)


def features_for_samples(samples, encoder):
    """Inference path shared by training, validation, test, CLI and API."""
    prepared, texts = [], {}
    for sample in samples:
        validate_input(sample)
        chunks = chunk_cv(sample["cv_text"], encoder.tokenizer)
        prepared.append(chunks)
        for chunk in chunks:
            texts.setdefault("passage: " + chunk["text"], len(texts))
        for req in sample["requirements"]:
            texts.setdefault("query: " + req["text"], len(texts))
    encoded = encoder.encode(list(texts))
    features, records = [], []
    for sample, chunks in zip(samples, prepared):
        documents = encoded[[texts["passage: " + c["text"]] for c in chunks]]
        for req in sample["requirements"]:
            query = encoded[texts["query: " + req["text"]]]
            similarities = documents @ query
            order = np.argsort(-similarities, kind="stable")[:TOP_K]
            best = documents[order[0]]
            mean = documents[order].mean(axis=0)
            sims = np.zeros(TOP_K, dtype=np.float32)
            sims[:len(order)] = similarities[order]
            features.append(np.concatenate([query, best, mean, np.abs(query - best), query * best, sims]))
            records.append({"sample_id": sample.get("sample_id", "new-cv"), "requirement_id": req["id"],
                            "retrieved": [{**chunks[i], "similarity": float(similarities[i])} for i in order]})
    return np.asarray(features, dtype=np.float32), records


def target_labels(samples):
    return np.array([next(a["status"] for a in s["target"]["assessments"] if a["id"] == r["id"])
                     for s in samples for r in s["requirements"]])


def threshold_predict(similarities, low, high):
    return np.where(similarities < low, "not_evidenced", np.where(similarities < high, "partial", "met"))


def weighted_score(requirements, statuses):
    ids = [r["id"] for r in requirements]
    if not ids or len(set(ids)) != len(ids) or set(ids) != set(statuses):
        raise ValueError("Trạng thái phải khớp đúng các ID yêu cầu")
    if any(status not in VALUES for status in statuses.values()):
        raise ValueError("Trạng thái không hợp lệ")
    if any(type(r["weight"]) is not int or not 1 <= r["weight"] <= 5 for r in requirements):
        raise ValueError("Weight phải là số nguyên 1–5")
    return 100 * sum(r["weight"] * VALUES[statuses[r["id"]]] for r in requirements) / sum(r["weight"] for r in requirements)


def render_review(sample, statuses, records):
    """Templates never invent skill-specific facts from an unverified retrieval."""
    score = weighted_score(sample["requirements"], statuses)
    counts = Counter(statuses.values())
    by_id = {record["requirement_id"]: record for record in records}
    if set(by_id) != set(statuses) or len(records) != len(statuses):
        raise ValueError("Thiếu hoặc trùng kết quả truy xuất")
    wording = {
        "met": "Bộ phân loại dự đoán đáp ứng yêu cầu; hãy đối chiếu đoạn CV được truy xuất.",
        "partial": "Bộ phân loại dự đoán đáp ứng một phần; hãy kiểm tra bối cảnh và mức kinh nghiệm trong đoạn CV.",
        "not_evidenced": "Bộ phân loại chưa xác định được bằng chứng đáp ứng yêu cầu trong CV.",
    }
    assessments = []
    for req in sample["requirements"]:
        status = statuses[req["id"]]
        contexts = by_id[req["id"]]["retrieved"]
        for context in contexts:
            if sample["cv_text"][context["start"]:context["end"]] != context["text"]:
                raise ValueError("Đoạn truy xuất không khớp vị trí trong CV")
        assessments.append({"id": req["id"], "requirement_text": req["text"], "status": status, "weight": req["weight"],
                            "contribution_points": round(100 * req["weight"] * VALUES[status] / sum(r["weight"] for r in sample["requirements"]), 4),
                            "comment": wording[status], "retrieved_context": contexts})
    return {"schema": FEATURE_VERSION, "sample_id": sample.get("sample_id", "new-cv"),
            "score": round(score, 4), "assessments": assessments,
            "summary": f"Dự đoán: {counts['met']}/{len(statuses)} yêu cầu đáp ứng; {counts['partial']} đáp ứng một phần; {counts['not_evidenced']} chưa có bằng chứng đáp ứng.",
            "suggestions": (["Với các yêu cầu chưa đáp ứng đầy đủ, bổ sung bối cảnh sử dụng, vai trò và thời gian nếu đúng thực tế."]
                            if counts["partial"] + counts["not_evidenced"] else []),
            "notice": "Điểm theo rubric từ dự đoán máy. Đoạn tương đồng là ngữ cảnh để kiểm tra, không phải bằng chứng đã được xác minh."}


def metrics(samples, predicted):
    from sklearn.metrics import classification_report, confusion_matrix

    gold = target_labels(samples)
    if len(gold) != len(predicted):
        raise ValueError("Sai số lượng dự đoán")
    report = classification_report(gold, predicted, labels=list(LABELS), output_dict=True, zero_division=0)
    errors, offset = [], 0
    for sample in samples:
        reqs = sample["requirements"]
        pred = dict(zip([r["id"] for r in reqs], predicted[offset:offset + len(reqs)]))
        target = {a["id"]: a["status"] for a in sample["target"]["assessments"]}
        errors.append(abs(weighted_score(reqs, pred) - weighted_score(reqs, target)))
        offset += len(reqs)
    return {"n_samples": len(samples), "n_requirements": len(gold), "macro_f1": report["macro avg"]["f1-score"],
            "accuracy": float(np.mean(gold == predicted)), "score_mae": float(np.mean(errors)),
            "classification_report": report,
            "confusion_labels": list(LABELS), "confusion_matrix": confusion_matrix(gold, predicted, labels=list(LABELS)).tolist()}


def save_classifier(path, scaler, classifier):
    is_linear = hasattr(classifier, "coef_")
    coefs = [classifier.coef_.T] if is_linear else classifier.coefs_
    intercepts = [classifier.intercept_] if is_linear else classifier.intercepts_
    arrays = {"mean": scaler.mean_, "scale": scaler.scale_, "classes": classifier.classes_,
              "layers": np.array(len(coefs)), "activation": np.array("identity" if is_linear else "relu")}
    for i, (weight, bias) in enumerate(zip(coefs, intercepts)):
        arrays[f"w{i}"], arrays[f"b{i}"] = weight, bias
    np.savez_compressed(path, **arrays)


class ClassifierHead:
    """Only numeric arrays and string labels, no executable pickle/joblib artifact."""
    def __init__(self, path):
        with np.load(path, allow_pickle=False) as data:
            self.mean, self.scale = data["mean"], data["scale"]
            self.classes, self.activation = data["classes"], str(data["activation"])
            count = int(data["layers"])
            if count not in (1, 2) or self.activation not in ("relu", "identity"):
                raise ValueError("Kiến trúc classifier không hợp lệ")
            self.layers = [(data[f"w{i}"], data[f"b{i}"]) for i in range(count)]
        if (set(self.classes) != set(LABELS) or self.mean.ndim != 1 or self.scale.shape != self.mean.shape or np.any(self.scale <= 0)):
            raise ValueError("Classifier artifact không hợp lệ")
        size = len(self.mean)
        for weight, bias in self.layers:
            if weight.ndim != 2 or weight.shape[0] != size or bias.shape != (weight.shape[1],):
                raise ValueError("Sai kích thước layer")
            size = weight.shape[1]
        if size != 3:
            raise ValueError("Classifier phải có ba đầu ra")
        if not all(np.all(np.isfinite(a)) for a in [self.mean, self.scale] + [a for layer in self.layers for a in layer]):
            raise ValueError("Classifier chứa giá trị không hữu hạn")

    def predict(self, features):
        logits = features.copy()
        logits -= self.mean
        logits /= self.scale
        for i, (weight, bias) in enumerate(self.layers):
            logits = logits @ weight + bias
            if i < len(self.layers) - 1 and self.activation == "relu":
                logits = np.maximum(logits, 0)
        return self.classes[np.argmax(logits, axis=1)]


class Reviewer:
    def __init__(self, artifact_dir, device="cpu", batch_size=8, threads=2):
        directory = Path(artifact_dir)
        self.manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if self.manifest["feature_version"] != FEATURE_VERSION or self.manifest["mode"] != "full":
            raise ValueError("Chỉ dùng artifact full đúng phiên bản pipeline")
        if file_hash(directory / "classifier.npz") != self.manifest["classifier_sha256"]:
            raise ValueError("Classifier không khớp manifest")
        for name, digest in self.manifest["encoder_file_hashes"].items():
            if Path(name).name != name or file_hash(directory / "encoder" / name) != digest:
                raise ValueError("Encoder không khớp manifest")
        self.head = ClassifierHead(directory / "classifier.npz")
        self.encoder = E5Encoder(directory / "encoder", revision=self.manifest["encoder_revision"],
                                 device=device, batch_size=batch_size, threads=threads)

    def review(self, sample):
        from jd_parser import resolve_input

        started = time.perf_counter()
        sample, profile = resolve_input(sample)
        validate_input(sample)
        features, records = features_for_samples([sample], self.encoder)
        statuses = dict(zip([r["id"] for r in sample["requirements"]], self.head.predict(features)))
        result = render_review(sample, statuses, records)
        result["model_profile"] = {key: self.manifest[key] for key in
                                   ("feature_version", "encoder", "encoder_revision", "classifier_sha256")}
        if profile:
            result["jd_profile"] = profile
            result["score_scope"] = "all_prepared_requirements"
            result["scoring_policy_version"] = profile["policy"]["version"]
        result["elapsed_seconds"] = round(time.perf_counter() - started, 4)
        return result
