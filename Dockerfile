FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY apps ./apps
COPY scripts ./scripts
COPY tutor ./tutor
COPY exam_packs ./exam_packs
COPY exam-bank ./exam-bank
RUN useradd --uid 10001 --create-home coach
USER coach
ENV PATH="/app/.venv/bin:$PATH" APP_ENV=development PYTHONUNBUFFERED=1 PORT=8080 TZ=Asia/Shanghai
EXPOSE 8080
CMD ["python", "-m", "apps.api.bootstrap"]
