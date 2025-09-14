ARG PYTHON_VERSION=3.12.6
FROM python:${PYTHON_VERSION}-slim-bookworm AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONOPTIMIZE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    APP_PATH="/app" \
    UV_VERSION="0.8.11"

ENV VIRTUAL_ENV="$APP_PATH/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR $APP_PATH

FROM python-base AS builder

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv==${UV_VERSION}"

COPY ./pyproject.toml ./uv.lock ./

RUN uv venv -p 3.12 \
    && uv sync --all-extras --no-install-project

COPY ./src ./src
RUN uv sync --all-extras --no-editable

FROM python-base AS runner

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV
