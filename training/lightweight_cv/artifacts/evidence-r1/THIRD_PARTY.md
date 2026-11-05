# Third-party model attribution

The frozen encoder is **intfloat/multilingual-e5-small**, by Liang Wang,
Nan Yang, Xiaolong Huang, Linjun Yang, Rangan Majumder and Furu Wei.

- Original model and license metadata (MIT): https://huggingface.co/intfloat/multilingual-e5-small
- Model card: https://huggingface.co/intfloat/multilingual-e5-small/blob/main/README.md
- Paper: https://arxiv.org/abs/2402.05672
- Initialization: https://huggingface.co/microsoft/Multilingual-MiniLM-L12-H384

The training export preserves the upstream model card and any upstream LICENSE
files present at the recorded revision. Keep these attribution files with the
deployment artifact. The classifier is trained separately; the encoder is frozen.

Follow each package's own license for NumPy, PyTorch, Transformers, scikit-learn,
FastAPI and Uvicorn. This note does not relicense those packages or their models.
