FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY pyproject.toml main.py ./
COPY task_manager/ ./task_manager/

RUN python -m pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "task_manager.api:app", "--host", "0.0.0.0", "--port", "8000"]