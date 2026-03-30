FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pillow rembg

COPY ai_stylist_v2.py .
COPY hanger.png .

EXPOSE 8765

CMD ["python", "ai_stylist_v2.py"]
