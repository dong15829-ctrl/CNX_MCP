FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 최소 설치(필요 시 추가)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY main.py index.html requirements.txt* ./
RUN pip install --no-cache-dir fastapi uvicorn httpx python-dotenv openai websockets || true \
    && if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
