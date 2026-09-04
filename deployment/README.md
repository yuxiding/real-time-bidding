# Local inference and Docker

Run `aurorabid reproduce` first to generate the probability bundle and `ppo.zip`.

```bash
uvicorn aurorabid.api:app --host 127.0.0.1 --port 8000
```

Set `AURORABID_MODEL_DIR` to serve a different output directory's models.
Startup validates the probability checkpoint; it never trains a replacement.

With Docker installed, run from the repository root:

```bash
docker build -f deployment/Dockerfile -t aurorabid .
docker run --rm -p 127.0.0.1:8000:8000 \
  -v "$(pwd)/outputs/models:/models:ro" aurorabid
```

The image uses CPU PyTorch and a non-root user. Models are mounted read-only.
Only load trusted checkpoints: joblib/PyTorch files are not untrusted-file parsers.

The service provides stateless quotes and does not coordinate balances across
concurrent requests. The API is covered by local tests. Optional container
execution requires Docker and is not presented as a measured production deployment.
