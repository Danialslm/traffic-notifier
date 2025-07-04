## راهنمای استفاده از برنامه

برای استفاده از این برنامه، لازم است به **پنل Virtualizor** سرور مجازی خود دسترسی داشته باشید. این پنل ممکن است در وب‌سایت ارائه‌دهنده خدمات، با عنوان **Enduser Panel** معرفی شده باشد.

### دریافت API Key و API Password

از طریق پنل Virtualizor، یک **API Key** و **API Password** ایجاد نمایید. **توصیه می‌شود حتماً آدرس IP سروری که قصد اجرای این اسکریپت را دارید در پنل وایت‌لیست کنید.** در غیر این صورت، هر فردی با هر IP می‌تواند به سرور شما دسترسی پیدا کند.

![image](https://github.com/user-attachments/assets/9037e9e1-57b7-43f1-9a97-7b56e89690ae)

---

## مراحل نصب

### 1. دانلود پروژه

ابتدا اسکریپت را از مخزن گیت‌هاب دانلود کرده و وارد پوشه پروژه شوید:

```bash
git clone https://github.com/Danialslm/traffic-notifier.git && cd traffic-notifier
```

### 2. کپی فایل‌های نمونه پیکربندی

دستورات زیر را اجرا کنید:

```bash
cp servers.json.sample servers.json
cp .env.sample .env
```

---

## پیکربندی فایل‌ها

### فایل `servers.json`

این فایل را با ویرایشگر دلخواه خود باز کرده و مقادیر آن را مطابق نیاز تنظیم کنید:

* `name`: یک نام دلخواه برای سرور.
* `url`: لینک دریافت اطلاعات از سرور مجازی در پنل Virtualizor.

نمونه‌ای از محتوای فایل:

```json
[
  {
    "name": "ایران ۱",
    "url": "https://example.com:4083/sess6ICCoygYmavNA358/index.php?act=vpsmanage&svs=85&api=json&apikey=<api key>&apipass=<api password>"
  },
  {
    "name": "ایران ۲",
    "url": "https://example.com:4083/sess6ICCoygYmavNA358/index.php?act=vpsmanage&svs=371&api=json&apikey=<api key>&apipass=<api password>"
  }
]
```

![image](https://github.com/user-attachments/assets/03a63fe8-aa5d-440f-baf5-c3a8f6ff5889)

---

### فایل `.env`

این فایل را با مقادیر دلخواه به‌صورت زیر ویرایش کنید:

```env
# توکن ربات تلگرام
BOT_TOKEN=

# شناسه چتی که ربات باید نوتیفیکیشن را به آن ارسال کند
CHAT_ID=

# آستانه‌های هشدار در صورت کاهش درصد باقی‌مانده ترافیک
NOTIFY_TRAFFIC_PERCENTS=10,5,1

# فاصله زمانی اجرای برنامه (بر حسب دقیقه)
INTERVAL_MINUTES=5
```

---

## اجرای برنامه

برای اجرای برنامه با استفاده از Docker و مشاهده لاگ‌ها، دستور زیر را اجرا کنید:

```bash
docker compose up -d && docker compose logs -f
```

---

### پیشنهادات و بازخورد

از دریافت نظرات و پیشنهادات شما استقبال می‌کنیم 💫

---
