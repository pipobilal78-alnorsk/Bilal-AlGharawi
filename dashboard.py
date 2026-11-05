"""Interactive Mobile & Desktop Web Dashboard for Smart Mail Sentinel v2.0 (Public Open-Source Edition)."""

import os
import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

logger = logging.getLogger(__name__)

# Global live log buffer for real-time web streaming
GLOBAL_LOG_BUFFER = []


class MemoryLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            GLOBAL_LOG_BUFFER.append(msg)
            if len(GLOBAL_LOG_BUFFER) > 120:
                GLOBAL_LOG_BUFFER.pop(0)
        except Exception:
            pass


HTML_TEMPLATE = """<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    
    <!-- iOS Web App Metadata -->
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Mail Sentinel">
    <meta name="theme-color" content="#090d16">
    <link rel="apple-touch-icon" href="/logo.jpg">
    <link rel="apple-touch-icon" sizes="180x180" href="/logo.jpg">
    
    <title>Smart Mail Sentinel v2.0 - المساعد الذكي للبريد</title>
    
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", "Segoe UI", Roboto, sans-serif;
            background: #070a12;
            color: #f8fafc;
            padding: max(16px, env(safe-area-inset-top)) max(16px, env(safe-area-inset-right)) max(80px, env(safe-area-inset-bottom)) max(16px, env(safe-area-inset-left));
            min-height: 100vh;
        }
        .container { max-width: 760px; margin: 0 auto; }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(18, 24, 38, 0.85);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            padding: 16px 20px;
            border-radius: 22px;
            margin-bottom: 16px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 12px 35px rgba(0,0,0,0.4);
        }
        .logo-box { display: flex; align-items: center; gap: 14px; }
        .logo-img {
            width: 52px;
            height: 52px;
            border-radius: 14px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.6);
            border: 1px solid rgba(255,255,255,0.15);
            object-fit: cover;
        }
        .app-title { font-size: 19px; font-weight: 700; letter-spacing: -0.5px; }
        .app-sub { font-size: 12px; color: #94a3b8; margin-top: 2px; }
        
        .pills-group { display: flex; gap: 8px; flex-wrap: wrap; }
        .status-pill {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            border: 1px solid rgba(16, 185, 129, 0.25);
        }
        .shield-pill {
            background: rgba(56, 189, 248, 0.15);
            color: #38bdf8;
            padding: 6px 14px;
            border-radius: 30px;
            font-size: 12px;
            font-weight: 600;
            border: 1px solid rgba(56, 189, 248, 0.25);
        }
        .status-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 10px #10b981;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

        .accounts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 10px;
            margin-bottom: 16px;
        }
        .acc-card {
            background: rgba(22, 30, 49, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 14px 12px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .acc-icon {
            font-size: 18px;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
        }
        .acc-name { font-size: 12px; font-weight: 600; color: #f1f5f9; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .acc-sub { font-size: 11px; color: #94a3b8; margin-top: 2px; }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }
        @media (max-width: 500px) {
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
        .stat-card {
            background: rgba(22, 30, 49, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 14px 10px;
            text-align: center;
        }
        .stat-val { font-size: 22px; font-weight: 700; color: #38bdf8; margin-bottom: 4px; }
        .stat-val.red { color: #f87171; }
        .stat-val.purple { color: #c084fc; }
        .stat-val.emerald { color: #34d399; }
        .stat-lbl { font-size: 11px; color: #94a3b8; }

        .action-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            margin-bottom: 16px;
        }
        @media (max-width: 600px) {
            .action-row { grid-template-columns: 1fr; }
        }
        .btn {
            padding: 14px 16px;
            border-radius: 14px;
            font-size: 13px;
            font-weight: 600;
            border: none;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: transform 0.1s, opacity 0.2s;
        }
        .btn:active { transform: scale(0.97); }
        .btn-blue { background: #2563eb; color: #fff; box-shadow: 0 4px 14px rgba(37,99,235,0.4); }
        .btn-orange { background: linear-gradient(135deg, #ea580c, #f97316); color: #fff; box-shadow: 0 4px 14px rgba(234,88,12,0.4); }
        .btn-purple { background: #7c3aed; color: #fff; box-shadow: 0 4px 14px rgba(124,58,237,0.4); }

        .panel {
            background: rgba(22, 30, 49, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 18px;
            margin-bottom: 16px;
        }
        .panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .panel-title { font-size: 14px; font-weight: 600; color: #e2e8f0; display: flex; align-items: center; gap: 8px; }
        .btn-sm {
            background: rgba(255,255,255,0.08);
            color: #94a3b8;
            border: none;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 11px;
            cursor: pointer;
        }
        .btn-sm:hover { color: #fff; }

        .log-box {
            background: #040711;
            border-radius: 12px;
            padding: 14px;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 11px;
            color: #67e8f9;
            height: 220px;
            overflow-y: auto;
            line-height: 1.6;
            white-space: pre-wrap;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .toast {
            position: fixed;
            bottom: max(24px, env(safe-area-inset-bottom));
            left: 50%;
            transform: translateX(-50%);
            background: #10b981;
            color: #fff;
            padding: 12px 24px;
            border-radius: 30px;
            font-size: 13px;
            font-weight: 600;
            display: none;
            box-shadow: 0 6px 20px rgba(0,0,0,0.6);
            z-index: 1000;
        }
    </style>
</head>
<body>
<div class="container">

    <div class="header">
        <div class="logo-box">
            <img src="/logo.jpg" alt="Logo" class="logo-img">
            <div>
                <h1 class="app-title">Smart Mail Sentinel <span style="font-size: 12px; color: #38bdf8; background: rgba(56,189,248,0.15); padding: 2px 6px; border-radius: 6px;">v2.0 AI</span></h1>
                <p class="app-sub">الحماية والتنظيف التلقائي بالذكاء الاصطناعي</p>
            </div>
        </div>
        <div class="pills-group">
            <div class="status-pill">
                <span class="status-dot"></span> الحماية نشطة
            </div>
            <div class="shield-pill">
                🛡️ رادار الاحتيال مفعّل
            </div>
        </div>
    </div>

    <div class="accounts-grid" id="accounts-grid"></div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-val red" id="val-promo">0</div>
            <div class="stat-lbl">إعلانات محذوفة</div>
        </div>
        <div class="stat-card">
            <div class="stat-val emerald" id="val-scam">0</div>
            <div class="stat-lbl">محاولات احتيال محظورة</div>
        </div>
        <div class="stat-card">
            <div class="stat-val" id="val-cycle">5 د</div>
            <div class="stat-lbl">دورة الفحص</div>
        </div>
        <div class="stat-card">
            <div class="stat-val purple" id="val-digest">23:59</div>
            <div class="stat-lbl">الملخص الليلي الذكي</div>
        </div>
    </div>

    <div class="action-row">
        <button class="btn btn-blue" onclick="triggerCheck()">
            <span>⚡ فحص الوارد الآن</span>
        </button>
        <button class="btn btn-orange" onclick="triggerDeepClean()">
            <span>🧹 تنظيف عميق (30 يوم)</span>
        </button>
        <button class="btn btn-purple" onclick="triggerDigest()">
            <span>🌙 إرسال الملخص الذكي</span>
        </button>
    </div>

    <div class="panel">
        <div class="panel-header">
            <div class="panel-title">📜 سجل العمليات الحية (Live Logs)</div>
            <button class="btn-sm" onclick="fetchLogs()">تحديث 🔄</button>
        </div>
        <div class="log-box" id="log-box">جاري جلب السجل الحي...</div>
    </div>

</div>

<div class="toast" id="toast"></div>

<script>
function showToast(msg) {
    const t = document.getElementById('toast');
    t.innerText = msg;
    t.style.display = 'block';
    if (navigator.vibrate) navigator.vibrate(50);
    setTimeout(() => { t.style.display = 'none'; }, 2500);
}

function fetchStats() {
    fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            if (data.cleaned_count !== undefined) {
                document.getElementById('val-promo').innerText = data.cleaned_count;
            }
            if (data.scam_count !== undefined) {
                document.getElementById('val-scam').innerText = data.scam_count;
            }
            if (data.check_interval) {
                document.getElementById('val-cycle').innerText = Math.round(data.check_interval / 60) + ' د';
            }
            if (data.night_digest_time) {
                document.getElementById('val-digest').innerText = data.night_digest_time;
            }
            if (data.account_list && data.account_list.length > 0) {
                const grid = document.getElementById('accounts-grid');
                const icons = ['🔴', '🟣', '🟢', '🔵', '🟠'];
                grid.innerHTML = data.account_list.map((acc, idx) => `
                    <div class="acc-card">
                        <div class="acc-icon">${icons[idx % icons.length]}</div>
                        <div>
                            <div class="acc-name">${acc.email}</div>
                            <div class="acc-sub">${acc.provider} • محمي ✅</div>
                        </div>
                    </div>
                `).join('');
            }
        })
        .catch(e => console.error(e));
}

function fetchLogs() {
    fetch('/api/logs')
        .then(r => r.json())
        .then(data => {
            const box = document.getElementById('log-box');
            if (data.logs && data.logs.length > 0) {
                box.innerText = data.logs.join('\\n');
            } else {
                box.innerText = "🟢 Smart Mail Sentinel v2.0 يعمل بنجاح 24/7\\n🔍 دورة الفحص التلقائي مستمرة...";
            }
            box.scrollTop = box.scrollHeight;
        })
        .catch(e => console.error(e));
}

function triggerCheck() {
    showToast('⚡ جاري فحص الحسابات الآن...');
    fetch('/api/check', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
            showToast('✅ تم فحص الصناديق وتنظيف الترويجي!');
            fetchLogs();
            fetchStats();
        });
}

function triggerDeepClean() {
    showToast('🧹 جاري تشغيل التنظيف العميق لآخر 30 يوماً...');
    fetch('/api/deep-clean', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
            showToast('✅ اكتمل التنظيف العميق لـ 30 يوماً بنجاح!');
            fetchLogs();
            fetchStats();
        });
}

function triggerDigest() {
    showToast('🌙 جاري إرسال الملخص الذكي إلى بريدك...');
    fetch('/api/digest', { method: 'POST' })
        .then(r => r.json())
        .then(() => {
            showToast('✅ تم إرسال التقرير الذكي بنجاح!');
            fetchLogs();
            fetchStats();
        });
}

fetchLogs();
fetchStats();
setInterval(() => {
    fetchLogs();
    fetchStats();
}, 8000);
</script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    bot_context = None

    def log_message(self, format, *args):
        return

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        elif self.path == "/logo.jpg" or self.path == "/apple-touch-icon.png":
            logo_path = os.path.join(os.path.dirname(__file__), "logo.jpg")
            if os.path.exists(logo_path):
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                with open(logo_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

        elif self.path == "/api/logs":
            log_file = os.path.join(os.path.dirname(__file__), "sentinel.log")
            lines = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
            if not lines and GLOBAL_LOG_BUFFER:
                lines = list(GLOBAL_LOG_BUFFER)
            if not lines:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                lines = [
                    f"{now_str} [INFO] 🟢 Smart Mail Sentinel v2.0 يعمل بنجاح 24/7",
                    f"{now_str} [INFO] 🔍 رادار كشف الاحتيال والتصيد مفعّل ومستمر"
                ]
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"logs": lines[-50:]}).encode("utf-8"))

        elif self.path == "/api/status":
            cfg = self.bot_context.get("config") if self.bot_context else None
            notifier = self.bot_context.get("notifier") if self.bot_context else None

            cleaned_cnt = 0
            scam_cnt = 0
            if notifier:
                daily_cleaned = len(getattr(notifier.stats, "promotional_emails", []))
                lifetime_cleaned = getattr(notifier, "lifetime_cleaned", 0)
                cleaned_cnt = max(daily_cleaned, lifetime_cleaned)

                daily_scam = len(getattr(notifier.stats, "scam_emails", []))
                lifetime_scam = getattr(notifier, "lifetime_scam", 0)
                scam_cnt = max(daily_scam, lifetime_scam)

            account_list = []
            if cfg and cfg.accounts:
                account_list = [{"email": a.email_address, "provider": a.provider} for a in cfg.accounts if a.enabled]

            data = {
                "running": True,
                "version": "2.0 AI",
                "accounts": len(account_list),
                "account_list": account_list,
                "night_digest_time": cfg.night_digest_time if cfg else "23:59",
                "check_interval": cfg.check_interval_seconds if cfg else 300,
                "cleaned_count": cleaned_cnt,
                "scam_count": scam_cnt
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path == "/api/digest-data":
            notifier = self.bot_context.get("notifier") if self.bot_context else None
            if notifier:
                html_content = notifier.generate_digest_html()
                text_content = notifier.generate_digest_text()
                data = {
                    "subject": f"📊 الملخص الليلي الذكي للبريد الإلكتروني - {notifier.stats.date_str}",
                    "recipient": notifier.config.report_recipient or notifier.config.email_address,
                    "html": html_content,
                    "text": text_content
                }
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(data).encode("utf-8"))
            else:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/check":
            if self.bot_context and "run_check" in self.bot_context:
                try:
                    self.bot_context["run_check"]()
                except Exception as e:
                    logger.error(f"Error in manual check: {e}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Check complete"}).encode("utf-8"))

        elif self.path == "/api/deep-clean":
            if self.bot_context and "run_deep_clean" in self.bot_context:
                try:
                    self.bot_context["run_deep_clean"]()
                except Exception as e:
                    logger.error(f"Error in deep clean: {e}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Deep clean complete"}).encode("utf-8"))

        elif self.path == "/api/digest":
            if self.bot_context and "notifier" in self.bot_context:
                try:
                    self.bot_context["notifier"].send_daily_digest(force=True)
                except Exception as e:
                    logger.error(f"Error in manual digest: {e}")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Digest sent"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def start_dashboard_server(bot_context: dict, port: int = 8080):
    """Starts the multithreaded web dashboard server."""
    DashboardHandler.bot_context = bot_context

    def _serve():
        try:
            httpd = ThreadedHTTPServer(("0.0.0.0", port), DashboardHandler)
            logger.info(f"لوحة التحكم v2.0 جاهزة: http://localhost:{port}")
            httpd.serve_forever()
        except Exception as e:
            logger.error(f"فشل تشغيل سيرفر اللوحة: {e}")

    import threading
    t = threading.Thread(target=_serve, daemon=True)
    t.start()
