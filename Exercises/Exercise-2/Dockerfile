# Using Python 3.12 as requested
FROM python:3.12-slim

# Install uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# See logs in real-time by disabling buffering
ENV PYTHONUNBUFFERED=1
# Prevent Python from writing .pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1
# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
# Prevent uv from downloading managed Pythons; use the base image's version
ENV UV_PYTHON_PREFERENCE=only-system
# Copy only the files needed for installing dependencies to take advantage of layer caching.
# These files need to be present in the image for uv sync to work.
# COPY is safer than bind mounts in rootless Podman build environments.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the source code
COPY . .

# Set the virtual environment path and add it to PATH
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"


CMD ["python", "main.py"]