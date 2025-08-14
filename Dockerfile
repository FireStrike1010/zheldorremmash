FROM python:3.12-alpine

# 1. Install only what's strictly needed
RUN apk add --no-cache curl

# 2. Install UV without compilation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    # Add UV to PATH
    echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc

# 3. Make UV available system-wide
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
COPY README.md README.md* ./

# 4. Create venv and install deps
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install -e .

COPY backend .

EXPOSE 8000

CMD ["sh", "-c", "source ../opt/venv/bin/activate && uvicorn docker-app:app --host 0.0.0.0 --port 8000"]