ARG python=python:3.11-slim

FROM ${python} AS cbot-builder-python
RUN apt update -y
RUN apt install -y g++
RUN apt-get clean
WORKDIR /app
RUN python -m venv /venv
ENV PATH=/venv/bin:$PATH
RUN pip install --no-cache-dir poetry==1.7.1
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry config virtualenvs.create false
RUN poetry config installer.max-workers 10
RUN poetry install --no-dev -n

FROM node:20.17-slim AS cbot-builder-node
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
COPY --from=cbot-builder-python /venv /venv
ENV PATH=/venv/bin:$PATH
WORKDIR /app
ADD bin bin
ADD cbot cbot
ENV PYTHONPATH "${PYTHONPATH}:/app"
EXPOSE 80
EXPOSE 2268
EXPOSE 2269
COPY conf/docker/etc/supervisord.conf /etc/supervisord.conf
COPY conf/docker/etc/nginx/ /etc/nginx/
HEALTHCHECK --interval=60m --timeout=3s CMD curl -f http://localhost/ || exit 1
CMD /usr/local/bin/supervisord -c /etc/supervisord.conf
