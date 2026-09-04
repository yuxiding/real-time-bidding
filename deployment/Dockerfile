FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu \
    && python -m pip install --no-cache-dir .
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
ENV AURORABID_MODEL_DIR=/models
EXPOSE 8000
CMD ["uvicorn", "aurorabid.api:app", "--host", "0.0.0.0", "--port", "8000"]
