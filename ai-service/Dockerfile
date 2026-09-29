FROM python:3.11-slim

WORKDIR /srv

COPY requirements.txt .
# sentence-transformers pulls in torch, and pip's default Linux wheel drags
# in multi-hundred-MB CUDA packages even with no GPU present. Force the
# small CPU-only build first so the rest of the install stays lightweight.
RUN pip install --no-cache-dir --timeout 120 --retries 10 torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
