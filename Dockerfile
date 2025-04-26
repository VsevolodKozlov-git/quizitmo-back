FROM python:3.13-slim

# required for psycopg2
RUN apt update \
    && apt install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

# COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
# RUN useradd --no-create-home --gid root runner

# ENV UV_PYTHON_PREFERENCE=only-system
# ENV UV_NO_CACHE=true

WORKDIR /code

# COPY pyproject.toml .
# COPY uv.lock .

COPY pyproject.toml .
COPY requirements.txt .


# RUN uv sync --all-extras --frozen --no-install-project

RUN pip install -r requirements.txt

COPY . .
