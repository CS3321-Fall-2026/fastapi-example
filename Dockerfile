FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ARG PROJECT_URL=https://github.com/CS3321-Fall-2024/fastapi-example
ARG PROJECT_BRANCH=main

ENV PATH="/tmp/fastapi-example/.venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT=/tmp/fastapi-example/.venv

RUN apt-get update \
  && apt-get install -y --no-install-recommends --no-install-suggests \
    curl \
    git \
    bash \
    gnupg \
  && ln -sf /bin/bash /bin/sh \
  && curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh | sh \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN git clone $PROJECT_URL
WORKDIR /tmp/fastapi-example

RUN git switch $PROJECT_BRANCH \
  && uv sync --frozen

EXPOSE 80

CMD ["doppler", "run", "--", "uvicorn", "src.fastapi_example.main:app", "--host", "0.0.0.0", "--port", "80"]
