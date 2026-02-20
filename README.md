# 🎬 YouTube İndirici

> **Reklamsız. İnternet sitesi yok. Tamamen lokalde çalışır — hiçbir şey buluta gönderilmez.**

YouTube'dan video (1080p MP4) veya ses (WAV) indiren küçük bir masaüstü uygulaması.

## Kurulum (tek seferlik)

### 🪟 Windows

**1. Python yüklü değilse:** [python.org](https://python.org) → Download → Kur ("Add to PATH" kutusunu işaretle)

**2. Terminalde:**
```bash
pip install -r requirements.txt
winget install ffmpeg
```

**3. Çalıştır:**
```bash
pythonw app.py
```

---

### 🐧 Linux

**Debian / Ubuntu / Mint:**
```bash
sudo apt install python3 python3-pip ffmpeg -y
pip3 install -r requirements.txt
python3 app.py
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S python python-pip ffmpeg --noconfirm
pip install -r requirements.txt
python app.py
```

---

İndirilen dosyalar otomatik olarak **İndirilenler (Downloads)** klasörüne kaydedilir.
