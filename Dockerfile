ARG python=python:3.13-slim-trixie
ARG TARGETARCH

FROM ${python} AS cbot-builder-python
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG TARGETARCH
ENV TARGETARCH=${TARGETARCH:-amd64}

RUN apt update -y
RUN apt install -y g++
RUN apt-get clean

WORKDIR /app
ENV UV_NO_DEV=1

RUN --mount=type=cache,target=/root/.cache/uv,id=uv-${TARGETARCH} \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY pyproject.toml .
COPY uv.lock .
RUN --mount=type=cache,target=/root/.cache/uv,id=uv-${TARGETARCH} \
    uv sync --locked --no-editable

FROM node:22.12-slim AS cbot-builder-node
WORKDIR /app
COPY cbot/client_web/*.json .
COPY cbot/client_web/*.js .
COPY cbot/client_web/src src
RUN npm ci
RUN npm run build

FROM ${python}
RUN apt update -y
RUN apt install -y curl nginx
RUN pip install --no-cache-dir supervisor
RUN apt-get clean
RUN mkdir /app /app/run /etc/cbot
COPY --from=cbot-builder-node /app/dist /app/web
COPY --from=cbot-builder-python /app/.venv /app/.venv
ENV PATH=/app/.venv/bin:$PATH
WORKDIR /app
ADD bin bin
ADD cbot cbot
EXPOSE 80
EXPOSE 2268
EXPOSE 2269
COPY conf/docker/etc/supervisord.conf /etc/supervisord.conf
COPY conf/docker/etc/nginx/ /etc/nginx/

HEALTHCHECK --interval=60m --timeout=3s CMD curl -f http://localhost/ || exit 1
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]
