FROM python:3.12-bookworm

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PNPM_HOME="/pnpm" \
    VIRTUAL_ENV="/opt/venv" \
    PATH="/opt/venv/bin:/pnpm:${PATH}"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl bash ca-certificates gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_23.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN corepack enable && corepack prepare pnpm@10.6.3 --activate

RUN python -m venv "${VIRTUAL_ENV}"

COPY package.json pnpm-workspace.yaml ./
COPY apps/web/package.json ./apps/web/package.json
RUN pnpm install --filter investment-platform-web... --no-frozen-lockfile

COPY apps/backend/pyproject.toml ./apps/backend/pyproject.toml
COPY apps/agent/pyproject.toml ./apps/agent/pyproject.toml
RUN pip install --upgrade pip setuptools wheel \
    && pip install -e ./apps/backend -e ./apps/agent

COPY . .

RUN chmod +x /app/apps/start-entrypoint.sh

EXPOSE 3000 8000 9002

CMD ["/app/apps/start-entrypoint.sh"]
