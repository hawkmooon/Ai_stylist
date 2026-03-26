import socket
import json
import urllib.request
import urllib.error
import os
import sys
import time
import threading

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PORT = int(os.environ.get("PORT", 8765))
ALLOWED_MODELS = {"claude-sonnet-4-5", "claude-haiku-4-5-20251001", "claude-sonnet-4-5-20241022"}
MAX_TOKENS_LIMIT = 2000

RATE_LIMIT = 10
rate_store = {}
rate_lock = threading.Lock()

INDEX_HTML = r'''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Stylist - Dolabim</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,400&family=Playfair+Display:wght@400;600&display=swap" rel="stylesheet">
<style>
  *{box-sizing:border-box;margin:0;padding:0;}
  body{background:#faf7f4;font-family:'Cormorant Garamond',Georgia,serif;color:#2c2420;min-height:100vh;}
  ::-webkit-scrollbar{width:4px;}
  ::-webkit-scrollbar-thumb{background:#c4a882;border-radius:2px;}
  @keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
  @keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}
  @keyframes spin{to{transform:rotate(360deg)}}
  .fade-up{animation:fadeUp .45s ease forwards;}
  .pulse{animation:pulse 1.6s ease-in-out infinite;}

  .header{background:#2c2420;padding:24px 20px 18px;text-align:center;position:sticky;top:0;z-index:100;}
  .header-sub{font-size:10px;letter-spacing:4px;color:#c4a882;margin-bottom:4px;text-transform:uppercase;}
  .header-title{font-family:'Playfair Display',serif;font-size:26px;font-weight:400;color:#faf7f4;letter-spacing:1px;}
  .tabs{display:flex;justify-content:center;margin-top:16px;}
  .tab{border:1px solid #c4a882;padding:8px 22px;font-size:13px;letter-spacing:1px;cursor:pointer;font-family:'Cormorant Garamond',serif;transition:all .2s;background:transparent;color:#c4a882;}
  .tab.active{background:#c4a882;color:#2c2420;}
  .tab:first-child{border-radius:20px 0 0 20px;}
  .tab:last-child{border-radius:0 20px 20px 0;}

  .container{max-width:480px;margin:0 auto;padding:24px 16px 80px;}
  .screen{display:none;}
  .screen.active{display:block;}
  .subtitle{text-align:center;color:#8b7355;font-size:15px;margin-bottom:20px;font-style:italic;}

  .upload-zone{border:2px dashed #d4c4b4;border-radius:18px;padding:36px 20px;text-align:center;cursor:pointer;background:#fff;margin-bottom:20px;transition:all .3s;}
  .upload-zone:hover,.upload-zone.dragover{border-color:#c4a882;background:#f5ede3;}
  .upload-icon{font-size:38px;margin-bottom:10px;}
  .upload-text{font-size:16px;color:#8b7355;font-style:italic;}
  .upload-sub{font-size:12px;color:#b0a090;margin-top:6px;}

  .clothes-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;}
  .clothes-count{font-size:14px;color:#8b7355;}
  .go-btn{background:#2c2420;color:#faf7f4;border:none;border-radius:20px;padding:8px 18px;font-size:13px;letter-spacing:1px;cursor:pointer;font-family:'Cormorant Garamond',serif;}

  .clothes-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;}
  .cloth-card{position:relative;border-radius:14px;overflow:hidden;aspect-ratio:3/4;background:#f5f0eb;border:1px solid #e8e0d8;transition:transform .2s;}
  .cloth-card:hover{transform:scale(1.03);}
  .cloth-card img{width:100%;height:100%;object-fit:cover;}
  .cloth-remove{position:absolute;top:6px;right:6px;background:rgba(0,0,0,.55);border:none;border-radius:50%;width:26px;height:26px;color:#fff;cursor:pointer;font-size:15px;display:flex;align-items:center;justify-content:center;}
  .cloth-tag{position:absolute;bottom:0;left:0;right:0;background:rgba(44,36,32,.75);padding:4px 6px;font-size:10px;color:#faf7f4;text-align:center;line-height:1.3;}
  .cloth-analyzing{position:absolute;inset:0;background:rgba(44,36,32,.5);display:flex;align-items:center;justify-content:center;font-size:22px;}
  .spinner{border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;width:22px;height:22px;animation:spin .8s linear infinite;}

  .empty{text-align:center;padding:40px 0;color:#c4b4a4;font-style:italic;font-size:15px;}

  .info-box{background:#fff;border-radius:14px;padding:14px 16px;margin-bottom:22px;display:flex;gap:12px;align-items:center;border:1px solid #e8e0d8;}
  .info-icon{font-size:22px;}
  .info-title{font-size:14px;font-weight:500;}
  .info-sub{font-size:12px;color:#8b7355;font-style:italic;}

  .section-label{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#8b7355;margin-bottom:10px;}
  .weather-opts{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:22px;}
  .event-opts{display:flex;flex-direction:column;gap:8px;margin-bottom:28px;}

  .opt-btn{border-radius:20px;padding:8px 14px;font-size:14px;cursor:pointer;font-family:'Cormorant Garamond',serif;transition:all .2s;background:#fff;color:#4a3728;border:1px solid #d4c4b4;}
  .opt-btn:hover{transform:translateY(-1px);}
  .opt-btn.selected{background:#2c2420;color:#faf7f4;border-color:#2c2420;}
  .event-btn{border-radius:12px;padding:12px 16px;font-size:15px;text-align:left;border:1px solid #d4c4b4;cursor:pointer;font-family:'Cormorant Garamond',serif;transition:all .2s;background:#fff;color:#4a3728;width:100%;}
  .event-btn:hover{transform:translateY(-1px);}
  .event-btn.selected{background:#2c2420;color:#faf7f4;border-color:#2c2420;}

  .suggest-btn{width:100%;background:#8b5a2b;color:#faf7f4;border:none;border-radius:14px;padding:17px;font-size:16px;letter-spacing:1px;margin-bottom:28px;box-shadow:0 4px 18px rgba(139,90,43,.2);cursor:pointer;font-family:'Playfair Display',serif;transition:all .3s;}
  .suggest-btn:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(139,90,43,.3);}
  .suggest-btn:disabled{background:#d4c4b4;box-shadow:none;cursor:not-allowed;transform:none;}

  .loading{text-align:center;padding:16px;}
  .loading-icon{font-size:30px;margin-bottom:10px;}
  .loading-text{color:#8b7355;font-style:italic;font-size:14px;}

  .error-box{background:#fff5f5;border:1px solid #f5c6c6;border-radius:14px;padding:16px 20px;margin-bottom:16px;color:#c0392b;font-size:14px;}
  .error-sub{margin-top:6px;font-size:12px;color:#8b7355;}

  .result-box{background:#fff;border-radius:18px;padding:24px 20px;border:1px solid #e8e0d8;box-shadow:0 4px 20px rgba(44,36,32,.06);}
  .result-line{width:36px;height:3px;background:#c4a882;border-radius:2px;margin-bottom:18px;}
  .result-text h3{font-family:'Playfair Display',serif;color:#8b5a2b;font-size:16px;margin:14px 0 6px;font-weight:600;}
  .result-text p{line-height:1.85;color:#4a3728;font-size:15px;margin-bottom:4px;}
  .result-text strong{color:#8b5a2b;}
  .retry-btn{margin-top:18px;background:transparent;border:1px solid #c4a882;border-radius:20px;padding:8px 18px;color:#8b5a2b;font-size:14px;letter-spacing:1px;cursor:pointer;font-family:'Cormorant Garamond',serif;transition:all .2s;}
  .retry-btn:hover{transform:translateY(-1px);}

  .no-clothes{text-align:center;padding:60px 20px;}
  .no-clothes-icon{font-size:44px;margin-bottom:14px;}
  .no-clothes-text{color:#8b7355;font-style:italic;margin-bottom:20px;}
  .go-wardrobe{background:#2c2420;color:#faf7f4;border:none;border-radius:20px;padding:10px 24px;font-size:14px;cursor:pointer;font-family:'Cormorant Garamond',serif;}

  .selected-preview{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;}
  .preview-chip{background:#f5ede3;border:1px solid #d4c4b4;border-radius:20px;padding:4px 10px;font-size:12px;color:#4a3728;}
</style>
</head>
<body>

<div class="header">
  <div class="header-sub">AI Stylist</div>
  <h1 class="header-title">Dolabim</h1>
  <div class="tabs">
    <button class="tab active" id="tab-wardrobe" onclick="showScreen('wardrobe')">&#128087; Dolabim (<span id="count">0</span>)</button>
    <button class="tab" id="tab-suggest" onclick="showScreen('suggest')">&#10024; Kombin Al</button>
  </div>
</div>

<div class="container">
  <div class="screen active fade-up" id="screen-wardrobe">
    <p class="subtitle">Kiyafetlerinin fotograflarini ekle</p>
    <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
      <div class="upload-icon">&#128087;</div>
      <div class="upload-text">Fotograf surukle veya tikla</div>
      <div class="upload-sub">Tum dolabini yukleyebilirsin</div>
    </div>
    <input type="file" id="fileInput" accept="image/*" multiple style="display:none" onchange="handleFiles(this.files)">
    <div id="clothesSection" style="display:none">
      <div class="clothes-header">
        <span class="clothes-count" id="clothesCount">0 parca eklendi</span>
        <button class="go-btn" onclick="showScreen('suggest')">Kombin Al &#8594;</button>
      </div>
      <div class="clothes-grid" id="clothesGrid"></div>
    </div>
    <div class="empty" id="emptyMsg">Henuz kiyafet eklenmedi</div>
  </div>

  <div class="screen" id="screen-suggest">
    <div id="no-clothes" class="no-clothes" style="display:none">
      <div class="no-clothes-icon">&#128087;</div>
      <p class="no-clothes-text">Once dolabina kiyafet ekle</p>
      <button class="go-wardrobe" onclick="showScreen('wardrobe')">Dolabima Git</button>
    </div>
    <div id="suggest-content">
      <div class="info-box">
        <div class="info-icon">&#128087;</div>
        <div>
          <div class="info-title" id="infoCount">0 kiyafet yuklendi</div>
          <div class="info-sub">AI dolabindan en uygun kombinasyonu sececek</div>
        </div>
      </div>

      <div class="section-label">Bugun Hava</div>
      <div class="weather-opts">
        <button class="opt-btn" onclick="selectWeather(this,'sicak (25C+)')">&#9728;&#65039; Sicak</button>
        <button class="opt-btn" onclick="selectWeather(this,'ilik (15-25C)')">&#127780;&#65039; Ilik</button>
        <button class="opt-btn" onclick="selectWeather(this,'serin (5-15C)')">&#129509; Serin</button>
        <button class="opt-btn" onclick="selectWeather(this,'soguk (5C alti)')">&#10052;&#65039; Soguk</button>
        <button class="opt-btn" onclick="selectWeather(this,'yagmurlu')">&#127783;&#65039; Yagmurlu</button>
      </div>

      <div class="section-label">Etkinlik</div>
      <div class="event-opts">
        <button class="event-btn" onclick="selectEvent(this,'is toplantisi veya ofis')">&#128188; Is / Toplanti</button>
        <button class="event-btn" onclick="selectEvent(this,'gunluk casual cikis')">&#9749; Gunluk / Casual</button>
        <button class="event-btn" onclick="selectEvent(this,'gece disari cikma')">&#127769; Gece / Eglence</button>
        <button class="event-btn" onclick="selectEvent(this,'spor veya aktif aktivite')">&#127939; Spor / Aktif</button>
        <button class="event-btn" onclick="selectEvent(this,'romantik veya ozel gun')">&#128149; Ozel Gun</button>
        <button class="event-btn" onclick="selectEvent(this,'alisveris veya arkadasla bulusma')">&#128717;&#65039; Alisveris</button>
      </div>

      <button class="suggest-btn" id="suggestBtn" onclick="getSuggestion()" disabled>&#10024; Kombin Oner</button>

      <div class="loading" id="loading" style="display:none">
        <div class="loading-icon pulse">&#10024;</div>
        <p class="loading-text">Stilist dusunuyor...</p>
      </div>

      <div class="error-box" id="errorBox" style="display:none">
        <span id="errorMsg"></span>
        <div class="error-sub">Tekrar denemek icin butona bas.</div>
      </div>

      <div class="result-box fade-up" id="resultBox" style="display:none">
        <div class="result-line"></div>
        <div class="result-text" id="resultText"></div>
        <button class="retry-btn" onclick="getSuggestion()">&#128260; Farkli Kombin</button>
      </div>
    </div>
  </div>
</div>

<script>
// ── Veri modeli ──────────────────────────────────────────────────────────────
// Her kiyafet: { id, url, base64, tag: { ... detayli profil } | null, confirmed: bool }
// pendingConfirm: { item, profile } — teyit bekleyen kiyafet
let clothes = [];
let selectedWeather = null;
let selectedEvent = null;
let pendingConfirm = null;

const STORAGE_KEY = 'dolabim_v2';

// ── LocalStorage ─────────────────────────────────────────────────────────────
function saveToStorage() {
  try {
    const data = clothes.map(c => ({ id: c.id, base64: c.base64, tag: c.tag }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch(e) { console.warn('Storage hatasi:', e); }
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    data.forEach(item => {
      clothes.push({
        id: item.id,
        url: 'data:image/jpeg;base64,' + item.base64,
        base64: item.base64,
        tag: item.tag
      });
    });
    renderClothes();
  } catch(e) { console.warn('Storage yuklenemedi:', e); }
}

// ── Goruntu isleme ────────────────────────────────────────────────────────────
function compressImage(file, maxDim = 600, quality = 0.65) {
  return new Promise(res => {
    const img = new Image();
    const blobUrl = URL.createObjectURL(file);
    img.onload = () => {
      let w = img.width, h = img.height;
      if (w > maxDim || h > maxDim) {
        if (w > h) { h = Math.round(h * maxDim / w); w = maxDim; }
        else { w = Math.round(w * maxDim / h); h = maxDim; }
      }
      const c = document.createElement('canvas');
      c.width = w; c.height = h;
      c.getContext('2d').drawImage(img, 0, 0, w, h);
      const b64 = c.toDataURL('image/jpeg', quality).split(',')[1];
      URL.revokeObjectURL(blobUrl);
      res(b64);
    };
    img.src = blobUrl;
  });
}

// ── Derin analiz (her kiyafet icin tek API cagrisi) ──────────────────────────
async function analyzeCloth(item) {
  try {
    const res = await fetch('/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 400,
        system: 'Sadece JSON don. Baska hicbir sey yazma. Fotograf kalitesi ne olursa olsun (kirişik, karanlik, yerde, asilik, uzerinde) kiyafeti analiz et.',
        messages: [{
          role: 'user',
          content: [
            { type: 'image', source: { type: 'base64', media_type: 'image/jpeg', data: item.base64 } },
            { type: 'text', text: 'Bu kiyafeti tum detaylariyla analiz et. Fotograf burusuk/karanlik/duzensizdahi olsa kiyafeti anla. Sadece su JSON formatinda don, baska hicbir sey yazma:\n{"parca_tipi":"ornek: slim fit chino pantolon","kategori":"ust/alt/dis/ayakkabi/aksesuar","ana_renk":"ornek: koyu lacivert","ikincil_renk":"varsa yaz yoksa bos birak","desen":"duz/cizgili/kareli/cicekli/baskili","kumaş_tahmini":"ornek: pamuk","fit":"slim/regular/oversize/fitted","stil":["casual","ofis","spor","elegant"],"mevsim":["yaz","kis","ilkbahar","sonbahar"],"askida_tanim":"Bu kiyafeti beyaz bir askida asili duruyor gibi tek cümlede tanimla. Ornek: Beyaz askida asili koyu lacivert slim fit chino pantolon.","kombinlenir_ile":["ornek: beyaz gomlek","ornek: gri kazak"]}' }
          ]
        }]
      })
    });
    const data = await res.json();
    const text = data.content?.find(b => b.type === 'text')?.text || '';
    const clean = text.replace(/```json|```/g, '').trim();
    const profile = JSON.parse(clean);
    // Teyit ekranini goster
    showConfirmScreen(item, profile);
  } catch(e) {
    // Analiz basarisiz — yine de teyit sor ama bos profille
    showConfirmScreen(item, {
      parca_tipi: 'Tanımlanamadı',
      kategori: 'diger',
      ana_renk: 'bilinmiyor',
      ikincil_renk: '',
      desen: 'duz',
      kumaş_tahmini: '',
      fit: 'regular',
      stil: ['casual'],
      mevsim: ['yaz','kis','ilkbahar','sonbahar'],
      askida_tanim: 'Kıyafet analiz edilemedi. Lütfen bilgileri düzenleyin.',
      kombinlenir_ile: []
    });
  }
}

// ── Teyit ekrani ──────────────────────────────────────────────────────────────
function showConfirmScreen(item, profile) {
  pendingConfirm = { item, profile };

  // Normalize canvas: beyaz arkaplan uzerine kiyafeti ortala
  const canvas = document.createElement('canvas');
  canvas.width = 300; canvas.height = 400;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#f8f5f2';
  ctx.fillRect(0, 0, 300, 400);

  const img = new Image();
  img.onload = () => {
    // Kiyafeti orantili olarak ortala
    const scale = Math.min(280 / img.width, 360 / img.height);
    const w = img.width * scale;
    const h = img.height * scale;
    const x = (300 - w) / 2;
    const y = (400 - h) / 2;
    ctx.drawImage(img, x, y, w, h);

    // Askı çiz
    ctx.strokeStyle = '#8b7355';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(150, 0);
    ctx.lineTo(150, y - 2);
    ctx.stroke();
    // Askı çengeli
    ctx.beginPath();
    ctx.arc(150, y - 8, 6, 0, Math.PI * 2);
    ctx.stroke();

    const normalizedUrl = canvas.toDataURL('image/jpeg', 0.85);
    renderConfirmModal(normalizedUrl, profile);
  };
  img.src = item.url;
}

function renderConfirmModal(normalizedUrl, profile) {
  // Varsa eski modali kaldir
  const old = document.getElementById('confirmModal');
  if (old) old.remove();

  const stilList = Array.isArray(profile.stil) ? profile.stil.join(', ') : profile.stil;
  const mevsimList = Array.isArray(profile.mevsim) ? profile.mevsim.join(', ') : profile.mevsim;
  const kombinList = Array.isArray(profile.kombinlenir_ile) ? profile.kombinlenir_ile.join(', ') : '';

  const modal = document.createElement('div');
  modal.id = 'confirmModal';
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(44,36,32,.85);z-index:1000;display:flex;align-items:flex-end;justify-content:center;';

  modal.innerHTML = `
    <div style="background:#faf7f4;border-radius:24px 24px 0 0;width:100%;max-width:480px;padding:24px 20px 40px;max-height:90vh;overflow-y:auto;">
      <div style="text-align:center;margin-bottom:16px;">
        <div style="font-size:11px;letter-spacing:3px;color:#8b7355;text-transform:uppercase;margin-bottom:6px;">Kıyafet Tanındı</div>
        <div style="font-family:'Playfair Display',serif;font-size:18px;color:#2c2420;">${profile.askida_tanim}</div>
      </div>

      <div style="text-align:center;margin-bottom:20px;">
        <img src="${normalizedUrl}" style="width:180px;height:240px;object-fit:contain;border-radius:16px;border:1px solid #e8e0d8;background:#f8f5f2;">
      </div>

      <div style="background:#fff;border-radius:14px;padding:14px 16px;border:1px solid #e8e0d8;margin-bottom:20px;font-size:14px;line-height:2;">
        <div><strong style="color:#8b5a2b;">Parça:</strong> <span id="edit_parca">${profile.parca_tipi}</span></div>
        <div><strong style="color:#8b5a2b;">Renk:</strong> <span id="edit_renk">${profile.ana_renk}${profile.ikincil_renk ? ' + ' + profile.ikincil_renk : ''}</span></div>
        <div><strong style="color:#8b5a2b;">Desen:</strong> <span>${profile.desen}</span></div>
        <div><strong style="color:#8b5a2b;">Fit:</strong> <span>${profile.fit}</span></div>
        <div><strong style="color:#8b5a2b;">Stil:</strong> <span>${stilList}</span></div>
        <div><strong style="color:#8b5a2b;">Mevsim:</strong> <span>${mevsimList}</span></div>
        ${kombinList ? '<div><strong style="color:#8b5a2b;">Kombinlenir:</strong> <span style="color:#8b7355;font-style:italic;">' + kombinList + '</span></div>' : ''}
      </div>

      <div style="display:flex;gap:10px;">
        <button onclick="rejectConfirm()" style="flex:1;background:transparent;border:1px solid #d4c4b4;border-radius:14px;padding:14px;font-size:15px;cursor:pointer;font-family:'Cormorant Garamond',serif;color:#8b7355;">✗ Bu değil</button>
        <button onclick="approveConfirm()" style="flex:2;background:#2c2420;border:none;border-radius:14px;padding:14px;font-size:15px;cursor:pointer;font-family:'Playfair Display',serif;color:#faf7f4;">✓ Evet, dolaba ekle</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
}

function approveConfirm() {
  if (!pendingConfirm) return;
  const { item, profile } = pendingConfirm;
  item.tag = {
    kategori: profile.kategori,
    ana_renk: profile.ana_renk,
    ikincil_renk: profile.ikincil_renk || '',
    desen: profile.desen,
    kumaş: profile.kumaş_tahmini || '',
    fit: profile.fit,
    stil: Array.isArray(profile.stil) ? profile.stil : [profile.stil],
    mevsim: Array.isArray(profile.mevsim) ? profile.mevsim : [profile.mevsim],
    parca_tipi: profile.parca_tipi,
    askida_tanim: profile.askida_tanim,
    kombinlenir_ile: profile.kombinlenir_ile || [],
    // Eski uyumluluk icin
    renk: profile.ana_renk,
    stil_str: Array.isArray(profile.stil) ? profile.stil[0] : profile.stil
  };
  item.confirmed = true;
  pendingConfirm = null;
  document.getElementById('confirmModal')?.remove();
  saveToStorage();
  renderClothes();
}

function rejectConfirm() {
  if (!pendingConfirm) return;
  // Dolaba ekleme, sadece kaldir
  const { item } = pendingConfirm;
  const idx = clothes.findIndex(c => c.id === item.id);
  if (idx !== -1) clothes.splice(idx, 1);
  pendingConfirm = null;
  document.getElementById('confirmModal')?.remove();
  renderClothes();
}

// ── Akilli secim: hava + etkinlige gore en uygun maks 7 kiyafet ──────────────
function selectBestClothes(weather, event) {
  const tagged = clothes.filter(c => c.tag && c.confirmed);
  if (tagged.length === 0) return clothes.filter(c => c.tag).slice(0, 7);

  let targetStil = 'casual';
  if (event.includes('ofis') || event.includes('toplanti')) targetStil = 'ofis';
  else if (event.includes('gece') || event.includes('ozel')) targetStil = 'elegant';
  else if (event.includes('spor')) targetStil = 'spor';

  let targetMevsim = 'tum_mevsim';
  if (weather.includes('sicak')) targetMevsim = 'yaz';
  else if (weather.includes('soguk')) targetMevsim = 'kis';
  else if (weather.includes('serin')) targetMevsim = 'ilkbahar';

  const scored = tagged.map(c => {
    let score = 0;
    const stilArr = Array.isArray(c.tag.stil) ? c.tag.stil : [c.tag.stil_str || 'casual'];
    const mevsimArr = Array.isArray(c.tag.mevsim) ? c.tag.mevsim : [c.tag.mevsim || 'tum_mevsim'];
    if (stilArr.includes(targetStil)) score += 3;
    if (mevsimArr.includes(targetMevsim) || mevsimArr.includes('tum_mevsim')) score += 2;
    return { c, score };
  });

  scored.sort((a, b) => b.score - a.score);

  const selected = [];
  const cats = { ust: false, alt: false };
  for (const { c } of scored) {
    if (selected.length >= 7) break;
    if (c.tag.kategori === 'ust' && !cats.ust) { cats.ust = true; selected.push(c); }
    else if (c.tag.kategori === 'alt' && !cats.alt) { cats.alt = true; selected.push(c); }
    else if (!['ust','alt'].includes(c.tag.kategori)) selected.push(c);
  }
  for (const { c } of scored) {
    if (selected.length >= 7) break;
    if (!selected.includes(c)) selected.push(c);
  }
  return selected;
}

// ── UI ────────────────────────────────────────────────────────────────────────
function showScreen(name) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('screen-' + name).classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'suggest') {
    const has = clothes.length > 0;
    document.getElementById('no-clothes').style.display = has ? 'none' : 'block';
    document.getElementById('suggest-content').style.display = has ? 'block' : 'none';
    document.getElementById('infoCount').textContent = clothes.length + ' kiyafet dolabinda';
  }
}

async function handleFiles(files) {
  const newItems = [];
  for (const file of Array.from(files)) {
    if (!file.type.startsWith('image/')) continue;
    const base64 = await compressImage(file);
    const item = { id: Date.now() + Math.random(), url: 'data:image/jpeg;base64,' + base64, base64, tag: null, confirmed: false };
    clothes.push(item);
    newItems.push(item);
  }
  renderClothes();
  // Sirayla analiz et — biri onaylanmadan digeri baslamasin
  for (const item of newItems) {
    await new Promise(resolve => {
      const original_approve = window.approveConfirm;
      const original_reject = window.rejectConfirm;
      window.approveConfirm = function() { original_approve(); resolve(); window.approveConfirm = original_approve; window.rejectConfirm = original_reject; };
      window.rejectConfirm = function() { original_reject(); resolve(); window.approveConfirm = original_approve; window.rejectConfirm = original_reject; };
      analyzeCloth(item);
    });
  }
}

function renderClothes() {
  const grid = document.getElementById('clothesGrid');
  document.getElementById('count').textContent = clothes.length;
  document.getElementById('clothesCount').textContent = clothes.length + ' parca eklendi';
  document.getElementById('clothesSection').style.display = clothes.length > 0 ? 'block' : 'none';
  document.getElementById('emptyMsg').style.display = clothes.length > 0 ? 'none' : 'block';
  grid.innerHTML = '';
  clothes.forEach(item => {
    const card = document.createElement('div');
    card.className = 'cloth-card';
    card.id = 'card-' + item.id;
    let inner = '<img src="' + item.url + '">';
    inner += '<button class="cloth-remove" onclick="removeCloth(' + JSON.stringify(item.id) + ')">x</button>';
    if (!item.tag) {
      inner += '<div class="cloth-analyzing"><div class="spinner"></div></div>';
    } else {
      const renk = item.tag.ana_renk || item.tag.renk || '';
      const tip = item.tag.parca_tipi || item.tag.kategori || '';
      inner += '<div class="cloth-tag">' + renk + ' · ' + tip + '</div>';
    }
    card.innerHTML = inner;
    grid.appendChild(card);
  });
  updateSuggestBtn();
}

function removeCloth(id) {
  const idx = clothes.findIndex(c => c.id === id);
  if (idx !== -1) clothes.splice(idx, 1);
  saveToStorage();
  renderClothes();
}

function selectWeather(btn, val) {
  document.querySelectorAll('.opt-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedWeather = val;
  updateSuggestBtn();
}

function selectEvent(btn, val) {
  document.querySelectorAll('.event-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedEvent = val;
  updateSuggestBtn();
}

function updateSuggestBtn() {
  document.getElementById('suggestBtn').disabled = !(clothes.length > 0 && selectedWeather && selectedEvent);
}

function renderMarkdown(text) {
  return text.split('\n').map(line => {
    if (!line.trim()) return '<div style="height:8px"></div>';
    if (line.startsWith('**') && line.endsWith('**')) return '<h3>' + line.replace(/\*\*/g,'') + '</h3>';
    return '<p>' + line.replace(/\*\*(.*?)\*\*/g,'<strong>$1</strong>') + '</p>';
  }).join('');
}

async function getSuggestion() {
  if (!clothes.length || !selectedWeather || !selectedEvent) return;
  document.getElementById('suggestBtn').disabled = true;
  document.getElementById('loading').style.display = 'block';
  document.getElementById('resultBox').style.display = 'none';
  document.getElementById('errorBox').style.display = 'none';

  try {
    // Akilli secim
    const selected = selectBestClothes(selectedWeather, selectedEvent);

    const imageContents = selected.map(c => ({
      type: 'image',
      source: { type: 'base64', media_type: 'image/jpeg', data: c.base64 }
    }));

    // Etiket ozeti (resim gondermeden once metin olarak da bildir)
    const tagSummary = clothes.filter(c => c.tag && c.confirmed).map((c, i) =>
      (i+1) + '. ' + (c.tag.parca_tipi || c.tag.kategori) + ', ' + (c.tag.ana_renk || c.tag.renk) + ', ' + (Array.isArray(c.tag.stil) ? c.tag.stil.join('/') : c.tag.stil_str)
    ).join('\n');

    const prompt = 'Sen dunyaca unlu bir moda stilistisin. Vogue ve Harpers Bazaar gibi dergilerin stil rehberlerini, renk teorisini icsellestirmis uzmansin.\n\nKullanicinin dolabinda toplam ' + clothes.length + ' parca var. Sana en uygun ' + selected.length + ' tanesini gonderdim.\n\nTum dolap ozeti:\n' + tagSummary + '\n\nHava: ' + selectedWeather + '\nEtkinlik: ' + selectedEvent + '\n\nBu kiyafetlerden en iyi kombinasyonu olustur:\n\n**Bugunun Kombin Onerisi**\n[Hangi parcalar nasil bir araya gelmeli]\n\n**Neden Bu Kombin?**\n[Renk uyumu, siluet, uygunluk]\n\n**Tamamlayici Detaylar**\n[Ayakkabi, canta, aksesuar]\n\n**Stil Tuyosu**\n[Bir moda sirri]\n\nTurkce yaz, samimi ve ilham verici ol.';

    const res = await fetch('/suggest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'claude-sonnet-4-5',
        max_tokens: 1000,
        system: 'Sen kapsamli moda bilgisine sahip profesyonel bir AI stilistisin. Her zaman Turkce yanit verirsin.',
        messages: [{ role: 'user', content: [...imageContents, { type: 'text', text: prompt }] }]
      })
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error?.message || 'HTTP ' + res.status);
    }
    const data = await res.json();
    const text = data.content?.find(b => b.type === 'text')?.text;
    if (!text) throw new Error('Bos yanit');

    document.getElementById('resultText').innerHTML = renderMarkdown(text);
    document.getElementById('resultBox').style.display = 'block';
  } catch(e) {
    document.getElementById('errorMsg').textContent = e.message;
    document.getElementById('errorBox').style.display = 'block';
  }

  document.getElementById('loading').style.display = 'none';
  document.getElementById('suggestBtn').disabled = false;
}

// ── Drag & Drop ───────────────────────────────────────────────────────────────
const zone = document.getElementById('uploadZone');
zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragover'); });
zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
zone.addEventListener('drop', e => { e.preventDefault(); zone.classList.remove('dragover'); handleFiles(e.dataTransfer.files); });

// ── Baslangic ─────────────────────────────────────────────────────────────────
loadFromStorage();
</script>
</body>
</html>'''


def check_rate_limit(ip):
    now = time.time()
    with rate_lock:
        if ip not in rate_store:
            rate_store[ip] = []
        rate_store[ip] = [t for t in rate_store[ip] if now - t < 60]
        if len(rate_store[ip]) >= RATE_LIMIT:
            return False
        rate_store[ip].append(now)
        return True


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
    request_line = lines[0]
    parts = request_line.split(" ")
    if len(parts) < 2:
        return None, None, None, None

    method = parts[0]
    path = parts[1]

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
    status_texts = {200: "OK", 400: "Bad Request", 404: "Not Found", 413: "Payload Too Large", 429: "Too Many Requests", 502: "Bad Gateway"}
    status_text = status_texts.get(status, "Error")
    if isinstance(body, str):
        body = body.encode("utf-8")
    header = (
        "HTTP/1.1 " + str(status) + " " + status_text + "\r\n"
        "Content-Type: " + content_type + "\r\n"
        "Content-Length: " + str(len(body)) + "\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: POST, GET, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Connection: close\r\n"
        "\r\n"
    )
    try:
        conn.sendall(header.encode("utf-8") + body)
    except Exception:
        pass


def handle_suggest(body):
    try:
        data = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return 400, json.dumps({"error": "Invalid JSON"})

    sanitized = {
        "model": data.get("model", "claude-sonnet-4-5"),
        "max_tokens": min(int(data.get("max_tokens", 1000)), MAX_TOKENS_LIMIT),
        "messages": data.get("messages", []),
    }
    if "system" in data:
        sanitized["system"] = str(data["system"])[:500]
    if sanitized["model"] not in ALLOWED_MODELS:
        sanitized["model"] = "claude-sonnet-4-5"

    api_payload = json.dumps(sanitized).encode()
    print("[INFO] Anthropic API'ye gonderiliyor: " + str(round(len(api_payload) / 1024 / 1024, 2)) + " MB")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=api_payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return 200, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        result = e.read().decode("utf-8", errors="replace")
        print("[HATA] Anthropic API " + str(e.code) + ": " + result[:300])
        return e.code, result
    except urllib.error.URLError as e:
        return 502, json.dumps({"error": "API baglanti hatasi: " + str(e.reason)})


def handle_client(conn, addr):
    try:
        method, path, headers, body = parse_request(conn)
        if method is None:
            conn.close()
            return

        client_ip = addr[0]
        print("[" + method + "] " + path + " (" + client_ip + ", " + str(len(body) if body else 0) + " bytes)")

        if method == "OPTIONS":
            send_response(conn, 200, "text/plain", "")
        elif method == "GET" and (path == "/" or path == "/index.html"):
            send_response(conn, 200, "text/html; charset=utf-8", INDEX_HTML)
        elif method == "GET" and path == "/health":
            send_response(conn, 200, "application/json", '{"status":"ok"}')
        elif method == "POST" and path == "/suggest":
            if not check_rate_limit(client_ip):
                send_response(conn, 429, "application/json", '{"error":"Rate limit exceeded"}')
            else:
                status, result = handle_suggest(body)
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
    server.listen(5)
    print("AI Stylist baslatildi - http://localhost:" + str(PORT))

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\nSunucu durduruluyor...")
        server.close()
