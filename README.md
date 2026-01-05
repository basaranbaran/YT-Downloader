<div align="center">
  <img src="static/favicon.png" alt="Logo" width="100" height="auto">

  # 🎵 YT Downloader

  <p>
    Flask, yt-dlp ve FFmpeg ile güçlendirilmiş modern, hızlı ve kullanıcı dostu bir YouTube indirme aracı.
    <br>
    A modern, fast, and user-friendly YouTube downloader powered by Flask, yt-dlp, and FFmpeg.
  </p>

[🇹🇷 Türkçe](#-proje-hakkında) • [🇬🇧 English](#-about-the-project)

</div>

---

<a name="-proje-hakkında"></a>
# 🇹🇷 Proje Hakkında

**YT Downloader**, YouTube videolarını ve çalma listelerini (playlist) en yüksek kalitede indirmenizi sağlayan web tabanlı bir uygulamadır. Kullanıcı dostu arayüzü sayesinde teknik bilgi gerektirmeden herkes tarafından kullanılabilir.

## ✨ Özellikler

- 🎬 **Video İndirme**: 4K, 1080p, 720p gibi farklı çözünürlüklerde video indirme.
- 🎵 **Ses İndirme**: Videoları otomatik olarak en yüksek kalitede MP3 formatına dönüştürme.
- 📀 **Playlist Desteği**: Tek tıkla bütün bir albümü veya oynatma listesini indirme.
- 📊 **Canlı İlerleme**: Playlist indirirken anlık durum bildirimleri (SSE teknolojisi ile).
- 🎨 **Modern Arayüz**: Responsive, animasyonlu ve şık tasarım.
- 🛠️ **Güçlü Altyapı**: Arka planda **FFmpeg** kullanarak ses ve görüntüyü kayıpsız birleştirir.

## 🚀 Kurulum

Bu projeyi kendi bilgisayarınızda çalıştırmak için aşağıdaki adımları izleyin.

### 1. Gereksinimler
- **Python 3.7+**
- **FFmpeg**: Video ve ses birleştirme işlemleri için **ZORUNLUDUR**.
  - **Windows:** [Buradan indirin](https://ffmpeg.org/download.html) ve `bin` klasörünü PATH'e ekleyin.
  - **Linux:** `sudo apt install ffmpeg`
  - **macOS:** `brew install ffmpeg`

### 2. İndirme ve Kurulum

Projeyi klonlayın:
```bash
git clone https://github.com/basaranbaran/YT-Downloader
cd youtube-download
```

Sanal ortam oluşturun (Önerilen):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

### 3. Çalıştırma

Uygulamayı başlatın:
```bash
python app.py
```

Tarayıcınızı açın ve şu adrese gidin:
`http://localhost:5000`

## 📁 Proje Yapısı

```
youtube-download/
├── app.py                 # Backend (Flask) - İndirme mantığı burada
├── requirements.txt       # Gerekli kütüphaneler
├── static/                # Statik dosyalar
│   ├── favicon.png        # Logo
│   ├── script.js          # Frontend mantığı (Fetch, UI updates)
│   └── style.css          # Tasarım kodları
└── templates/
    └── index.html         # Arayüz HTML dosyası
```

---

<br>

<a name="-about-the-project"></a>
# 🇬🇧 About the Project

**YT Downloader** is a web-based application that allows you to download YouTube videos and playlists in the highest quality. Thanks to its user-friendly interface, it can be used by anyone without technical knowledge.

## ✨ Features

- 🎬 **Video Download**: Download videos in various resolutions like 4K, 1080p, 720p.
- 🎵 **Audio Download**: Automatically convert videos to high-quality MP3 format.
- 📀 **Playlist Support**: Download an entire album or playlist with a single click.
- 📊 **Live Progress**: Real-time status notifications during playlist downloads (via SSE).
- 🎨 **Modern Interface**: Responsive, animated, and stylish design.
- 🛠️ **Powerful Backend**: Uses **FFmpeg** in the background to merge audio and video losslessly.

## 🚀 Installation

Follow these steps to run the project on your local machine.

### 1. Requirements
- **Python 3.7+**
- **FFmpeg**: **MANDATORY** for merging audio and video.
  - **Windows:** [Download here](https://ffmpeg.org/download.html) and add the `bin` folder to PATH.
  - **Linux:** `sudo apt install ffmpeg`
  - **macOS:** `brew install ffmpeg`

### 2. Download and Setup

Clone the project:
```bash
git clone https://github.com/basaranbaran/YT-Downloader
cd youtube-download
```

Create a virtual environment (Recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Running

Start the application:
```bash
python app.py
```

Open your browser and navigate to:
`http://localhost:5000`

## 📁 Project Structure

```
youtube-download/
├── app.py                 # Backend (Flask) - Download logic
├── requirements.txt       # Dependencies
├── static/                # Static files
│   ├── favicon.png        # Logo
│   ├── script.js          # Frontend logic (Fetch, UI updates)
│   └── style.css          # Styling
└── templates/
    └── index.html         # Interface HTML file
```

<div align="center">
  <br>
  <p>Done with ❤️ using Flask & yt-dlp</p>
</div>
