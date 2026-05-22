FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir nicegui>=2.0.0 plotly>=5.0.0 pydantic>=2.0.0 pandas>=2.0.0 pyyaml>=6.0 kaleido>=0.1.0

COPY app/ app/

EXPOSE 8080

CMD ["python", "-m", "app.main"]