FROM mwader/static-ffmpeg:7.1 AS ffmpeg

FROM python:3.13-slim
# binário estático: ffmpeg do apt arrasta libavdevice->SDL2->X11 (200+ pacotes)
# só pra um binário de linha de comando headless.
COPY --from=ffmpeg /ffmpeg /usr/local/bin/ffmpeg
RUN pip install --no-cache-dir uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
EXPOSE 8000
CMD ["uv", "run", "manage.py", "runserver", "0.0.0.0:8000"]
