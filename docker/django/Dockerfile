# /home/ubuntu/accounting_project/docker/django/Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # uv: don't try to create a venv, install directly into system Python
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1

# Set work directory
WORKDIR /app

# Install system dependencies + uv in a single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Install uv from official binary – much faster than pip for large dep trees
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    ln -s /root/.local/bin/uv /usr/local/bin/uv

# Install Python dependencies with uv
# Copy requirements first to leverage Docker layer cache
COPY ./requirements.txt /app/requirements.txt
RUN uv pip install -r requirements.txt

# Copy project source code
COPY ./src /app/

# Collect static files (optional - can be done in entrypoint or manually)
# RUN python manage.py collectstatic --noinput

# Expose port Gunicorn will run on
EXPOSE 8000

# Run Gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
