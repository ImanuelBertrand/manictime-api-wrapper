# 1. Use the official uv image for the build stage
FROM ghcr.io/astral-sh/uv:0.11.16-python3.14-trixie AS builder

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

RUN groupadd -g 1001 appgroup && \
    useradd -u 1000 -g 1001 -m appuser

COPY --from=builder /venv /venv
COPY . .

ENV UV_PROJECT_ENVIRONMENT=/venv
ENV PATH="/venv/bin:$PATH"

COPY docker/entrypoint.sh docker/entrypoint.sh
RUN chmod +x docker/entrypoint.sh

USER appuser

ENTRYPOINT ["./docker/entrypoint.sh"]

# --- Squid Stage ---
FROM ubuntu/squid:6.13-25.04_beta AS squid

ARG MT_HOSTNAME=example.invalid

RUN apt-get update && apt-get install -y --no-install-recommends gettext-base && rm -rf /var/lib/apt/lists/*

COPY docker/squid/squid-prod.conf.template /etc/squid/squid.conf.template
COPY docker/squid/squid-entrypoint.sh /squid-entrypoint.sh

RUN chmod +x /squid-entrypoint.sh && \
    envsubst '${MT_HOSTNAME}' < /etc/squid/squid.conf.template > /etc/squid/squid.conf

ENTRYPOINT ["/squid-entrypoint.sh"]

# --- Development Stage ---
FROM production AS development

USER root

COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
RUN uv sync --frozen

RUN apt-get update && apt-get install -y \
    curl git \
    && rm -rf /var/lib/apt/lists/*

RUN chown -R appuser:appgroup /venv

RUN mkdir -p /home/appuser/.local && \
    chown -R appuser:appgroup /home/appuser/.local

ENV PATH="/home/appuser/.local/bin:$PATH"
ENV FLASK_ENV=development

USER appuser
