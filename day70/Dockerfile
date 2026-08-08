FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
COPY data ./data
RUN pip install --no-cache-dir .
RUN useradd --create-home appuser
USER appuser
CMD ["python", "-m", "customer_support.app"]
