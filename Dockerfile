FROM python:3.11-slim

# Sistem bağımlılıkları (rembg için gerekli)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python paketleri
RUN pip install --no-cache-dir \
    rembg \
    pillow \
    numpy \
    onnxruntime

# Uygulama dosyaları
COPY ai_stylist_v3.py .
COPY hanger.png .

# rembg modelini önceden indir (ilk istekte gecikme olmasın)
RUN python -c "from rembg import remove; from PIL import Image; import io; \
    img = Image.new('RGB', (10,10), 'white'); \
    buf = io.BytesIO(); img.save(buf, 'JPEG'); \
    remove(buf.getvalue()); print('rembg model indirildi.')"

EXPOSE 8765

CMD ["python", "ai_stylist_v3.py"]
