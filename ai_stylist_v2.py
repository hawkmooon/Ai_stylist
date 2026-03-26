import socket
import json
import urllib.request
import urllib.error
import os
import sys
import threading
import base64

API_KEY = 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
PORT = int(os.environ.get("PORT", 8765))
MAX_TOKENS_LIMIT = 2000

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
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{background:#faf7f4;font-family:'Cormorant Garamond',Georgia,serif;color:#2c2420;min-height:100vh;}
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-thumb{background:#c4a882;border-radius:2px;}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
@keyframes pulse{0%,100%{opacity:.4}50%{opacity:1}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes slideOut{from{transform:translateX(0);opacity:1}to{transform:translateX(120%);opacity:0}}
@keyframes slideIn{from{transform:translateX(-120%);opacity:0}to{transform:translateX(0);opacity:1}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
.fade-up{animation:fadeUp .45s ease forwards;}

/* AUTH SCREEN */
#auth-screen{
  position:fixed;inset:0;background:linear-gradient(135deg,#2c2420 0%,#4a3728 50%,#8b5a2b 100%);
  display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:1000;
  padding:40px 20px;
}
.auth-logo{font-family:'Playfair Display',serif;font-size:42px;color:#faf7f4;margin-bottom:8px;letter-spacing:2px;}
.auth-sub{font-size:13px;letter-spacing:4px;color:#c4a882;margin-bottom:50px;text-transform:uppercase;}
.auth-hanger{font-size:60px;margin-bottom:30px;animation:float 3s ease-in-out infinite;}
.google-btn{
  background:#fff;border:none;border-radius:50px;padding:16px 32px;
  font-size:16px;font-family:'Cormorant Garamond',serif;cursor:pointer;
  display:flex;align-items:center;gap:12px;box-shadow:0 4px 20px rgba(0,0,0,.3);
  transition:all .3s;width:100%;max-width:300px;justify-content:center;
}
.google-btn:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(0,0,0,.4);}
.google-icon{width:22px;height:22px;}
.auth-note{color:#c4a882;font-size:12px;margin-top:20px;text-align:center;font-style:italic;}

/* ONBOARD SCREEN */
#onboard-screen{
  position:fixed;inset:0;background:#faf7f4;z-index:900;
  display:flex;flex-direction:column;align-items:center;padding:40px 20px;
  overflow-y:auto;
}
.onboard-title{font-family:'Playfair Display',serif;font-size:28px;color:#2c2420;margin-bottom:8px;text-align:center;}
.onboard-sub{color:#8b7355;font-style:italic;margin-bottom:30px;text-align:center;}
.body-upload-zone{
  border:2px dashed #c4a882;border-radius:20px;padding:40px 20px;
  text-align:center;cursor:pointer;background:#fff;width:100%;max-width:360px;
  margin-bottom:20px;transition:all .3s;
}
.body-upload-zone:hover{border-color:#8b5a2b;background:#f5ede3;}
.body-preview{width:100%;max-width:360px;border-radius:20px;overflow:hidden;margin-bottom:20px;position:relative;}
.body-preview img{width:100%;display:block;}
.body-analysis{background:#fff;border-radius:14px;padding:16px;width:100%;max-width:360px;margin-bottom:20px;border:1px solid #e8e0d8;}
.analysis-item{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f0e8e0;font-size:14px;}
.analysis-item:last-child{border:none;}
.analysis-label{color:#8b7355;}
.analysis-value{font-weight:500;color:#2c2420;}
.start-btn{
  background:#8b5a2b;color:#faf7f4;border:none;border-radius:14px;
  padding:17px;font-size:16px;width:100%;max-width:360px;
  cursor:pointer;font-family:'Playfair Display',serif;transition:all .3s;
}
.start-btn:disabled{background:#d4c4b4;cursor:not-allowed;}

/* HEADER */
.header{background:#2c2420;padding:20px 16px 14px;position:sticky;top:0;z-index:100;}
.header-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.header-title{font-family:'Playfair Display',serif;font-size:22px;color:#faf7f4;}
.user-avatar{width:34px;height:34px;border-radius:50%;border:2px solid #c4a882;cursor:pointer;}
.tabs{display:flex;justify-content:center;gap:0;}
.tab{border:1px solid #c4a882;padding:7px 16px;font-size:12px;letter-spacing:1px;cursor:pointer;
  font-family:'Cormorant Garamond',serif;transition:all .2s;background:transparent;color:#c4a882;}
.tab.active{background:#c4a882;color:#2c2420;}
.tab:first-child{border-radius:20px 0 0 20px;}
.tab:last-child{border-radius:0 20px 20px 0;}
.tab:not(:first-child):not(:last-child){border-left:none;border-right:none;}

/* MAIN */
.container{max-width:480px;margin:0 auto;padding:20px 16px 80px;}
.screen{display:none;}
.screen.active{display:block;}

/* WARDROBE */
.wardrobe-wrapper{position:relative;}
.wardrobe-bg{
  background:linear-gradient(180deg,#3d2b1f 0%,#5c3d2e 30%,#7a5040 100%);
  border-radius:20px;padding:16px;margin-bottom:20px;position:relative;overflow:hidden;
  min-height:300px;
}
.wardrobe-top-bar{
  display:flex;gap:8px;margin-bottom:16px;
}
.wardrobe-rail{
  background:linear-gradient(90deg,#8b6914,#c4a035,#8b6914);
  height:8px;border-radius:4px;margin-bottom:16px;position:relative;box-shadow:0 2px 8px rgba(0,0,0,.4);
}
.wardrobe-rail::before,.wardrobe-rail::after{
  content:'';position:absolute;top:-6px;width:3px;height:20px;
  background:#a07820;border-radius:2px;
}
.wardrobe-rail::before{left:20px;}
.wardrobe-rail::after{right:20px;}
.clothes-rail{display:flex;gap:10px;overflow-x:auto;padding:8px 4px 16px;min-height:140px;}
.clothes-rail::-webkit-scrollbar{height:3px;}
.clothes-rail::-webkit-scrollbar-thumb{background:#c4a882;border-radius:2px;}
.hanger-item{
  flex-shrink:0;width:90px;cursor:pointer;text-align:center;position:relative;
  transition:transform .3s;
}
.hanger-item:hover{transform:translateY(-4px);}
.hanger-top{font-size:16px;display:block;}
.hanger-img{
  width:80px;height:100px;object-fit:cover;border-radius:8px;
  border:2px solid rgba(255,255,255,.2);box-shadow:0 4px 12px rgba(0,0,0,.4);
}
.hanger-label{font-size:9px;color:#faf7f4;margin-top:4px;line-height:1.2;opacity:.8;}
.wardrobe-floor{
  height:12px;background:linear-gradient(180deg,#8b6914,#5c4510);
  border-radius:0 0 8px 8px;margin-top:8px;
}
.wardrobe-empty{text-align:center;padding:40px 20px;color:#c4b090;font-style:italic;}

/* UPLOAD */
.upload-zone{
  border:2px dashed #d4c4b4;border-radius:18px;padding:28px 20px;
  text-align:center;cursor:pointer;background:#fff;margin-bottom:16px;transition:all .3s;
}
.upload-zone:hover{border-color:#c4a882;background:#f5ede3;}
.upload-icon{font-size:32px;margin-bottom:8px;}
.upload-text{font-size:15px;color:#8b7355;font-style:italic;}

/* SUGGEST */
.section-label{font-size:11px;letter-spacing:3px;text-transform:uppercase;color:#8b7355;margin-bottom:10px;}
.weather-opts{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px;}
.event-opts{display:flex;flex-direction:column;gap:8px;margin-bottom:24px;}
.opt-btn{
  border-radius:20px;padding:8px 14px;font-size:14px;cursor:pointer;
  font-family:'Cormorant Garamond',serif;transition:all .2s;
  background:#fff;color:#4a3728;border:1px solid #d4c4b4;
}
.opt-btn.selected{background:#2c2420;color:#faf7f4;border-color:#2c2420;}
.event-btn{
  border-radius:12px;padding:12px 16px;font-size:15px;text-align:left;
  border:1px solid #d4c4b4;cursor:pointer;font-family:'Cormorant Garamond',serif;
  transition:all .2s;background:#fff;color:#4a3728;width:100%;
}
.event-btn.selected{background:#2c2420;color:#faf7f4;border-color:#2c2420;}
.suggest-btn{
  width:100%;background:#8b5a2b;color:#faf7f4;border:none;border-radius:14px;
  padding:17px;font-size:16px;letter-spacing:1px;margin-bottom:24px;
  box-shadow:0 4px 18px rgba(139,90,43,.2);cursor:pointer;
  font-family:'Playfair Display',serif;transition:all .3s;
}
.suggest-btn:hover{transform:translateY(-2px);}
.suggest-btn:disabled{background:#d4c4b4;box-shadow:none;cursor:not-allowed;transform:none;}

/* RESULT */
.result-box{
  background:#fff;border-radius:18px;padding:24px 20px;
  border:1px solid #e8e0d8;box-shadow:0 4px 20px rgba(44,36,32,.06);margin-bottom:20px;
}
.result-line{width:36px;height:3px;background:#c4a882;border-radius:2px;margin-bottom:16px;}
.result-text h3{font-family:'Playfair Display',serif;color:#8b5a2b;font-size:16px;margin:14px 0 6px;}
.result-text p{line-height:1.85;color:#4a3728;font-size:15px;margin-bottom:4px;}
.result-text strong{color:#8b5a2b;}
.feedback-row{display:flex;gap:12px;margin-top:16px;}
.feedback-btn{
  flex:1;padding:10px;border-radius:12px;border:1px solid #d4c4b4;
  background:#fff;cursor:pointer;font-family:'Cormorant Garamond',serif;
  font-size:14px;transition:all .2s;
}
.feedback-btn.like{border-color:#4caf50;color:#4caf50;}
.feedback-btn.like:hover,.feedback-btn.like.active{background:#4caf50;color:#fff;}
.feedback-btn.dislike{border-color:#f44336;color:#f44336;}
.feedback-btn.dislike:hover,.feedback-btn.dislike.active{background:#f44336;color:#fff;}

/* LOADING */
.loading{text-align:center;padding:20px;}
.spinner{border:3px solid #f0e8e0;border-top-color:#c4a882;border-radius:50%;width:36px;height:36px;animation:spin .8s linear infinite;margin:0 auto 12px;}
.loading-text{color:#8b7355;font-style:italic;font-size:14px;}

/* AI COMMENT TOAST */
.ai-toast{
  position:fixed;bottom:90px;left:50%;transform:translateX(-50%);
  background:#2c2420;color:#faf7f4;border-radius:20px;padding:12px 20px;
  font-size:14px;font-style:italic;max-width:320px;text-align:center;
  box-shadow:0 4px 20px rgba(0,0,0,.3);z-index:500;
  animation:fadeUp .4s ease forwards;
}
.ai-toast-emoji{font-size:20px;display:block;margin-bottom:4px;}

/* CLOTH DETAIL */
.cloth-detail-overlay{
  position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:800;
  display:flex;align-items:flex-end;
}
.cloth-detail-sheet{
  background:#faf7f4;border-radius:24px 24px 0 0;padding:24px 20px 40px;
  width:100%;max-height:80vh;overflow-y:auto;
}
.cloth-detail-img{width:100%;max-height:300px;object-fit:contain;border-radius:14px;margin-bottom:16px;}
.cloth-tags{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px;}
.cloth-tag-chip{background:#f5ede3;border:1px solid #d4c4b4;border-radius:20px;padding:4px 12px;font-size:12px;color:#4a3728;}
.remove-cloth-btn{width:100%;padding:12px;border:1px solid #f44336;border-radius:12px;color:#f44336;background:#fff;font-family:'Cormorant Garamond',serif;font-size:15px;cursor:pointer;}

/* PROFILE */
.profile-card{background:#fff;border-radius:18px;padding:20px;margin-bottom:16px;border:1px solid #e8e0d8;}
.profile-avatar{width:70px;height:70px;border-radius:50%;border:3px solid #c4a882;margin-bottom:12px;}
.profile-name{font-family:'Playfair Display',serif;font-size:20px;margin-bottom:4px;}
.profile-email{color:#8b7355;font-size:13px;margin-bottom:16px;}
.profile-stat{display:flex;justify-content:space-around;padding-top:12px;border-top:1px solid #f0e8e0;}
.stat-item{text-align:center;}
.stat-num{font-family:'Playfair Display',serif;font-size:22px;color:#8b5a2b;}
.stat-label{font-size:11px;color:#8b7355;letter-spacing:1px;}
.logout-btn{width:100%;padding:12px;border:1px solid #d4c4b4;border-radius:12px;color:#8b7355;background:#fff;font-family:'Cormorant Garamond',serif;font-size:15px;cursor:pointer;margin-top:8px;}

.error-box{background:#fff5f5;border:1px solid #f5c6c6;border-radius:14px;padding:14px;margin-bottom:14px;color:#c0392b;font-size:14px;}
</style>
</head>
<body>

<!-- AUTH SCREEN -->
<div id="auth-screen">
  <div class="auth-hanger">👗</div>
  <div class="auth-logo">Dolabım</div>
  <div class="auth-sub">AI Kişisel Stilist</div>
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
      <div style="font-family:'Playfair Display',serif;font-size:20px;color:#faf7f4;">Dolabım</div>
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
      <div class="wardrobe-bg">
        <div class="wardrobe-rail"></div>
        <div class="clothes-rail" id="clothes-rail">
          <div class="wardrobe-empty" id="wardrobe-empty">
            Henüz kıyafet eklenmedi<br>
            <span style="font-size:12px;">Aşağıdan fotoğraf ekle</span>
          </div>
        </div>
        <div class="wardrobe-floor"></div>
      </div>
      
      <div class="upload-zone" onclick="document.getElementById('fileInput').click()">
        <div class="upload-icon">📷</div>
        <div class="upload-text">Kıyafet fotoğrafı ekle</div>
      </div>
      <input type="file" id="fileInput" accept="image/*" multiple style="display:none" onchange="handleClothes(this.files)">
      
      <div id="upload-loading" style="display:none;" class="loading">
        <div class="spinner"></div>
        <div class="loading-text">AI kıyafetini analiz ediyor...</div>
      </div>
    </div>

    <!-- SUGGEST SCREEN -->
    <div class="screen" id="screen-suggest">
      <div id="suggest-form">
        <div style="background:#fff;border-radius:14px;padding:14px 16px;margin-bottom:20px;display:flex;gap:12px;align-items:center;border:1px solid #e8e0d8;">
          <div style="font-size:22px;">👗</div>
          <div>
            <div style="font-size:14px;font-weight:500;" id="suggest-count">0 kıyafet yüklendi</div>
            <div style="font-size:12px;color:#8b7355;font-style:italic;">AI dolabından en uygun kombinasyonu seçecek</div>
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
        <button onclick="resetSuggest()" style="width:100%;background:transparent;border:1px solid #c4a882;border-radius:12px;padding:10px;color:#8b5a2b;font-family:'Cormorant Garamond',serif;font-size:14px;cursor:pointer;">
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
import { getFirestore, doc, getDoc, setDoc, updateDoc, arrayUnion, increment, collection, addDoc, query, where, getDocs } from "https://www.gstatic.com/firebasejs/12.11.0/firebase-firestore.js";

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

// AI TOAST COMMENTS
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

window.signInWithGoogle = async () => {
  const provider = new GoogleAuthProvider();
  try {
    await signInWithPopup(auth, provider);
  } catch(e) {
    alert('Giriş başarısız: ' + e.message);
  }
};

window.signOut = async () => {
  await fbSignOut(auth);
};

onAuthStateChanged(auth, async (user) => {
  if (user) {
    currentUser = user;
    document.getElementById('auth-screen').style.display = 'none';
    
    // Set avatar
    if (user.photoURL) {
      document.getElementById('user-avatar').src = user.photoURL;
      document.getElementById('user-avatar').style.display = 'block';
      document.getElementById('profile-avatar-big').src = user.photoURL;
    }
    document.getElementById('profile-name').textContent = user.displayName || 'Kullanıcı';
    document.getElementById('profile-email').textContent = user.email;

    // Check if onboarded
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

window.handleBodyPhoto = async (file) => {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = async (e) => {
    document.getElementById('body-preview-img').src = e.target.result;
    document.getElementById('body-preview-wrap').style.display = 'block';
    
    // Analyze body
    const base64 = e.target.result.split(',')[1];
    try {
      const resp = await fetch('/analyze-body', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({image: base64})
      });
      const data = await resp.json();
      if (data.analysis) {
        document.getElementById('body-analysis-box').style.display = 'block';
        document.getElementById('body-analysis-content').innerHTML = data.analysis;
        window._bodyAnalysis = data.analysis;
        window._bodyImage = base64;
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
    comboCount: 0,
    likeCount: 0,
    createdAt: new Date().toISOString()
  }, {merge: true});
  
  document.getElementById('onboard-screen').style.display = 'none';
  document.getElementById('main-app').style.display = 'block';
  await loadClothes();
  showToast('👗', 'Dolabına hoş geldin! Kıyafetlerini eklemeye başla.');
};

async function loadClothes() {
  const userDoc = await getDoc(doc(db, 'users', currentUser.uid));
  clothes = userDoc.data()?.clothes || [];
  renderClothes();
  updateCounts();
  
  // Update profile stats
  document.getElementById('stat-clothes').textContent = clothes.length;
  document.getElementById('stat-combos').textContent = userDoc.data()?.comboCount || 0;
  document.getElementById('stat-likes').textContent = userDoc.data()?.likeCount || 0;
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
  rail.innerHTML = '';
  
  clothes.forEach((c, i) => {
    const item = document.createElement('div');
    item.className = 'hanger-item';
    item.onclick = () => showClothDetail(i);
    item.innerHTML = `
      <span class="hanger-top">🪝</span>
      <img class="hanger-img" src="${c.imageData}" alt="${c.label}">
      <div class="hanger-label">${c.label}</div>
    `;
    rail.appendChild(item);
  });
}

function updateCounts() {
  document.getElementById('count').textContent = clothes.length;
  document.getElementById('suggest-count').textContent = `${clothes.length} kıyafet yüklendi`;
  document.getElementById('stat-clothes').textContent = clothes.length;
}

window.handleClothes = async (files) => {
  for (const file of files) {
    document.getElementById('upload-loading').style.display = 'block';
    
    const reader = new FileReader();
    await new Promise(resolve => {
      reader.onload = async (e) => {
        const base64 = e.target.result.split(',')[1];
        
        try {
          const resp = await fetch('/analyze-cloth', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({image: base64})
          });
          const data = await resp.json();
          
          const cloth = {
            id: Date.now() + Math.random(),
            imageData: e.target.result,
            label: data.label || 'Kıyafet',
            tags: data.tags || [],
            aiComment: data.comment || '',
            addedAt: new Date().toISOString()
          };
          
          clothes.push(cloth);
          
          // Save to Firestore (without full image for size - just metadata)
          const clothForDB = {...cloth, imageData: e.target.result};
          await updateDoc(doc(db, 'users', currentUser.uid), {
            clothes: arrayUnion(clothForDB)
          });
          
          renderClothes();
          updateCounts();
          
          // Random fun comment
          const pick = uploadComments[Math.floor(Math.random() * uploadComments.length)];
          setTimeout(() => showToast(pick[0], data.comment || pick[1]), 500);
          
        } catch(err) {
          console.error(err);
        }
        resolve();
      };
      reader.readAsDataURL(file);
    });
  }
  document.getElementById('upload-loading').style.display = 'none';
};

window.showClothDetail = (index) => {
  currentDetailIndex = index;
  const c = clothes[index];
  document.getElementById('detail-img').src = c.imageData;
  document.getElementById('detail-tags').innerHTML = (c.tags || []).map(t => 
    `<span class="cloth-tag-chip">${t}</span>`
  ).join('');
  document.getElementById('detail-ai-comment').textContent = c.aiComment || 'Bu kıyafet dolabında çok iyi duruyor!';
  document.getElementById('cloth-detail-overlay').style.display = 'flex';
};

window.closeDetail = (e) => {
  if (e.target === document.getElementById('cloth-detail-overlay')) {
    document.getElementById('cloth-detail-overlay').style.display = 'none';
  }
};

window.removeCloth = async () => {
  if (currentDetailIndex < 0) return;
  clothes.splice(currentDetailIndex, 1);
  await setDoc(doc(db, 'users', currentUser.uid), {clothes}, {merge: true});
  renderClothes();
  updateCounts();
  document.getElementById('cloth-detail-overlay').style.display = 'none';
  showToast('🗑️', 'Kıyafet dolabından kaldırıldı.');
};

window.showScreen = (name) => {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('screen-' + name)?.classList.add('active');
  document.getElementById('tab-' + name)?.classList.add('active');
};

window.selectOpt = (btn, type, val) => {
  const parent = btn.parentElement;
  parent.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  if (type === 'weather') selectedWeather = val;
  if (type === 'event') selectedEvent = val;
  checkSuggestReady();
};

function checkSuggestReady() {
  document.getElementById('suggest-btn').disabled = 
    !(selectedWeather && selectedEvent && clothes.length > 0);
}

window.getSuggestion = async () => {
  document.getElementById('suggest-form').style.display = 'none';
  document.getElementById('suggest-loading').style.display = 'block';
  document.getElementById('suggest-result').style.display = 'none';
  
  const userDoc = await getDoc(doc(db, 'users', currentUser.uid));
  const userData = userDoc.data();
  const bodyAnalysis = userData?.bodyAnalysis || '';
  const likeHistory = userData?.likeHistory || [];
  
  const clothesList = clothes.map((c, i) => 
    `${i+1}. ${c.label} (Etiketler: ${(c.tags||[]).join(', ')})`
  ).join('\n');
  
  try {
    const resp = await fetch('/suggest', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
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
        model: 'claude-sonnet-4-5',
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
    
    // Increment combo count
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
  selectedWeather = '';
  selectedEvent = '';
  document.querySelectorAll('.opt-btn, .event-btn').forEach(b => b.classList.remove('selected'));
  checkSuggestReady();
};
</script>

</body>
</html>
'''

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
    status_texts = {200: "OK", 400: "Bad Request", 404: "Not Found", 500: "Server Error"}
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

def call_anthropic(payload):
    data = json.dumps(payload).encode()
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
            return 200, resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return 502, json.dumps({"error": str(e.reason)})

def handle_analyze_cloth(body):
    try:
        data = json.loads(body)
        image_b64 = data.get("image", "")
    except Exception:
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
                    "text": """Bu kıyafeti analiz et ve JSON olarak döndür:
{
  "label": "kısa etiket (örn: Kırmızı Gömlek)",
  "tags": ["renk", "tür", "stil", "mevsim"],
  "comment": "Bu kıyafet hakkında samimi, heyecanlı 1-2 cümle yorum (Türkçe)"
}
Sadece JSON döndür, başka şey yazma."""
                }
            ]
        }]
    }
    status, result = call_anthropic(payload)
    if status == 200:
        try:
            resp_data = json.loads(result)
            text = resp_data["content"][0]["text"]
            text = text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            parsed = json.loads(text.strip())
            return 200, json.dumps(parsed)
        except Exception as e:
            return 200, json.dumps({"label": "Kıyafet", "tags": [], "comment": "Harika bir kıyafet!"})
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
        "model": "claude-sonnet-4-5",
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
    print("AI Stylist V2 baslatildi - http://localhost:" + str(PORT))

    try:
        while True:
            conn, addr = server.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\nSunucu durduruluyor...")
        server.close()
