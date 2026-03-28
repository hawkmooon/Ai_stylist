FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    rembg \
    pillow \
    numpy \
    onnxruntime

COPY ai_stylist_v3.py .
COPY hanger.png .

RUN python -c "from rembg import remove; from PIL import Image; import io; \
    img = Image.new('RGB', (10,10), 'white'); \
    buf = io.BytesIO(); img.save(buf, 'JPEG'); \
    remove(buf.getvalue()); print('rembg model indirildi.')"

EXPOSE 8765

CMD ["python", "ai_stylist_v3.py"]
