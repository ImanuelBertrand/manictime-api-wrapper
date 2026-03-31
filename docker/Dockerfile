# 1. Use the official uv image for the build stage
FROM ghcr.io/astral-sh/uv:0.11.2-python3.14-trixie AS builder

# 2. Set the working directory
WORKDIR /app

# 3. Enable bytecode compilation for faster startups
ENV UV_LINK_MODE=copy
ENV UV_COMPILE_BYTECODE=1
ENV UV_PROJECT_ENVIRONMENT=/venv
ENV PATH="/venv/bin:$PATH"

# 4. Copy only the lock and project files first
COPY uv.lock pyproject.toml ./

# 5. Install dependencies (without the app itself)
RUN uv sync --frozen --no-install-project --no-dev

# 6. Copy the rest of the app
COPY . .

# 7. Sync the project (installs the app into the venv)
RUN uv sync --frozen --no-dev

# --- Production Stage ---
FROM python:3.14-slim AS production

LABEL org.opencontainers.image.title="Manictime API wrapper"
LABEL org.opencontainers.image.description="Provides secure read-only access to a ManicTime server"
LABEL org.opencontainers.image.authors="Imanuel Bertrand"
LABEL org.opencontainers.image.url="https://github.com/ImanuelBertrand/manictime-api-wrapper"

WORKDIR /app

COPY --from=builder /venv /venv
COPY . .

ENV UV_PROJECT_ENVIRONMENT=/venv
ENV PATH="/venv/bin:$PATH"

COPY docker/entrypoint.sh docker/entrypoint.sh
RUN chmod +x docker/entrypoint.sh

ENTRYPOINT ["./docker/entrypoint.sh"]

# --- Squid Stage ---
FROM ubuntu/squid:6.13-25.04_beta AS squid
COPY docker/squid/squid-prod.conf /etc/squid/squid.conf

# --- Development Stage ---
FROM production AS development

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
RUN uv sync --frozen

RUN apt-get update && apt-get install -y \
    curl git \
    && rm -rf /var/lib/apt/lists/*

# Create group (gid 1001) and user (uid 1000) matching typical host IDs
RUN groupadd -g 1001 appgroup && \
    useradd -u 1000 -g 1001 -m appuser

RUN chown -R appuser:appgroup /venv

# Install Claude Code as appuser so it lands in /home/appuser/.local/bin
RUN su - appuser -c "curl -fsSL https://claude.ai/install.sh | bash"

ENV PATH="/home/appuser/.local/bin:$PATH"
ENV FLASK_ENV=development

USER appuser
