import socket
import json
import urllib.request
import urllib.error
import os
import sys
import threading
import base64
import io

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "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")
PORT = int(os.environ.get("PORT", 8765))
MAX_TOKENS_LIMIT = 2000

# ──────────────────────────────────────────────
# HANGER IMAGE PROCESSING (rembg + Pillow)
# ──────────────────────────────────────────────
try:
    from rembg import remove
    from PIL import Image
    REMBG_AVAILABLE = True
    print("[INFO] rembg + Pillow aktif, gerçek askı görselleri kullanılacak.")
except ImportError:
    REMBG_AVAILABLE = False
    print("[WARN] rembg veya Pillow yok, SVG moduna dönülüyor.")

HANGER_PATH = os.path.join(os.path.dirname(__file__), "hanger.png")

def process_cloth_with_hanger(image_b64, category="üst"):
    """Kıyafetten arka planı sil, ahşap askıya bindir, base64 PNG döndür."""
    if not REMBG_AVAILABLE:
        return None

    hanger_path = HANGER_PATH
    if not os.path.exists(hanger_path):
        print("[WARN] hanger.png bulunamadı:", hanger_path)
        return None

    try:
        # base64 → PIL Image
        img_data = base64.b64decode(image_b64)
        input_image = Image.open(io.BytesIO(img_data)).convert("RGBA")

        # 1) Arka plan sil
        cloth = remove(input_image)

        # 2) Boşlukları temizle (crop)
        bbox = cloth.getbbox()
        if not bbox:
            return None
        cloth = cloth.crop(bbox)

        # 3) Kategoriye göre boyutlandır
        if category in ("üst", "aksesuar", "iç"):
            cloth_size = (200, 200)
        elif category == "alt":
            cloth_size = (180, 220)
        elif category == "ayak":
            cloth_size = (200, 150)
        else:
            cloth_size = (200, 200)
        cloth = cloth.resize(cloth_size, Image.LANCZOS)

        # 4) Askıyı yükle
        hanger = Image.open(hanger_path).convert("RGBA")

        # 5) Canvas = askı boyutu
        canvas = Image.new("RGBA", hanger.size, (0, 0, 0, 0))
        canvas.paste(hanger, (0, 0), hanger)

        # 6) Kategoriye göre Y offset
        if category == "üst":
            offset_y = int(hanger.size[1] * 0.38)
        elif category == "alt":
            offset_y = int(hanger.size[1] * 0.42)
        elif category == "ayak":
            offset_y = int(hanger.size[1] * 0.48)
        else:
            offset_y = int(hanger.size[1] * 0.40)

        offset_x = (hanger.size[0] - cloth_size[0]) // 2

        # 7) Gölge efekti
        shadow = cloth.copy()
        shadow_pixels = shadow.load()
        w, h = shadow.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = shadow_pixels[x, y]
                shadow_pixels[x, y] = (0, 0, 0, int(a * 0.22))
        canvas.paste(shadow, (offset_x + 4, offset_y + 4), shadow)

        # 8) Kıyafeti koy
        canvas.paste(cloth, (offset_x, offset_y), cloth)

        # 9) PNG → base64
        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG", optimize=True)
        return base64.b64encode(buffer.getvalue()).decode()

    except Exception as e:
        print("[HATA] process_cloth_with_hanger:", e)
        return None


FIREBASE_CONFIG = {
    "apiKey": "AIzaSyBeE62ZcocMTDNIfeKFyfDDNr_evWon_9w",
    "authDomain": "ai-stylist-94c04.firebaseapp.com",
    "projectId": "ai-stylist-94c04",
    "storageBucket": "ai-stylist-94c04.firebasestorage.app",
    "messagingSenderId": "360910240515",
    "appId": "1:360910240515:web:6530b5d571fe1280bb8736"
}

INDEX_HTML = r'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dolabim - AI Stylist</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Playfair+Display:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/cropperjs/1.6.2/cropper.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Playfair+Display:wght@400;500;600;700&display=swap');

*{box-sizing:border-box;margin:0;padding:0;}

:root{
  --wood-dark:#3d2a14;
  --wood-mid:#6b4c28;
  --wood-light:#a07840;
  --wood-plank:#8b6535;
  --wood-grain:#c4a06a;
  --oak-inner:#ede0c4;
  --oak-panel:#d9c498;
  --oak-mid:#c8a870;
  --oak-shelf:#e2d0a8;
  --oak-frame:#7a5828;
  --gold:#c9a84c;
  --gold-light:#e0c06a;
  --gold-shine:#f5e199;
  --brass:#b8860b;
  --cream:#f7f0e6;
  --warm-white:#fdf8f2;
  --text-dark:#1e1208;
  --text-mid:#5c3d22;
  --text-light:#9b7a56;
  --shadow-deep:rgba(15,8,2,0.55);
  --shadow-mid:rgba(30,16,6,0.3);
  --shadow-soft:rgba(80,50,20,0.12);
}

body{
  background:var(--cream);
  font-family:'Cormorant Garamond',Georgia,serif;
  color:var(--text-dark);
  min-height:100vh;
}

::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:#e8ddd0;}
::-webkit-scrollbar-thumb{background:var(--gold);border-radius:3px;}

/* ── ANIMATIONS ── */
@keyframes fadeUp{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:translateY(0)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes float{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-10px) rotate(2deg)}}
@keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
@keyframes doorSwing{
  0%{transform:perspective(800px) rotateY(0deg);box-shadow:inset -8px 0 30px var(--shadow-deep);}
  100%{transform:perspective(800px) rotateY(-115deg);box-shadow:none;opacity:0.2;}
}
@keyframes clothFlyIn{
  0%{opacity:0;transform:translateY(60px) scale(0.4) rotate(-5deg)}
  65%{transform:translateY(-6px) scale(1.04) rotate(1deg)}
  100%{opacity:1;transform:translateY(0) scale(1) rotate(0deg)}
}
@keyframes hangSwing{
  0%,100%{transform:rotate(-5deg) translateX(-2px)}
  50%{transform:rotate(5deg) translateX(2px)}
}
@keyframes woodGrain{
  0%{opacity:.06} 50%{opacity:.12} 100%{opacity:.06}
}

.fade-up{animation:fadeUp .5s cubic-bezier(.22,1,.36,1) forwards;}
.cloth-fly-in{animation:clothFlyIn 0.75s cubic-bezier(0.34,1.56,0.64,1) forwards;}
.hang-swing{animation:hangSwing 0.5s ease-in-out 3;}

/* ── AUTH SCREEN ── */
#auth-screen{
  position:fixed;inset:0;z-index:1000;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:40px 24px;overflow:hidden;
  background:
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 60px,
      rgba(255,255,255,.015) 60px,
      rgba(255,255,255,.015) 62px
    ),
    linear-gradient(160deg, var(--wood-dark) 0%, var(--wood-mid) 40%, var(--wood-plank) 70%, var(--wood-grain) 100%);
}

#auth-screen::before{
  content:'';position:absolute;inset:0;
  background:
    repeating-linear-gradient(
      2deg,
      transparent,
      transparent 18px,
      rgba(0,0,0,.04) 18px,
      rgba(0,0,0,.04) 20px
    );
  pointer-events:none;
}

.auth-emblem{
  width:90px;height:90px;
  border-radius:50%;
  background:radial-gradient(circle at 35% 35%, var(--gold-shine), var(--gold) 50%, var(--brass) 100%);
  display:flex;align-items:center;justify-content:center;
  font-size:40px;margin-bottom:28px;
  box-shadow:0 8px 30px var(--shadow-deep), inset 0 2px 4px rgba(255,255,255,.3);
  animation:float 4s ease-in-out infinite;
}

.auth-logo{
  font-family:'Playfair Display',serif;
  font-size:46px;font-weight:700;
  color:var(--cream);
  letter-spacing:3px;
  margin-bottom:6px;
  text-shadow:0 2px 20px var(--shadow-deep);
}

.auth-sub{
  font-size:11px;letter-spacing:6px;
  background:linear-gradient(90deg, var(--gold), var(--gold-shine), var(--gold));
  background-size:200% auto;
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  animation:shimmer 3s linear infinite;
  text-transform:uppercase;
  margin-bottom:56px;
}

.auth-divider{
  width:120px;height:1px;
  background:linear-gradient(90deg, transparent, var(--gold), transparent);
  margin-bottom:40px;
}

.google-btn{
  background:var(--warm-white);
  border:none;border-radius:4px;
  padding:16px 32px;
  font-size:16px;font-family:'Cormorant Garamond',serif;
  cursor:pointer;
  display:flex;align-items:center;gap:14px;
  box-shadow:0 4px 24px var(--shadow-deep), 0 1px 0 rgba(255,255,255,.2) inset;
  transition:all .3s cubic-bezier(.22,1,.36,1);
  width:100%;max-width:300px;justify-content:center;
  letter-spacing:.5px;
  position:relative;overflow:hidden;
}
.google-btn::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg, rgba(255,255,255,.3) 0%, transparent 60%);
  pointer-events:none;
}
.google-btn:hover{transform:translateY(-3px);box-shadow:0 10px 40px var(--shadow-deep);}
.google-icon{width:22px;height:22px;flex-shrink:0;}
.auth-note{color:rgba(196,168,130,.7);font-size:12px;margin-top:22px;text-align:center;font-style:italic;}

/* ── ONBOARD SCREEN ── */
#onboard-screen{
  position:fixed;inset:0;background:var(--warm-white);z-index:900;
  display:flex;flex-direction:column;align-items:center;padding:40px 20px;
  overflow-y:auto;
}

.onboard-title{
  font-family:'Playfair Display',serif;font-size:30px;color:var(--text-dark);
  margin-bottom:6px;text-align:center;
}
.onboard-sub{color:var(--text-light);font-style:italic;margin-bottom:32px;text-align:center;font-size:15px;}

.body-upload-zone{
  border:2px dashed var(--gold);border-radius:4px;padding:44px 20px;
  text-align:center;cursor:pointer;background:#fff;width:100%;max-width:360px;
  margin-bottom:20px;transition:all .3s;
  box-shadow:inset 0 0 40px rgba(201,168,76,.04);
}
.body-upload-zone:hover{border-color:var(--wood-plank);background:#fdf5ea;transform:translateY(-2px);}

.body-analysis{background:#fff;border-radius:4px;padding:16px;width:100%;max-width:360px;
  margin-bottom:20px;border-left:3px solid var(--gold);}
.analysis-item{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #f0e8e0;font-size:14px;}
.analysis-item:last-child{border:none;}
.analysis-label{color:var(--text-light);}
.analysis-value{font-weight:500;color:var(--text-dark);}

.start-btn{
  background:linear-gradient(135deg, var(--wood-plank), var(--wood-mid));
  color:var(--cream);border:none;border-radius:4px;
  padding:18px;font-size:17px;width:100%;max-width:360px;
  cursor:pointer;font-family:'Playfair Display',serif;
  letter-spacing:1px;transition:all .3s;
  box-shadow:0 4px 20px var(--shadow-mid);
}
.start-btn:hover{transform:translateY(-2px);box-shadow:0 8px 30px var(--shadow-mid);}
.start-btn:disabled{background:#d4c4b4;box-shadow:none;cursor:not-allowed;transform:none;}

/* ── HEADER ── */
.header{
  background:
    repeating-linear-gradient(
      90deg,
      transparent, transparent 58px,
      rgba(255,255,255,.018) 58px, rgba(255,255,255,.018) 60px
    ),
    linear-gradient(180deg, var(--wood-dark) 0%, var(--wood-mid) 100%);
  padding:18px 18px 14px;
  position:sticky;top:0;z-index:100;
  border-bottom:3px solid var(--gold);
  box-shadow:0 4px 20px var(--shadow-deep);
}

.header-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}

.header-title{
  font-family:'Playfair Display',serif;font-size:22px;
  color:var(--cream);letter-spacing:2px;
}
.header-title span{
  color:var(--gold);
}

.user-avatar{
  width:36px;height:36px;border-radius:50%;
  border:2px solid var(--gold);cursor:pointer;
  box-shadow:0 2px 10px var(--shadow-deep);
}

/* TABS */
.tabs{display:flex;justify-content:center;gap:0;background:rgba(0,0,0,.2);border-radius:3px;overflow:hidden;}
.tab{
  flex:1;padding:9px 8px;font-size:11px;letter-spacing:1.5px;
  text-transform:uppercase;cursor:pointer;
  font-family:'Cormorant Garamond',serif;
  transition:all .25s;background:transparent;
  color:rgba(196,168,130,.6);border:none;
  border-right:1px solid rgba(255,255,255,.08);
}
.tab:last-child{border-right:none;}
.tab.active{
  background:linear-gradient(180deg, var(--gold-light), var(--gold));
  color:var(--wood-dark);font-weight:600;
}

/* ── MAIN ── */
.container{max-width:480px;margin:0 auto;padding:20px 16px 90px;}
.screen{display:none;}
.screen.active{display:block;}

/* ── WARDROBE ── */
.wardrobe-outer{
  position:relative;
  border-radius:10px;
  overflow:hidden;
  margin-bottom:18px;
  border:2px solid #1a1d1e;
  box-shadow:
    0 20px 60px rgba(0,0,0,0.5),
    0 4px 16px rgba(0,0,0,0.3),
    inset 0 1px 0 rgba(255,255,255,0.06);
}

/* SVG arka plan — tam genişlik, sabit oran */
.wardrobe-svg-bg{
  display:block;
  width:100%;
  height:260px;
  position:absolute;
  top:0;left:0;
}

/* Kıyafetler katmanı — SVG üzerinde, tam kaplama */
.clothes-layer{
  position:relative;
  z-index:2;
  width:100%;
  height:260px;
  display:flex;
  flex-direction:column;
}

/* Kapı animasyonu */
.wardrobe-door-overlay{
  position:absolute;inset:0;
  background:
    repeating-linear-gradient(
      90deg,
      transparent, transparent 58px,
      rgba(255,255,255,.03) 58px, rgba(255,255,255,.03) 60px
    ),
    linear-gradient(160deg, #4a3520 0%, #3a2810 40%, #2e2008 80%, #1e1404 100%);
  z-index:10;transform-origin:left center;
  display:flex;align-items:center;justify-content:flex-end;
  padding-right:24px;
  cursor:pointer;
  pointer-events:auto;
  transition:box-shadow 0.2s;
}
.wardrobe-door-overlay:hover .door-handle{
  filter:brightness(1.2);
}
.wardrobe-door-overlay::before{
  content:'';
  position:absolute;top:12px;right:12px;bottom:12px;left:12px;
  border:1px solid rgba(255,255,255,0.06);
  border-radius:2px;
}
.wardrobe-door-overlay.open{animation:doorSwing 0.7s cubic-bezier(.4,0,.2,1) forwards;}

.door-handle{
  width:8px;height:48px;
  background:linear-gradient(180deg, #e0e0e0 0%, #b8b8b8 40%, #d8d8d8 100%);
  border-radius:4px;
  box-shadow:0 2px 10px rgba(0,0,0,0.6), inset 0 1px 2px rgba(255,255,255,0.4);
}
.door-handle::before{
  content:'';position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);
  width:14px;height:14px;border-radius:50%;
  background:radial-gradient(circle at 35% 35%, #f0f0f0, #a0a0a0);
  box-shadow:0 2px 6px rgba(0,0,0,0.5);
}

/* Kıyafet askı rayı alanı — SVG'deki ray ile hizalı */
.clothes-rail{
  position:absolute;
  top:62px; /* SVG'deki ray'ın altına denk geliyor */
  left:0;right:0;bottom:0;
  display:flex;
  gap:4px;
  overflow-x:auto;
  padding:0 20px 28px;
  align-items:flex-start;
}
.clothes-rail::-webkit-scrollbar{height:3px;}
.clothes-rail::-webkit-scrollbar-thumb{background:rgba(200,200,200,.25);}

/* Tek hanger item */
.hanger-item{
  flex-shrink:0;
  width:80px;
  cursor:pointer;
  text-align:center;
  display:flex;flex-direction:column;align-items:center;
  transition:transform .3s cubic-bezier(.22,1,.36,1);
}
.hanger-item:hover{transform:translateY(-8px) scale(1.05);}

/* Gerçek tel askı SVG */
.hanger-wire{
  width:72px;
  height:52px;
  display:block;
  flex-shrink:0;
}

/* Kıyafet görseli — askının hemen altında */
.real-hanger{
  width:76px;height:90px;
  object-fit:contain;
  display:block;
  margin-top:-8px;
  filter:drop-shadow(0 6px 14px rgba(0,0,0,0.7));
  border-radius:4px;
}

/* Gerçek fotoğraf (rembg'siz) — beyaz arka planla kırpılmış görünüm */
.real-photo-hanger{
  width:76px;height:86px;
  object-fit:cover;
  object-position:center top;
  display:block;
  margin-top:-6px;
  border-radius:6px;
  box-shadow:0 6px 18px rgba(0,0,0,0.75), 0 2px 4px rgba(0,0,0,0.5);
  border:1px solid rgba(255,255,255,0.08);
}

.hanger-svg{
  width:64px;height:78px;
  margin-top:-8px;
  filter:drop-shadow(0 5px 12px rgba(0,0,0,0.65));
}
.hanger-svg svg{width:100%;height:100%;}

/* Claude tarafından üretilen SVG — daha büyük ve detaylı */
.ai-generated-svg{
  width:76px;height:90px;
  margin-top:-10px;
  filter:drop-shadow(0 6px 16px rgba(0,0,0,0.75)) drop-shadow(0 2px 4px rgba(0,0,0,0.5));
}
.ai-generated-svg svg{width:100%;height:100%;}

.hanger-label{
  font-size:9px;
  color:rgba(220,220,220,0.7);
  margin-top:4px;
  max-width:78px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
  letter-spacing:.3px;
  transition:color .2s;
}
.hanger-item:hover .hanger-label{color:rgba(255,255,255,0.95);}

/* Empty state */
.wardrobe-empty{
  position:absolute;
  top:50%;left:50%;transform:translate(-50%,-50%);
  text-align:center;
  color:rgba(200,200,200,0.4);
  font-style:italic;font-size:14px;
  line-height:1.8;white-space:nowrap;
}

/* ── UPLOAD ZONE ── */
.upload-zone{
  border:2px dashed var(--gold);
  border-radius:4px;padding:30px 20px;
  text-align:center;cursor:pointer;
  background:rgba(255,255,255,.8);
  margin-bottom:16px;transition:all .3s;
  position:relative;overflow:hidden;
}
.upload-zone::before{
  content:'';position:absolute;inset:0;
  background:linear-gradient(135deg, rgba(201,168,76,.04) 0%, transparent 60%);
  pointer-events:none;
}
.upload-zone:hover{border-color:var(--wood-plank);background:#fdf5ea;transform:translateY(-2px);}
.upload-icon{font-size:30px;margin-bottom:8px;}
.upload-text{font-size:15px;color:var(--text-light);font-style:italic;}

/* ── SUGGEST SCREEN ── */
.section-label{
  font-size:10px;letter-spacing:4px;text-transform:uppercase;
  color:var(--text-light);margin-bottom:10px;
  display:flex;align-items:center;gap:10px;
}
.section-label::after{
  content:'';flex:1;height:1px;
  background:linear-gradient(90deg, var(--gold), transparent);
  opacity:.4;
}

.weather-opts{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px;}
.event-opts{display:flex;flex-direction:column;gap:8px;margin-bottom:26px;}

.opt-btn{
  border-radius:3px;padding:9px 15px;font-size:14px;cursor:pointer;
  font-family:'Cormorant Garamond',serif;transition:all .2s;
  background:#fff;color:var(--text-mid);
  border:1px solid rgba(201,168,76,.4);
  box-shadow:0 2px 6px rgba(0,0,0,.04);
}
.opt-btn:hover{border-color:var(--gold);background:#fdf5ea;}
.opt-btn.selected{
  background:linear-gradient(135deg, var(--wood-plank), var(--wood-mid));
  color:var(--cream);border-color:var(--wood-plank);
  box-shadow:0 3px 12px var(--shadow-mid);
}

.event-btn{
  border-radius:4px;padding:14px 16px;font-size:15px;text-align:left;
  border:1px solid rgba(201,168,76,.35);cursor:pointer;
  font-family:'Cormorant Garamond',serif;
  transition:all .25s;background:#fff;color:var(--text-mid);width:100%;
  box-shadow:0 2px 8px rgba(0,0,0,.04);
}
.event-btn:hover{border-color:var(--gold);background:#fdf8f0;transform:translateX(4px);}
.event-btn.selected{
  background:linear-gradient(135deg, var(--wood-plank), var(--wood-mid));
  color:var(--cream);border-color:transparent;
  box-shadow:0 4px 16px var(--shadow-mid);
  transform:translateX(4px);
}

.suggest-btn{
  width:100%;
  background:linear-gradient(135deg, var(--gold-light) 0%, var(--gold) 50%, var(--brass) 100%);
  color:var(--wood-dark);border:none;border-radius:4px;
  padding:18px;font-size:16px;letter-spacing:2px;margin-bottom:24px;
  box-shadow:0 6px 24px rgba(184,134,11,.35);cursor:pointer;
  font-family:'Playfair Display',serif;font-weight:600;
  transition:all .3s cubic-bezier(.22,1,.36,1);
  text-transform:uppercase;
}
.suggest-btn:hover{transform:translateY(-3px);box-shadow:0 12px 36px rgba(184,134,11,.4);}
.suggest-btn:disabled{
  background:linear-gradient(135deg, #d4c4a8, #bfaa8c);
  box-shadow:none;cursor:not-allowed;transform:none;color:#8b7a65;
}

/* ── RESULT BOX ── */
.result-box{
  background:#fff;border-radius:4px;padding:26px 22px;
  border-top:3px solid var(--gold);
  box-shadow:0 8px 32px rgba(0,0,0,.08);margin-bottom:20px;
}
.result-line{
  width:40px;height:2px;
  background:linear-gradient(90deg, var(--gold), var(--gold-light));
  margin-bottom:18px;
}
.result-text h3{font-family:'Playfair Display',serif;color:var(--wood-plank);font-size:16px;margin:16px 0 7px;}
.result-text p{line-height:1.9;color:var(--text-mid);font-size:15px;margin-bottom:6px;}
.result-text strong{color:var(--wood-plank);}
.feedback-row{display:flex;gap:12px;margin-top:18px;}
.feedback-btn{
  flex:1;padding:11px;border-radius:3px;
  border:1px solid #d4c4b4;background:#fff;
  cursor:pointer;font-family:'Cormorant Garamond',serif;
  font-size:15px;transition:all .2s;
}
.feedback-btn.like{border-color:#5a9e6e;color:#5a9e6e;}
.feedback-btn.like:hover,.feedback-btn.like.active{background:#5a9e6e;color:#fff;}
.feedback-btn.dislike{border-color:#c0614e;color:#c0614e;}
.feedback-btn.dislike:hover,.feedback-btn.dislike.active{background:#c0614e;color:#fff;}

/* ── LOADING ── */
.loading{text-align:center;padding:24px;}
.spinner{
  border:3px solid rgba(201,168,76,.2);
  border-top-color:var(--gold);
  border-radius:50%;width:38px;height:38px;
  animation:spin .8s linear infinite;margin:0 auto 14px;
}
.loading-text{color:var(--text-light);font-style:italic;font-size:15px;}

/* ── AI TOAST ── */
.ai-toast{
  position:fixed;bottom:90px;left:50%;transform:translateX(-50%);
  background:linear-gradient(135deg, var(--wood-dark), var(--wood-mid));
  color:var(--cream);border-radius:4px;padding:14px 22px;
  font-size:14px;font-style:italic;max-width:320px;text-align:center;
  box-shadow:0 8px 30px var(--shadow-deep);z-index:500;
  border-top:2px solid var(--gold);
  animation:fadeUp .4s cubic-bezier(.22,1,.36,1) forwards;
}
.ai-toast-emoji{font-size:22px;display:block;margin-bottom:5px;}

/* ── CLOTH DETAIL ── */
.cloth-detail-overlay{
  position:fixed;inset:0;background:rgba(10,5,2,.75);z-index:800;
  display:flex;align-items:flex-end;
  backdrop-filter:blur(4px);
}
.cloth-detail-sheet{
  background:var(--warm-white);
  border-radius:12px 12px 0 0;
  border-top:3px solid var(--gold);
  padding:26px 22px 44px;
  width:100%;max-height:80vh;overflow-y:auto;
  box-shadow:0 -20px 60px var(--shadow-deep);
}
.cloth-detail-img{width:100%;max-height:300px;object-fit:contain;border-radius:4px;margin-bottom:18px;}
.cloth-tags{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px;}
.cloth-tag-chip{
  background:rgba(201,168,76,.1);
  border:1px solid rgba(201,168,76,.4);
  border-radius:3px;padding:4px 12px;
  font-size:12px;color:var(--text-mid);
  letter-spacing:.5px;
}
.remove-cloth-btn{
  width:100%;padding:13px;border:1px solid #c0614e;border-radius:4px;
  color:#c0614e;background:#fff;
  font-family:'Cormorant Garamond',serif;font-size:15px;cursor:pointer;
  transition:all .2s;
}
.remove-cloth-btn:hover{background:#c0614e;color:#fff;}

/* ── PROFILE ── */
.profile-card{
  background:#fff;border-radius:4px;padding:24px 22px;
  margin-bottom:16px;
  border-left:3px solid var(--gold);
  box-shadow:0 4px 20px rgba(0,0,0,.07);
}
.profile-avatar{width:72px;height:72px;border-radius:50%;border:3px solid var(--gold);margin-bottom:14px;box-shadow:0 4px 16px rgba(0,0,0,.15);}
.profile-name{font-family:'Playfair Display',serif;font-size:22px;margin-bottom:4px;color:var(--text-dark);}
.profile-email{color:var(--text-light);font-size:13px;margin-bottom:18px;}
.profile-stat{display:flex;justify-content:space-around;padding-top:14px;border-top:1px solid #f0e8e0;}
.stat-item{text-align:center;}
.stat-num{font-family:'Playfair Display',serif;font-size:26px;color:var(--wood-plank);}
.stat-label{font-size:10px;color:var(--text-light);letter-spacing:2px;text-transform:uppercase;}

.logout-btn{
  width:100%;padding:13px;
  border:1px solid rgba(201,168,76,.4);
  border-radius:4px;color:var(--text-light);background:#fff;
  font-family:'Cormorant Garamond',serif;font-size:15px;cursor:pointer;
  margin-top:10px;transition:all .2s;
}
.logout-btn:hover{border-color:var(--wood-plank);color:var(--wood-plank);}

.error-box{background:#fff5f5;border-left:3px solid #c0614e;border-radius:4px;padding:14px;margin-bottom:14px;color:#9b3a2a;font-size:14px;}

/* ── CROPPER MODAL ── */
#cropper-modal{
  position:fixed;inset:0;z-index:2000;
  background:rgba(10,6,2,0.92);
  display:flex;flex-direction:column;
  align-items:center;justify-content:flex-start;
  padding:0;
}
.cropper-modal-header{
  width:100%;display:flex;align-items:center;justify-content:space-between;
  padding:16px 20px 12px;
  border-bottom:1px solid rgba(201,168,76,0.25);
  flex-shrink:0;
}
.cropper-modal-title{
  font-family:'Playfair Display',serif;
  color:var(--cream);font-size:17px;letter-spacing:1px;
}
.cropper-modal-hint{
  color:rgba(196,168,130,0.6);font-size:11px;
  letter-spacing:.5px;margin-top:2px;
}
.cropper-img-wrap{
  flex:1;width:100%;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
  padding:12px;
  min-height:0;
}
#cropper-img{
  max-width:100%;max-height:100%;
  display:block;
}
.cropper-actions{
  width:100%;display:flex;gap:10px;
  padding:14px 16px 28px;
  flex-shrink:0;
}
.cropper-btn-cancel{
  flex:1;padding:14px;border-radius:4px;
  background:transparent;
  border:1px solid rgba(201,168,76,0.35);
  color:rgba(196,168,130,0.8);
  font-family:'Cormorant Garamond',serif;font-size:15px;
  cursor:pointer;letter-spacing:.5px;transition:all .2s;
}
.cropper-btn-cancel:hover{border-color:var(--gold);color:var(--gold);}
.cropper-btn-confirm{
  flex:2;padding:14px;border-radius:4px;
  background:linear-gradient(135deg, var(--gold-light), var(--gold));
  border:none;
  color:var(--wood-dark);
  font-family:'Playfair Display',serif;font-size:15px;font-weight:600;
  cursor:pointer;letter-spacing:1px;transition:all .2s;
  box-shadow:0 4px 16px rgba(184,134,11,0.35);
}
.cropper-btn-confirm:hover{box-shadow:0 6px 22px rgba(184,134,11,0.5);}
.cropper-counter{
  color:rgba(196,168,130,0.5);font-size:11px;
  text-align:center;margin-bottom:6px;letter-spacing:.5px;
}
</style>
</head>
<body>

<!-- AUTH SCREEN -->
<div id="auth-screen">
  <div class="auth-emblem">👗</div>

<!-- CROPPER MODAL -->
<div id="cropper-modal" style="display:none;">
  <div class="cropper-modal-header">
    <div>
      <div class="cropper-modal-title">Kıyafeti Kırp</div>
      <div class="cropper-modal-hint">Sadece kıyafeti seçin, arka planı dışarıda bırakın</div>
    </div>
    <div class="cropper-counter" id="cropper-counter"></div>
  </div>
  <div class="cropper-img-wrap">
    <img id="cropper-img" src="">
  </div>
  <div class="cropper-actions">
    <button class="cropper-btn-cancel" onclick="cropperCancel()">İptal</button>
    <button class="cropper-btn-confirm" onclick="cropperConfirm()">✓ Onayla ve Ekle</button>
  </div>
</div>
  <div class="auth-logo">Dolabım</div>
  <div class="auth-sub">AI Kişisel Stilist</div>
  <div class="auth-divider"></div>
  <button class="google-btn" onclick="signInWithGoogle()">
    <svg class="google-icon" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
    </svg>
    Google ile Giriş Yap
  </button>
  <p class="auth-note">Dolabın güvende saklanır ve<br>sadece sen görebilirsin</p>
</div>

<!-- ONBOARD SCREEN -->
<div id="onboard-screen" style="display:none;">
  <h2 class="onboard-title">Seni Tanıyalım</h2>
  <p class="onboard-sub">Boy fotoğrafını çek, sana özel kombin yapalım</p>
  <div class="body-upload-zone" onclick="document.getElementById('bodyInput').click()">
    <div style="font-size:48px;margin-bottom:10px;">🧍</div>
    <div style="font-size:16px;color:#8b7355;font-style:italic;">Boy fotoğrafı yükle</div>
    <div style="font-size:12px;color:#b0a090;margin-top:6px;">Baştan ayağa tam boy</div>
  </div>
  <input type="file" id="bodyInput" accept="image/*" style="display:none" onchange="handleBodyPhoto(this.files[0])">
  <div id="body-preview-wrap" style="display:none;width:100%;max-width:360px;">
    <img id="body-preview-img" style="width:100%;border-radius:16px;margin-bottom:12px;">
    <div id="body-analysis-box" class="body-analysis" style="display:none;">
      <div style="font-size:13px;letter-spacing:2px;color:#8b7355;margin-bottom:8px;">ANALİZ SONUCU</div>
      <div id="body-analysis-content"></div>
    </div>
  </div>
  <button class="start-btn" id="start-btn" onclick="finishOnboard()" disabled>
    Dolabıma Geç →
  </button>
</div>

<!-- MAIN APP -->
<div id="main-app" style="display:none;">
  <div class="header">
    <div class="header-top">
      <div class="header-title">Dola<span>bım</span></div>
      <img id="user-avatar" class="user-avatar" src="" onclick="showScreen('profile')" style="display:none;">
    </div>
    <div class="tabs">
      <button class="tab active" id="tab-wardrobe" onclick="showScreen('wardrobe')">👗 Dolap (<span id="count">0</span>)</button>
      <button class="tab" id="tab-suggest" onclick="showScreen('suggest')">✨ Kombin</button>
      <button class="tab" id="tab-profile" onclick="showScreen('profile')">👤 Profil</button>
    </div>
  </div>

  <div class="container">
    <!-- WARDROBE SCREEN -->
    <div class="screen active fade-up" id="screen-wardrobe">
      <div class="wardrobe-outer">
        <svg class="wardrobe-svg-bg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 480 260" preserveAspectRatio="xMidYMid slice">
          <defs>
            <linearGradient id="wallGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#252829"/>
              <stop offset="50%" stop-color="#2e3133"/>
              <stop offset="100%" stop-color="#1e2021"/>
            </linearGradient>
            <linearGradient id="floorGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#363a3b"/>
              <stop offset="100%" stop-color="#1a1d1e"/>
            </linearGradient>
            <linearGradient id="railGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="#f2f2f2"/>
              <stop offset="20%" stop-color="#d8d8d8"/>
              <stop offset="50%" stop-color="#b8b8b8"/>
              <stop offset="80%" stop-color="#d4d4d4"/>
              <stop offset="100%" stop-color="#989898"/>
            </linearGradient>
            <linearGradient id="capGrad" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="#c0c0c0"/>
              <stop offset="50%" stop-color="#ebebeb"/>
              <stop offset="100%" stop-color="#a0a0a0"/>
            </linearGradient>
            <linearGradient id="shadowL" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="rgba(0,0,0,0.45)"/>
              <stop offset="100%" stop-color="rgba(0,0,0,0)"/>
            </linearGradient>
            <linearGradient id="shadowR" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="rgba(0,0,0,0)"/>
              <stop offset="100%" stop-color="rgba(0,0,0,0.45)"/>
            </linearGradient>
            <linearGradient id="shadowT" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stop-color="rgba(0,0,0,0.55)"/>
              <stop offset="100%" stop-color="rgba(0,0,0,0)"/>
            </linearGradient>
          </defs>
          <!-- Arka duvar -->
          <rect width="480" height="260" fill="url(#wallGrad)"/>
          <!-- Ince duvar dokusu -->
          <rect x="0" y="65" width="480" height="1" fill="rgba(255,255,255,0.025)"/>
          <rect x="0" y="130" width="480" height="1" fill="rgba(255,255,255,0.025)"/>
          <rect x="0" y="195" width="480" height="1" fill="rgba(255,255,255,0.025)"/>
          <!-- Zemin -->
          <rect x="0" y="232" width="480" height="28" fill="url(#floorGrad)"/>
          <rect x="0" y="231" width="480" height="2" fill="rgba(255,255,255,0.07)"/>
          <!-- Gölgeler -->
          <rect x="0" y="0" width="44" height="260" fill="url(#shadowL)"/>
          <rect x="436" y="0" width="44" height="260" fill="url(#shadowR)"/>
          <rect x="0" y="0" width="480" height="55" fill="url(#shadowT)"/>
          <!-- Metal ray -->
          <rect x="18" y="46" width="444" height="16" rx="8" fill="url(#railGrad)"/>
          <rect x="20" y="47" width="440" height="3" rx="1.5" fill="rgba(255,255,255,0.65)"/>
          <rect x="20" y="60" width="440" height="2" rx="1" fill="rgba(0,0,0,0.25)"/>
          <!-- Ray uç kapaklar -->
          <rect x="10" y="42" width="16" height="24" rx="5" fill="url(#capGrad)"/>
          <rect x="12" y="45" width="5" height="18" rx="2.5" fill="rgba(255,255,255,0.55)"/>
          <rect x="454" y="42" width="16" height="24" rx="5" fill="url(#capGrad)"/>
          <rect x="463" y="45" width="5" height="18" rx="2.5" fill="rgba(255,255,255,0.55)"/>
          <!-- Ray gölgesi -->
          <ellipse cx="240" cy="65" rx="222" ry="5" fill="rgba(0,0,0,0.3)"/>
        </svg>

        <div class="clothes-layer" id="wardrobe-bg">
          <div class="wardrobe-door-overlay" id="wardrobe-door" onclick="openWardrobeDoor()">
            <div style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);text-align:center;pointer-events:none;" id="door-label">
              <div style="font-size:26px;margin-bottom:6px;">🚪</div>
              <div style="font-family:'Cormorant Garamond',serif;font-size:13px;letter-spacing:2px;color:rgba(196,168,130,0.75);text-transform:uppercase;">Dolabı Aç</div>
            </div>
            <div class="door-handle"></div>
          </div>
          <div class="clothes-rail" id="clothes-rail">
            <div class="wardrobe-empty" id="wardrobe-empty">
              Henüz kıyafet eklenmedi<br>
              <span style="font-size:12px;opacity:.6;">Aşağıdan fotoğraf ekle</span>
            </div>
          </div>
        </div>
      </div>

      <div class="upload-zone" onclick="openWardrobeAndUpload()">
        <div class="upload-icon">📷</div>
        <div class="upload-text">Kıyafet fotoğrafı ekle</div>
      </div>
      <input type="file" id="fileInput" accept="image/*" style="display:none" onchange="startCropFlow(this.files)">

      <div id="upload-loading" style="display:none;" class="loading">
        <div class="spinner"></div>
        <div class="loading-text">AI kıyafetini analiz ediyor...</div>
      </div>
    </div>

    <!-- SUGGEST SCREEN -->
    <div class="screen" id="screen-suggest">
      <div id="suggest-form">
        <div style="background:#fff;border-radius:4px;padding:16px 18px;margin-bottom:22px;display:flex;gap:14px;align-items:center;border-left:3px solid var(--gold);box-shadow:0 2px 10px rgba(0,0,0,.06);">
          <div style="font-size:24px;">👗</div>
          <div>
            <div style="font-size:15px;font-weight:500;color:var(--text-dark);" id="suggest-count">0 kıyafet yüklendi</div>
            <div style="font-size:12px;color:var(--text-light);font-style:italic;">AI dolabından en uygun kombinasyonu seçecek</div>
          </div>
        </div>

        <div class="section-label">Bugün Hava</div>
        <div class="weather-opts">
          <button class="opt-btn" onclick="selectOpt(this,'weather','sicak (25C+)')">☀️ Sıcak</button>
          <button class="opt-btn" onclick="selectOpt(this,'weather','ılık (15-25C)')">🌤️ Ilık</button>
          <button class="opt-btn" onclick="selectOpt(this,'weather','serin (5-15C)')">🧥 Serin</button>
          <button class="opt-btn" onclick="selectOpt(this,'weather','soğuk (5C altı)')">❄️ Soğuk</button>
          <button class="opt-btn" onclick="selectOpt(this,'weather','yağmurlu')">🌧️ Yağmurlu</button>
        </div>

        <div class="section-label">Etkinlik</div>
        <div class="event-opts">
          <button class="event-btn" onclick="selectOpt(this,'event','günlük/casual')">👟 Günlük / Casual</button>
          <button class="event-btn" onclick="selectOpt(this,'event','iş toplantısı')">💼 İş Toplantısı</button>
          <button class="event-btn" onclick="selectOpt(this,'event','romantik akşam yemeği')">🌹 Romantik Akşam</button>
          <button class="event-btn" onclick="selectOpt(this,'event','spor/aktif')">🏃 Spor / Aktif</button>
          <button class="event-btn" onclick="selectOpt(this,'event','özel davet/parti')">🎉 Özel Davet</button>
        </div>

        <button class="suggest-btn" id="suggest-btn" onclick="getSuggestion()" disabled>
          ✨ Kombin Öner
        </button>
      </div>

      <div id="suggest-loading" style="display:none;" class="loading">
        <div class="spinner"></div>
        <div class="loading-text">AI kombinini hazırlıyor...</div>
      </div>

      <div id="suggest-result" style="display:none;">
        <div class="result-box">
          <div class="result-line"></div>
          <div class="result-text" id="result-content"></div>
          <div class="feedback-row">
            <button class="feedback-btn like" onclick="saveFeedback('like')">👍 Beğendim</button>
            <button class="feedback-btn dislike" onclick="saveFeedback('dislike')">👎 Beğenmedim</button>
          </div>
        </div>
        <button onclick="resetSuggest()" style="width:100%;background:transparent;border:1px solid var(--gold);border-radius:4px;padding:12px;color:var(--wood-plank);font-family:'Cormorant Garamond',serif;font-size:15px;cursor:pointer;letter-spacing:1px;transition:all .2s;">
          Yeni Kombin Dene
        </button>
      </div>
    </div>

    <!-- PROFILE SCREEN -->
    <div class="screen" id="screen-profile">
      <div class="profile-card">
        <img id="profile-avatar-big" class="profile-avatar" src="">
        <div class="profile-name" id="profile-name">-</div>
        <div class="profile-email" id="profile-email">-</div>
        <div class="profile-stat">
          <div class="stat-item">
            <div class="stat-num" id="stat-clothes">0</div>
            <div class="stat-label">KIYAFEt</div>
          </div>
          <div class="stat-item">
            <div class="stat-num" id="stat-combos">0</div>
            <div class="stat-label">KOMBİN</div>
          </div>
          <div class="stat-item">
            <div class="stat-num" id="stat-likes">0</div>
            <div class="stat-label">BEĞENİ</div>
          </div>
        </div>
      </div>
      <button class="logout-btn" onclick="signOut()">Çıkış Yap</button>
    </div>
  </div>
</div>

<!-- CLOTH DETAIL OVERLAY -->
<div id="cloth-detail-overlay" class="cloth-detail-overlay" style="display:none;" onclick="closeDetail(event)">
  <div class="cloth-detail-sheet">
    <img id="detail-img" class="cloth-detail-img" src="">
    <div id="detail-tags" class="cloth-tags"></div>
    <div id="detail-ai-comment" style="background:#f5ede3;border-radius:12px;padding:14px;margin-bottom:16px;font-style:italic;color:#4a3728;font-size:14px;line-height:1.7;"></div>
    <button class="remove-cloth-btn" onclick="removeCloth()">🗑️ Bu Kıyafeti Sil</button>
  </div>
</div>

<script type="module">
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut as fbSignOut, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-auth.js";
import { getFirestore, doc, getDoc, setDoc, updateDoc, arrayUnion, increment } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-firestore.js";

const firebaseConfig = {
  apiKey: "AIzaSyBeE62ZcocMTDNIfeKFyfDDNr_evWon_9w",
  authDomain: "ai-stylist-94c04.firebaseapp.com",
  projectId: "ai-stylist-94c04",
  storageBucket: "ai-stylist-94c04.firebasestorage.app",
  messagingSenderId: "360910240515",
  appId: "1:360910240515:web:6530b5d571fe1280bb8736"
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

let currentUser = null;
let clothes = [];
let selectedWeather = '';
let selectedEvent = '';
let currentDetailIndex = -1;
let lastSuggestion = '';

const uploadComments = [
  ["✨", "Vay be! Bu renk sana çok yakışacak!"],
  ["😍", "Harika bir seçim! Çok şık duruyor."],
  ["👏", "Bu kıyafet dolabına güzellik katıyor!"],
  ["🔥", "Ateş gibi! Bu kombinlerde çok iyi iş çıkarır."],
  ["💫", "Zariflik bu işte! Çok beğendim."],
  ["🌟", "Mükemmel! AI gözüm bunu seviyor."],
];

function showToast(emoji, msg) {
  const old = document.querySelector('.ai-toast');
  if (old) old.remove();
  const t = document.createElement('div');
  t.className = 'ai-toast';
  t.innerHTML = `<span class="ai-toast-emoji">${emoji}</span>${msg}`;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function resizeImage(dataUrl, maxPx) {
  return new Promise(resolve => {
    const img = new Image();
    img.onload = () => {
      let w = img.width, h = img.height;
      if (w > maxPx || h > maxPx) {
        if (w > h) { h = Math.round(h * maxPx / w); w = maxPx; }
        else { w = Math.round(w * maxPx / h); h = maxPx; }
      }
      const canvas = document.createElement('canvas');
      canvas.width = w; canvas.height = h;
      canvas.getContext('2d').drawImage(img, 0, 0, w, h);
      resolve(canvas.toDataURL('image/jpeg', 0.8).split(',')[1]);
    };
    img.src = dataUrl;
  });
}

// ── AUTH ──
window.signInWithGoogle = async () => {
  const provider = new GoogleAuthProvider();
  try { await signInWithPopup(auth, provider); }
  catch(e) { alert('Giriş başarısız: ' + e.message); }
};

window.signOut = async () => { await fbSignOut(auth); };

onAuthStateChanged(auth, async (user) => {
  if (user) {
    currentUser = user;
    document.getElementById('auth-screen').style.display = 'none';
    if (user.photoURL) {
      document.getElementById('user-avatar').src = user.photoURL;
      document.getElementById('user-avatar').style.display = 'block';
      document.getElementById('profile-avatar-big').src = user.photoURL;
    }
    document.getElementById('profile-name').textContent = user.displayName || 'Kullanıcı';
    document.getElementById('profile-email').textContent = user.email;
    const userDoc = await getDoc(doc(db, 'users', user.uid));
    if (!userDoc.exists() || !userDoc.data().onboarded) {
      document.getElementById('onboard-screen').style.display = 'flex';
    } else {
      document.getElementById('main-app').style.display = 'block';
      await loadClothes();
    }
  } else {
    currentUser = null;
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('onboard-screen').style.display = 'none';
    document.getElementById('main-app').style.display = 'none';
  }
});

// ── ONBOARD ──
window.handleBodyPhoto = async (file) => {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async (e) => {
    document.getElementById('body-preview-img').src = e.target.result;
    document.getElementById('body-preview-wrap').style.display = 'block';
    const base64 = e.target.result.split(',')[1];
    try {
      const resp = await fetch('/analyze-body', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({image: base64})
      });
      const data = await resp.json();
      if (data.analysis) {
        document.getElementById('body-analysis-box').style.display = 'block';
        document.getElementById('body-analysis-content').innerHTML = data.analysis;
        window._bodyAnalysis = data.analysis;
      }
    } catch(e) {}
    document.getElementById('start-btn').disabled = false;
  };
  reader.readAsDataURL(file);
};

window.finishOnboard = async () => {
  await setDoc(doc(db, 'users', currentUser.uid), {
    onboarded: true,
    displayName: currentUser.displayName,
    email: currentUser.email,
    bodyAnalysis: window._bodyAnalysis || '',
    comboCount: 0, likeCount: 0,
    createdAt: new Date().toISOString()
  }, {merge: true});
  document.getElementById('onboard-screen').style.display = 'none';
  document.getElementById('main-app').style.display = 'block';
  await loadClothes();
  showToast('👗', 'Dolabına hoş geldin! Kıyafetlerini eklemeye başla.');
};

// ── WARDROBE DOOR ──
let wardrobeIsOpen = false;

window.openWardrobeDoor = function(instant) {
  const door = document.getElementById('wardrobe-door');
  if (!door || wardrobeIsOpen) return;
  wardrobeIsOpen = true;
  if (instant) {
    door.style.transition = 'none';
    door.style.display = 'none';
  } else {
    door.classList.add('open');
    setTimeout(() => { door.style.display = 'none'; }, 700);
  }
};

window.openWardrobeAndUpload = function() {
  openWardrobeDoor();
  setTimeout(() => {
    document.getElementById('fileInput').click();
  }, wardrobeIsOpen ? 0 : 350);
};

// ── WARDROBE ──
async function loadClothes() {
  const userDoc = await getDoc(doc(db, 'users', currentUser.uid));
  clothes = userDoc.data()?.clothes || [];
  renderClothes();
  updateCounts();
  document.getElementById('stat-clothes').textContent = clothes.length;
  document.getElementById('stat-combos').textContent = userDoc.data()?.comboCount || 0;
  document.getElementById('stat-likes').textContent = userDoc.data()?.likeCount || 0;
  // Kıyafet varsa kapıyı anında (animasyonsuz) aç
  if (clothes.length > 0) {
    openWardrobeDoor(true);
  }
}

// SVG fallback (rembg yoksa veya hanger_image gelmediyse)
function getClothSVG(category, color, label) {
  const c = color || '#888';
  const darker = shadeColor(c, -30);
  const lighter = shadeColor(c, 30);
  if (category === 'alt' || label?.includes('pantolon') || label?.includes('jean') || label?.includes('şort') || label?.includes('etek')) {
    if (label?.includes('etek')) {
      return `<svg viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg">
        <rect x="28" y="0" width="24" height="8" rx="3" fill="${darker}"/>
        <polygon points="20,8 60,8 72,95 8,95" fill="${c}"/>
        <line x1="40" y1="8" x2="40" y2="95" stroke="${darker}" stroke-width="1" opacity="0.3"/>
        <rect x="18" y="8" width="44" height="4" rx="2" fill="${darker}"/>
      </svg>`;
    }
    return `<svg viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="28" y="0" width="24" height="6" rx="3" fill="${darker}"/>
      <rect x="18" y="6" width="44" height="5" rx="2" fill="${darker}"/>
      <path d="M18,11 L8,95 L38,95 L40,50 L42,95 L72,95 L62,11 Z" fill="${c}"/>
      <line x1="40" y1="11" x2="38" y2="95" stroke="${darker}" stroke-width="1.5" opacity="0.4"/>
    </svg>`;
  }
  if (category === 'ayak' || label?.includes('ayakkabı') || label?.includes('bot') || label?.includes('sneaker')) {
    return `<svg viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="28" y="0" width="24" height="6" rx="3" fill="${darker}"/>
      <ellipse cx="40" cy="65" rx="30" ry="18" fill="${c}"/>
      <ellipse cx="40" cy="58" rx="22" ry="14" fill="${lighter}"/>
      <rect x="10" y="75" width="60" height="12" rx="6" fill="${darker}"/>
      <ellipse cx="55" cy="52" rx="12" ry="8" fill="${lighter}" opacity="0.6"/>
    </svg>`;
  }
  if (label?.includes('çorap') || label?.includes('tayt')) {
    return `<svg viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="28" y="0" width="24" height="6" rx="3" fill="${darker}"/>
      <rect x="25" y="6" width="30" height="55" rx="5" fill="${c}"/>
      <ellipse cx="40" cy="65" rx="20" ry="10" fill="${c}"/>
      <rect x="20" y="70" width="40" height="20" rx="8" fill="${darker}"/>
    </svg>`;
  }
  if (label?.includes('ceket') || label?.includes('mont') || label?.includes('kaban')) {
    return `<svg viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg">
      <rect x="33" y="0" width="14" height="6" rx="3" fill="${darker}"/>
      <path d="M40,6 L55,18 L68,14 L72,30 L60,32 L60,95 L20,95 L20,32 L8,30 L12,14 L25,18 Z" fill="${c}"/>
      <path d="M40,6 L40,95" stroke="${darker}" stroke-width="1.5" opacity="0.3"/>
    </svg>`;
  }
  return `<svg viewBox="0 0 80 100" xmlns="http://www.w3.org/2000/svg">
    <rect x="33" y="0" width="14" height="6" rx="3" fill="${darker}"/>
    <path d="M40,6 C37,6 34,8 32,12 L18,22 L12,14 L5,28 L20,34 L20,95 L60,95 L60,34 L75,28 L68,14 L62,22 L48,12 C46,8 43,6 40,6 Z" fill="${c}"/>
    <path d="M32,12 Q40,20 48,12" fill="none" stroke="${darker}" stroke-width="1.5"/>
  </svg>`;
}

function shadeColor(color, percent) {
  try {
    let R = parseInt(color.substring(1,3),16);
    let G = parseInt(color.substring(3,5),16);
    let B = parseInt(color.substring(5,7),16);
    R = Math.min(255, Math.max(0, R+percent));
    G = Math.min(255, Math.max(0, G+percent));
    B = Math.min(255, Math.max(0, B+percent));
    return '#'+((1<<24)+(R<<16)+(G<<8)+B).toString(16).slice(1);
  } catch(e) { return color; }
}

function tagToColor(tags) {
  const colorMap = {
    'kırmızı':'#e53935','kirmizi':'#e53935','red':'#e53935',
    'mavi':'#1e88e5','blue':'#1e88e5','lacivert':'#1a237e','navy':'#1a237e',
    'yeşil':'#43a047','yesil':'#43a047','green':'#43a047','haki':'#827717',
    'siyah':'#212121','black':'#212121',
    'beyaz':'#f5f5f5','white':'#f5f5f5',
    'gri':'#757575','grey':'#757575','gray':'#757575',
    'bej':'#d4b896','bege':'#d4b896','krem':'#f0e6d3',
    'sarı':'#fdd835','sari':'#fdd835','yellow':'#fdd835',
    'turuncu':'#fb8c00','orange':'#fb8c00',
    'mor':'#8e24aa','purple':'#8e24aa','lila':'#ab47bc',
    'pembe':'#e91e8c','pink':'#e91e8c','pudra':'#f8bbd0',
    'kahve':'#6d4c41','brown':'#6d4c41','camel':'#c19a6b',
    'bordo':'#880e4f','burgundy':'#880e4f',
  };
  for (const tag of (tags||[])) {
    const lower = tag.toLowerCase();
    for (const [key, val] of Object.entries(colorMap)) {
      if (lower.includes(key)) return val;
    }
  }
  return '#8b7355';
}

// Gerçek tel askı SVG — krom metal görünüm
function getWireHangerSVG() {
  return `<svg class="hanger-wire" viewBox="0 0 72 52" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="wg" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#f0f0f0"/>
        <stop offset="40%" stop-color="#c0c0c0"/>
        <stop offset="100%" stop-color="#888"/>
      </linearGradient>
      <linearGradient id="wh" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#d8d8d8"/>
        <stop offset="50%" stop-color="#f8f8f8"/>
        <stop offset="100%" stop-color="#b0b0b0"/>
      </linearGradient>
    </defs>
    <!-- Kanca üst kısmı (raya bağlı) -->
    <path d="M36 2 Q36 0 38 0 Q42 0 42 4 Q42 8 38 10 L36 12" 
          fill="none" stroke="url(#wg)" stroke-width="2.5" stroke-linecap="round"/>
    <!-- Kanca orta -->
    <path d="M36 12 Q34 16 30 18" 
          fill="none" stroke="url(#wg)" stroke-width="2.5" stroke-linecap="round"/>
    <!-- Sol kol -->
    <path d="M30 18 Q10 22 4 28 Q2 30 4 32" 
          fill="none" stroke="url(#wh)" stroke-width="2" stroke-linecap="round"/>
    <!-- Sağ kol -->
    <path d="M30 18 Q52 22 68 28 Q70 30 68 32" 
          fill="none" stroke="url(#wh)" stroke-width="2" stroke-linecap="round"/>
    <!-- Alt yatay bar -->
    <path d="M4 32 Q36 36 68 32" 
          fill="none" stroke="url(#wh)" stroke-width="2.5" stroke-linecap="round"/>
    <!-- Parlama efekti -->
    <path d="M10 29 Q36 33 62 29" 
          fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1" stroke-linecap="round"/>
  </svg>`;
}

function renderClothes() {
  const rail = document.getElementById('clothes-rail');
  const empty = document.getElementById('wardrobe-empty');
  if (clothes.length === 0) {
    rail.innerHTML = '';
    rail.appendChild(empty);
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  Array.from(rail.children).forEach(c => { if (c.id !== 'wardrobe-empty') c.remove(); });

  clothes.forEach((c, i) => {
    const item = document.createElement('div');
    item.className = 'hanger-item';
    item.onclick = () => showClothDetail(i);

    const hangerSVG = getWireHangerSVG();

    if (c.hanger_image) {
      // rembg ile üretilmiş arka planı silinmiş görsel
      item.innerHTML = `
        ${hangerSVG}
        <img src="data:image/png;base64,${c.hanger_image}" class="real-hanger" alt="${c.label}">
        <div class="hanger-label">${c.label}</div>
      `;
    } else if (c.cloth_svg) {
      // Claude'un ürettiği gerçekçi SVG
      item.innerHTML = `
        ${hangerSVG}
        <div class="hanger-svg ai-generated-svg">${c.cloth_svg}</div>
        <div class="hanger-label">${c.label}</div>
      `;
    } else if (c.imageData) {
      // Hiçbir şey yoksa gerçek fotoğrafı direkt kullan
      item.innerHTML = `
        ${hangerSVG}
        <img src="${c.imageData}" class="real-photo-hanger" alt="${c.label}">
        <div class="hanger-label">${c.label}</div>
      `;
    } else {
      const color = tagToColor(c.tags);
      const svg = getClothSVG(c.category, color, c.label?.toLowerCase());
      item.innerHTML = `
        ${hangerSVG}
        <div class="hanger-svg">${svg}</div>
        <div class="hanger-label">${c.label}</div>
      `;
    }
    rail.appendChild(item);
  });
}

function updateCounts() {
  document.getElementById('count').textContent = clothes.length;
  document.getElementById('suggest-count').textContent = `${clothes.length} kıyafet yüklendi`;
  document.getElementById('stat-clothes').textContent = clothes.length;
}

// ── CROPPER ──
let cropperInstance = null;
let cropperQueue = [];   // birden fazla dosya seçilince sırayla işle
let cropperQueueIndex = 0;

window.startCropFlow = function(files) {
  if (!files || files.length === 0) return;
  // fileInput'u sıfırla ki aynı dosya tekrar seçilebilsin
  document.getElementById('fileInput').value = '';
  cropperQueue = Array.from(files);
  cropperQueueIndex = 0;
  showCropperForIndex(0);
};

function showCropperForIndex(idx) {
  if (idx >= cropperQueue.length) return;
  const file = cropperQueue[idx];
  const reader = new FileReader();
  reader.onload = (e) => {
    const modal = document.getElementById('cropper-modal');
    const img   = document.getElementById('cropper-img');
    const counter = document.getElementById('cropper-counter');

    // Sayaç (birden fazla fotoğrafta)
    if (cropperQueue.length > 1) {
      counter.textContent = `${idx + 1} / ${cropperQueue.length}`;
    } else {
      counter.textContent = '';
    }

    // Eski cropper'ı temizle
    if (cropperInstance) { cropperInstance.destroy(); cropperInstance = null; }

    img.src = e.target.result;
    modal.style.display = 'flex';

    // Kısa gecikme — img yüklenmesini bekle
    setTimeout(() => {
      cropperInstance = new Cropper(img, {
        aspectRatio: NaN,        // serbest oran
        viewMode: 1,             // görüntü kutu dışına çıkamasın
        dragMode: 'move',
        autoCropArea: 0.85,      // başlangıçta %85 seçili
        restore: false,
        guides: true,
        center: true,
        highlight: false,
        cropBoxMovable: true,
        cropBoxResizable: true,
        toggleDragModeOnDblclick: false,
        background: false,
      });
    }, 150);
  };
  reader.readAsDataURL(file);
}

window.cropperConfirm = async function() {
  if (!cropperInstance) return;

  // Kırpılmış canvas al — max 800px
  const canvas = cropperInstance.getCroppedCanvas({ maxWidth: 800, maxHeight: 800 });
  const croppedDataUrl = canvas.toDataURL('image/jpeg', 0.85);

  // Modal'ı kapat
  document.getElementById('cropper-modal').style.display = 'none';
  if (cropperInstance) { cropperInstance.destroy(); cropperInstance = null; }

  // Analiz et
  await analyzeAndAddCloth(croppedDataUrl);

  // Sonraki fotoğraf varsa devam et
  cropperQueueIndex++;
  if (cropperQueueIndex < cropperQueue.length) {
    showCropperForIndex(cropperQueueIndex);
  }
};

window.cropperCancel = function() {
  document.getElementById('cropper-modal').style.display = 'none';
  if (cropperInstance) { cropperInstance.destroy(); cropperInstance = null; }
  // Kuyruğu temizle
  cropperQueue = [];
  cropperQueueIndex = 0;
};

// ── UPLOAD ──
// Tek bir kırpılmış görsel al, analiz et, dolaba ekle
async function analyzeAndAddCloth(croppedDataUrl) {
  document.getElementById('upload-loading').style.display = 'block';
  try {
    const base64 = await resizeImage(croppedDataUrl, 800);
    const resp = await fetch('/analyze-cloth', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({image: base64})
    });
    const data = await resp.json();

    const cloth = {
      id: Date.now() + Math.random(),
      imageData: croppedDataUrl,
      hanger_image: data.hanger_image || null,
      cloth_svg: data.cloth_svg || null,
      label: data.label || 'Kıyafet',
      category: data.category || 'üst',
      tags: data.tags || [],
      aiComment: data.comment || '',
      addedAt: new Date().toISOString()
    };

    clothes.push(cloth);

    if (!wardrobeIsOpen) openWardrobeDoor();
    renderClothes();
    updateCounts();

    setTimeout(() => {
      const items = document.querySelectorAll('.hanger-item');
      const lastItem = items[items.length - 1];
      if (lastItem) {
        lastItem.classList.add('cloth-fly-in');
        setTimeout(() => lastItem.classList.add('hang-swing'), 700);
      }
    }, 100);

    try {
      const clothMeta = {
        id: cloth.id, label: cloth.label,
        tags: cloth.tags, aiComment: cloth.aiComment,
        category: cloth.category, addedAt: cloth.addedAt
      };
      await setDoc(doc(db, 'users', currentUser.uid),
        {clothesMeta: arrayUnion(clothMeta)}, {merge: true});
    } catch(fsErr) { console.error("Firestore meta hata:", fsErr.message); }

    const pick = uploadComments[Math.floor(Math.random() * uploadComments.length)];
    setTimeout(() => showToast(pick[0], data.comment || pick[1]), 500);

  } catch(err) { console.error(err); }
  document.getElementById('upload-loading').style.display = 'none';
}

window.handleClothes = async (files) => {
  // Artık kullanılmıyor — startCropFlow üzerinden geliyor
  // Ama eski referanslar için burada bırakıyoruz
  startCropFlow(files);
};


// ── DETAIL ──
window.showClothDetail = (index) => {
  currentDetailIndex = index;
  const c = clothes[index];
  // Detay ekranında orijinal görsel göster
  document.getElementById('detail-img').src = c.imageData;
  document.getElementById('detail-tags').innerHTML = (c.tags||[]).map(t =>
    `<span class="cloth-tag-chip">${t}</span>`).join('');
  document.getElementById('detail-ai-comment').textContent = c.aiComment || 'Bu kıyafet dolabında çok iyi duruyor!';
  document.getElementById('cloth-detail-overlay').style.display = 'flex';
};

window.closeDetail = (e) => {
  if (e.target === document.getElementById('cloth-detail-overlay'))
    document.getElementById('cloth-detail-overlay').style.display = 'none';
};

window.removeCloth = async () => {
  if (currentDetailIndex < 0) return;
  clothes.splice(currentDetailIndex, 1);
  await setDoc(doc(db, 'users', currentUser.uid), {clothes}, {merge: true});
  renderClothes(); updateCounts();
  document.getElementById('cloth-detail-overlay').style.display = 'none';
  showToast('🗑️', 'Kıyafet dolabından kaldırıldı.');
};

// ── NAVIGATION ──
window.showScreen = (name) => {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('screen-' + name)?.classList.add('active');
  document.getElementById('tab-' + name)?.classList.add('active');
};

window.selectOpt = (btn, type, val) => {
  btn.parentElement.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  if (type === 'weather') selectedWeather = val;
  if (type === 'event') selectedEvent = val;
  checkSuggestReady();
};

function checkSuggestReady() {
  document.getElementById('suggest-btn').disabled = !(selectedWeather && selectedEvent && clothes.length > 0);
}

// ── SUGGEST ──
window.getSuggestion = async () => {
  document.getElementById('suggest-form').style.display = 'none';
  document.getElementById('suggest-loading').style.display = 'block';
  document.getElementById('suggest-result').style.display = 'none';

  const userDoc = await getDoc(doc(db, 'users', currentUser.uid));
  const userData = userDoc.data();
  const bodyAnalysis = userData?.bodyAnalysis || '';
  const likeHistory = userData?.likeHistory || [];

  const clothesList = clothes.map((c, i) =>
    `${i+1}. ${c.label} (Etiketler: ${(c.tags||[]).join(', ')})`).join('\n');

  try {
    const resp = await fetch('/suggest', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        messages: [{
          role: 'user',
          content: `Sen bir kişisel stil danışmanısın. Kullanıcının dolabından kombin öner.

KULLANICI VÜCUT ANALİZİ:
${bodyAnalysis || 'Bilgi yok'}

KIYAFETLERİ:
${clothesList}

HAVA DURUMU: ${selectedWeather}
ETKİNLİK: ${selectedEvent}

BEĞENME GEÇMİŞİ: ${likeHistory.slice(-5).join(', ') || 'Henüz yok'}

Türkçe olarak:
1. Hangi kıyafetlerden kombin yap (numara ile belirt)
2. Neden bu kombinasyonu seçtin
3. Bu kombinle nasıl görüneceğini anlat (vücut analizine göre)
4. Stil ipuçları

Samimi, sıcak ve heyecanlı bir dil kullan. Kısa ve net ol.`
        }],
        model: 'claude-sonnet-4-20250514',
        max_tokens: 1000
      })
    });
    const data = await resp.json();
    const text = data.content?.[0]?.text || 'Kombin üretilemedi.';
    lastSuggestion = text;
    document.getElementById('result-content').innerHTML = text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
    document.getElementById('suggest-loading').style.display = 'none';
    document.getElementById('suggest-result').style.display = 'block';
    await updateDoc(doc(db, 'users', currentUser.uid), {comboCount: increment(1)});
    document.getElementById('stat-combos').textContent = (userData.comboCount || 0) + 1;
  } catch(e) {
    document.getElementById('suggest-loading').style.display = 'none';
    document.getElementById('suggest-form').style.display = 'block';
    alert('Hata: ' + e.message);
  }
};

window.saveFeedback = async (type) => {
  document.querySelectorAll('.feedback-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  if (type === 'like') {
    await updateDoc(doc(db, 'users', currentUser.uid), {
      likeCount: increment(1),
      likeHistory: arrayUnion(lastSuggestion.substring(0, 100))
    });
    showToast('💖', 'Harika! Bu tarzı aklımda tutacağım.');
    const el = document.getElementById('stat-likes');
    el.textContent = parseInt(el.textContent) + 1;
  } else {
    showToast('🤔', 'Anlıyorum! Bir daha denersek daha iyi olacak.');
  }
};

window.resetSuggest = () => {
  document.getElementById('suggest-form').style.display = 'block';
  document.getElementById('suggest-result').style.display = 'none';
  selectedWeather = ''; selectedEvent = '';
  document.querySelectorAll('.opt-btn, .event-btn').forEach(b => b.classList.remove('selected'));
  checkSuggestReady();
};
</script>
</body>
</html>
'''

# ──────────────────────────────────────────────
# HTTP SERVER
# ──────────────────────────────────────────────
def recv_exact(conn, length):
    data = b""
    while len(data) < length:
        chunk = conn.recv(min(65536, length - len(data)))
        if not chunk:
            break
        data += chunk
    return data

def parse_request(conn):
    header_data = b""
    while b"\r\n\r\n" not in header_data:
        chunk = conn.recv(4096)
        if not chunk:
            return None, None, None, None
        header_data += chunk
    header_part, body_start = header_data.split(b"\r\n\r\n", 1)
    lines = header_part.decode("utf-8", errors="replace").split("\r\n")
    parts = lines[0].split(" ")
    if len(parts) < 2:
        return None, None, None, None
    method, path = parts[0], parts[1]
    headers = {}
    for line in lines[1:]:
        if ":" in line:
            key, val = line.split(":", 1)
            headers[key.strip().lower()] = val.strip()
    content_length = int(headers.get("content-length", 0))
    body = body_start
    remaining = content_length - len(body)
    if remaining > 0:
        body += recv_exact(conn, remaining)
    return method, path, headers, body

def send_response(conn, status, content_type, body):
    status_texts = {200:"OK", 400:"Bad Request", 404:"Not Found", 500:"Server Error"}
    status_text = status_texts.get(status, "Error")
    if isinstance(body, str):
        body = body.encode("utf-8")
    header = (
        f"HTTP/1.1 {status} {status_text}\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(body)}\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Connection: close\r\n\r\n"
    )
    try:
        conn.sendall(header.encode("utf-8") + body)
    except Exception:
        pass

def call_anthropic(payload):
    print("[DEBUG] Anthropic'e gonderiliyor, model:", payload.get("model","?"))
    data = json.dumps(payload).encode()
    print("[DEBUG] Payload boyut:", len(data)//1024, "KB")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = resp.read().decode("utf-8", errors="replace")
            print("[DEBUG] Anthropic cevap OK, boyut:", len(result)//1024, "KB")
            return 200, result
    except urllib.error.HTTPError as e:
        result = e.read().decode("utf-8", errors="replace")
        print("[HATA] Anthropic HTTP", e.code, ":", result[:300])
        return e.code, result
    except urllib.error.URLError as e:
        print("[HATA] Anthropic URL:", str(e.reason))
        return 502, json.dumps({"error": str(e.reason)})
    except Exception as e:
        print("[HATA] Anthropic genel:", str(e))
        return 500, json.dumps({"error": str(e)})

def generate_cloth_svg(label, category, tags, image_b64):
    """Claude'a kıyafetin görselini + analizini vererek gerçekçi SVG ürettir."""
    color_tags = ", ".join(tags[:5]) if tags else "belirsiz renk"
    prompt = f"""Sana bir kıyafetin fotoğrafını ve analizini veriyorum.
Bu kıyafeti temsil eden, bir mağaza kataloğuna yakışan GERÇEKÇİ bir SVG çiz.

Kıyafet bilgisi:
- İsim: {label}
- Kategori: {category}
- Özellikler: {color_tags}

SVG kuralları (KESİNLİKLE UYULACAK):
1. viewBox="0 0 120 150" kullan
2. SADECE SVG kodu yaz — başka hiçbir şey yazma, açıklama yok
3. Kıyafeti GERÇEK görünümlü çiz: katmanlar, gölgeler, dikiş detayları, düğmeler, yaka, kol gibi detaylar
4. Rengi fotoğraftan al — ana rengi doğru kullan
5. Kıyafet viewBox'ı dolduracak şekilde büyük olsun
6. Kumaş dokusunu lineerGradient ile simüle et
7. Detay ekle: yaka çizgisi, kol kıvrımları, düğmeler varsa, cep varsa, dikiş çizgileri
8. Alt kısmında hafif gölge bırak

Sadece <svg>...</svg> döndür."""

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 1200,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}
                },
                {"type": "text", "text": prompt}
            ]
        }]
    }
    status, result = call_anthropic(payload)
    if status != 200:
        return None
    try:
        resp_data = json.loads(result)
        svg_text = resp_data["content"][0]["text"].strip()
        # SVG'yi temizle
        if "<svg" in svg_text:
            start = svg_text.index("<svg")
            end = svg_text.rindex("</svg>") + 6
            svg_text = svg_text[start:end]
        return svg_text
    except Exception as e:
        print("[HATA] SVG parse:", e)
        return None


def handle_analyze_cloth(body):
    print("[DEBUG] analyze-cloth istegi alindi, boyut:", len(body)//1024, "KB")
    try:
        data = json.loads(body)
        image_b64 = data.get("image", "")
        print("[DEBUG] Image b64 boyut:", len(image_b64)//1024, "KB")
    except Exception as e:
        print("[HATA] JSON parse:", e)
        return 400, json.dumps({"error": "Invalid JSON"})

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 400,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}
                },
                {
                    "type": "text",
                    "text": """Bu kıyafeti çok dikkatli analiz et.

ÖNEMLİ: Önce kıyafetin tam olarak ne olduğunu belirle:
- Üst giyim: tişört, gömlek, bluz, kazak, hırka, ceket, mont, yelek
- Alt giyim: pantolon, jean, etek, şort, tayt, eşofman altı
- Ayak giyimi: ayakkabı, bot, sneaker, sandalet, terlik, ÇORAP
- Aksesuar: kemer, çanta, şapka, eşarp, kravat
- İç giyim: pijama, iç çamaşırı

Eğer görsel uzun ve ince ise ÇORAP veya TAYT olabilir dikkatli bak.

JSON formatında döndür (sadece JSON, başka hiçbir şey yazma):
{
  "label": "Kısa ve net isim (örn: Kırmızı Gömlek, Siyah Pantolon, Beyaz Çorap)",
  "category": "üst/alt/ayak/aksesuar/iç",
  "tags": ["renk", "tür", "materyal", "stil", "mevsim"],
  "comment": "Samimi ve heyecanlı 1-2 cümle yorum (Türkçe)"
}"""
                }
            ]
        }]
    }
    status, result = call_anthropic(payload)
    if status == 200:
        try:
            resp_data = json.loads(result)
            print("[DEBUG] Anthropic ham cevap:", result[:300])
            text = resp_data["content"][0]["text"].strip()
            if "```" in text:
                parts = text.split("```")
                for p in parts:
                    p = p.strip()
                    if p.startswith("json"): p = p[4:].strip()
                    if p.startswith("{"):
                        text = p
                        break
            parsed = json.loads(text.strip())

            # ── Askı görseli oluştur ──
            category = parsed.get("category", "üst")
            hanger_img = process_cloth_with_hanger(image_b64, category)
            if hanger_img:
                parsed["hanger_image"] = hanger_img
                print("[INFO] Hanger görsel oluşturuldu, boyut:", len(hanger_img)//1024, "KB")
            else:
                # rembg yok — Claude ile gerçekçi SVG üret
                print("[INFO] rembg yok, Claude SVG üretiyor...")
                cloth_svg = generate_cloth_svg(
                    parsed.get("label", "Kıyafet"),
                    category,
                    parsed.get("tags", []),
                    image_b64
                )
                if cloth_svg:
                    parsed["cloth_svg"] = cloth_svg
                    print("[INFO] Claude SVG üretildi, boyut:", len(cloth_svg), "karakter")
                else:
                    print("[INFO] SVG üretilemedi, fallback SVG kullanılacak.")

            return 200, json.dumps(parsed)
        except Exception as e:
            print("[HATA] analyze parse:", e, "| result:", result[:200])
            return 200, json.dumps({"label": "Kıyafet", "tags": ["kıyafet"], "comment": "Harika bir kıyafet!"})
    print("[HATA] analyze status:", status, result[:200])
    return status, result

def handle_analyze_body(body):
    try:
        data = json.loads(body)
        image_b64 = data.get("image", "")
    except Exception:
        return 400, json.dumps({"error": "Invalid JSON"})

    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 500,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/jpeg", "data": image_b64}
                },
                {
                    "type": "text",
                    "text": """Bu kişinin vücut tipini analiz et. Kombin önerilerinde kullanılacak.
HTML formatında, her özellik için <div class="analysis-item"><span class="analysis-label">Özellik</span><span class="analysis-value">Değer</span></div> şeklinde döndür:
- Vücut tipi (elma, armut, kum saati, dikdörtgen vb)
- Önerilen kıyafet stilleri
- Kaçınılması gerekenler
Sadece HTML döndür."""
                }
            ]
        }]
    }
    status, result = call_anthropic(payload)
    if status == 200:
        try:
            resp_data = json.loads(result)
            text = resp_data["content"][0]["text"]
            return 200, json.dumps({"analysis": text})
        except Exception:
            return 200, json.dumps({"analysis": ""})
    return status, result

def handle_suggest(body):
    try:
        data = json.loads(body)
    except Exception:
        return 400, json.dumps({"error": "Invalid JSON"})
    sanitized = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": min(int(data.get("max_tokens", 1000)), MAX_TOKENS_LIMIT),
        "messages": data.get("messages", []),
    }
    return call_anthropic(sanitized)

def handle_client(conn, addr):
    try:
        method, path, headers, body = parse_request(conn)
        if method is None:
            conn.close()
            return
        if method == "OPTIONS":
            send_response(conn, 200, "text/plain", "")
        elif method == "GET" and (path == "/" or path == "/index.html"):
            send_response(conn, 200, "text/html; charset=utf-8", INDEX_HTML)
        elif method == "GET" and path == "/health":
            send_response(conn, 200, "application/json", '{"status":"ok"}')
        elif method == "POST" and path == "/suggest":
            status, result = handle_suggest(body)
            send_response(conn, status, "application/json", result)
        elif method == "POST" and path == "/analyze-cloth":
            status, result = handle_analyze_cloth(body)
            send_response(conn, status, "application/json", result)
        elif method == "POST" and path == "/analyze-body":
            status, result = handle_analyze_body(body)
            send_response(conn, status, "application/json", result)
        else:
            send_response(conn, 404, "text/plain", "Not Found")
    except Exception as e:
        print("[HATA] " + str(e))
        try:
            send_response(conn, 500, "application/json", '{"error":"Sunucu hatasi"}')
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

if __name__ == "__main__":
    if not API_KEY:
        print("HATA: ANTHROPIC_API_KEY set edilmemis!")
        sys.exit(1)

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", PORT))
    server.listen(10)
    print("AI Stylist V3 baslatildi - http://localhost:" + str(PORT))
    print("hanger.png konumu:", HANGER_PATH)
    print("rembg durumu:", "AKTIF" if REMBG_AVAILABLE else "PASIF (SVG fallback)")

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\nSunucu durduruluyor...")
        server.close()
