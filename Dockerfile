FROM python:3.13-alpine

# 1. Install only what's strictly needed
RUN apk add --no-cache curl

# 2. Install UV without compilation
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    # Add UV to PATH
    echo 'export PATH="/root/.local/bin:$PATH"' >> /root/.bashrc

# 3. Make UV available system-wide
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /backend
COPY . .

# 4. Create venv and install deps
RUN uv venv && \
    . .venv/bin/activate && \
    uv pip install -e .

EXPOSE 8000
CMD ["sh", "-c", "source .venv/bin/activate && cd backend && uvicorn docker-app:app --host 0.0.0.0 --port 8000"]