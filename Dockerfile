FROM python:3.13-slim

RUN useradd -m -u 1000 user
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=user gateway gateway
COPY --chown=user data data
RUN rm -rf data/uploads && mkdir -p data/uploads && chown -R user /app

USER user
ENV PORT=7860
EXPOSE 7860
WORKDIR /app/gateway
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
