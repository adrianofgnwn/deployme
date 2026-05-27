# DeployMe backend image — pinned base, runs as a non-root user.
FROM python:3.11-slim

# No .pyc files, unbuffered logs (so container logs stream immediately).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Create an unprivileged user up front; we never run as root.
RUN groupadd --system app && useradd --system --gid app --create-home app

# Install dependencies first so the layer caches across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and hand ownership to the non-root user.
COPY . .
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
