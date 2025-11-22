FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PIP_DEFAULT_TIMEOUT=300 \
	PIP_RETRIES=10

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --default-timeout=${PIP_DEFAULT_TIMEOUT} --retries ${PIP_RETRIES} -r requirements.txt

COPY orchestrator ./orchestrator
COPY README.md ./README.md

EXPOSE 8010

CMD ["python", "-m", "orchestrator"]
