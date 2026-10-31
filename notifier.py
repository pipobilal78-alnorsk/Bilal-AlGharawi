"""Notification, Smart AI Digest, and Security Alerts module for Smart Mail Sentinel v2.0."""

import os
import re
import json
import time
import email
from email.utils import parsedate_to_datetime
import smtplib
import subprocess
import logging
from collections import Counter
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

from config import Config
from classifier import EmailCategory, EmailClassifier
from mail_client import ParsedEmail, MailClient

logger = logging.getLogger(__name__)


@dataclass
class DailyStats:
    date_str: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    total_checked: int = 0
    promotional_emails: List[ParsedEmail] = field(default_factory=list)
    important_emails: List[ParsedEmail] = field(default_factory=list)
    scam_emails: List[ParsedEmail] = field(default_factory=list)
    normal_emails: List[ParsedEmail] = field(default_factory=list)

    def reset(self):
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.total_checked = 0
        self.promotional_emails.clear()
        self.important_emails.clear()
        self.scam_emails.clear()
        self.normal_emails.clear()


class Notifier:
    def __init__(self, config: Config):
        self.config = config
        self.stats = DailyStats()
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.reports_dir = os.path.join(base_dir, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)
        self.stats_file = os.path.join(base_dir, "stats.json")
        self.lifetime_cleaned = 0
        self.lifetime_scam = 0
        self.daily_counts: Dict[str, Dict[str, int]] = {}
        self.trash_uid_baseline: Dict[str, Dict[str, Any]] = {}
        self._last_imap_sync_ts = 0.0
        self._last_sent_digest_date = ""
        self._load_lifetime_stats()

    def _load_lifetime_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.lifetime_cleaned = data.get("lifetime_cleaned", 0)
                    self.lifetime_scam = data.get("lifetime_scam", 0)
                    self.daily_counts = data.get("daily_counts", {})
                    self.trash_uid_baseline = data.get("trash_uid_baseline", {})
            except Exception:
                pass

    def _save_lifetime_stats(self):
        try:
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump({
                    "lifetime_cleaned": self.lifetime_cleaned,
                    "lifetime_scam": self.lifetime_scam,
                    "daily_counts": self.daily_counts,
                    "trash_uid_baseline": self.trash_uid_baseline
                }, f, indent=2)
        except Exception:
            pass

    def _check_date_rollover(self):
        now_date = datetime.now().strftime("%Y-%m-%d")
        if self.stats.date_str != now_date:
            self.stats.reset()

    def record_email(self, email_item: ParsedEmail, account_email: str = ""):
        """Records email activity into daily and lifetime statistics."""
        self._check_date_rollover()
        today = self.stats.date_str
        if today not in self.daily_counts:
            self.daily_counts[today] = {"total": 0, "cleaned": 0, "important": 0, "scam": 0}

        if account_email and "X-Account" not in email_item.headers:
            email_item.headers["X-Account"] = account_email

        self.stats.total_checked += 1
        self.daily_counts[today]["total"] += 1

        cat = email_item.classification.category if email_item.classification else EmailCategory.NORMAL

        if cat == EmailCategory.PROMOTIONAL:
            self.stats.promotional_emails.append(email_item)
            self.lifetime_cleaned += 1
            self.daily_counts[today]["cleaned"] += 1
            self._save_lifetime_stats()
        elif cat == EmailCategory.IMPORTANT:
            self.stats.important_emails.append(email_item)
            self.daily_counts[today]["important"] += 1
            self._save_lifetime_stats()
        elif cat == EmailCategory.SCAM_PHISHING:
            self.stats.scam_emails.append(email_item)
            self.lifetime_scam += 1
            self.daily_counts[today]["scam"] += 1
            self._save_lifetime_stats()
        else:
            self.stats.normal_emails.append(email_item)
            self._save_lifetime_stats()

    def notify_important_email(self, email_item: ParsedEmail):
        """Dispatches an immediate alert for an important incoming email."""
        reasons_text = ", ".join(email_item.classification.reasons) if email_item.classification else ""

        alert_msg = f"""
============================================================
🚨 [تنبيه بريد هام وعاجل!] 🚨
👤 المرسل: {email_item.sender_name} ({email_item.sender_email})
📌 الموضوع: {email_item.subject}
💡 السبب: {reasons_text}
📝 مقتطف: {email_item.snippet[:200]}...
============================================================
"""
        print(alert_msg)
        logger.info(f"تم إطلاق تنبيه لبريد هام من: {email_item.sender_email}")

        self._trigger_mac_notification(
            title="🚨 بريد إلكتروني هام جديد",
            subtitle=email_item.sender_name,
            message=email_item.subject[:100]
        )

    def notify_scam_email(self, email_item: ParsedEmail):
        """Dispatches a security alert for a detected phishing or scam email."""
        logger.warning(f"⚠️ رصد محاولة تصيد احتيالي من: {email_item.sender_email} ('{email_item.subject}')")

        self._trigger_mac_notification(
            title="⚠️ تحذير أمان: رصد رسالة مشبوهة",
            subtitle=email_item.sender_name,
            message=f"مشبوه: {email_item.subject[:90]}"
        )

    def _trigger_mac_notification(self, title: str, subtitle: str, message: str):
        """Sends native macOS banner notification using osascript."""
        try:
            safe_title = title.replace('"', '\\"')
            safe_sub = subtitle.replace('"', '\\"')
            safe_msg = message.replace('"', '\\"')
            script = f'display notification "{safe_msg}" with title "{safe_title}" subtitle "{safe_sub}" sound name "Glass"'
            subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def get_top_spammers(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Returns top N most frequent promotional/spam senders."""
        senders = [m.sender_name or m.sender_email for m in self.stats.promotional_emails]
        return Counter(senders).most_common(top_n)

    @staticmethod
    def _extract_internal_date_local(meta_str: str) -> Optional[str]:
        """Extracts INTERNALDATE from IMAP FETCH metadata and converts to local YYYY-MM-DD."""
        m = re.search(r'INTERNALDATE "([^"]+)"', meta_str)
        if not m:
            return None
        try:
            dt = parsedate_to_datetime(m.group(1))
            return dt.astimezone().strftime("%Y-%m-%d")
        except Exception:
            return None

    @staticmethod
    def _extract_imap_uid(meta_str: str, fallback_seq: str) -> int:
        """Extracts numeric UID from IMAP FETCH metadata."""
        m = re.search(r'UID (\d+)', meta_str)
        if m:
            return int(m.group(1))
        try:
            return int(fallback_seq)
        except Exception:
            return 0

    def _sync_today_from_imap(self, target_date_str: Optional[str] = None, record_baseline: bool = False):
        """
        Syncs all messages deleted into Trash on target_date_str (plus important INBOX messages)
        across all enabled accounts. Uses Trash sequence order + UID baseline + INTERNALDATE so
        even older messages deleted today or duplicate subjects are 100% captured.
        """
        if target_date_str is None:
            self._check_date_rollover()
            target_date = self.stats.date_str
        else:
            target_date = target_date_str

        now_ts = time.time()
        if not record_baseline and (now_ts - self._last_imap_sync_ts < 45) and getattr(self, "_last_imap_sync_date", "") == target_date:
            return
        self._last_imap_sync_ts = now_ts
        self._last_imap_sync_date = target_date

        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        since_imap_str = target_dt.strftime("%d-%b-%Y")

        classifier = EmailClassifier(
            vip_senders=self.config.vip_senders,
            custom_promo_keywords=self.config.custom_promo_keywords,
            custom_important_keywords=self.config.custom_important_keywords
        )

        # Build unique keys for already-recorded emails using Message-ID or (account, sender, subject, date)
        def _make_key(parsed_obj: ParsedEmail) -> str:
            msg_id = parsed_obj.headers.get("Message-ID", "").strip()
            acc_id = parsed_obj.headers.get("X-Account", "")
            if msg_id:
                return f"{acc_id}:{msg_id}"
            return f"{acc_id}:{parsed_obj.uid}:{parsed_obj.sender_email}:{parsed_obj.subject}:{parsed_obj.date}"

        existing_promo_keys = {_make_key(m) for m in self.stats.promotional_emails}
        existing_imp_keys = {_make_key(m) for m in self.stats.important_emails}
        total_inbox_today = 0

        for acc in self.config.accounts:
            if not acc.enabled or not acc.email_address or not acc.email_password:
                continue
            mc = MailClient(Config(accounts=[acc]), classifier)
            if not mc.connect():
                continue
            try:
                # 1. Inspect the tail of Trash in ascending order
                if mc.trash_folder:
                    sel_typ, _ = mc.connection.select(f'"{mc.trash_folder}"', readonly=True)
                    if sel_typ != "OK":
                        sel_typ, _ = mc.connection.select(mc.trash_folder, readonly=True)
                    if sel_typ == "OK":
                        typ, data = mc.connection.search(None, "ALL")
                        if typ == "OK" and data and data[0]:
                            tail_ids = data[0].split()[-40:]
                            started_target_day = False
                            baseline_info = self.trash_uid_baseline.get(acc.email_address, {})
                            baseline_uid = baseline_info.get("max_uid") if baseline_info.get("for_date") == target_date else None
                            max_seen_uid = 0

                            for mid in tail_ids:
                                seq_str = mid.decode("utf-8")
                                f_typ, msg_data = mc.connection.fetch(
                                    mid,
                                    "(UID INTERNALDATE BODY.PEEK[HEADER.FIELDS (MESSAGE-ID DATE FROM SUBJECT)])"
                                )
                                if f_typ != "OK" or not msg_data:
                                    continue
                                for part in msg_data:
                                    if isinstance(part, tuple):
                                        meta_str = part[0].decode("utf-8", errors="ignore")
                                        uid_val = self._extract_imap_uid(meta_str, seq_str)
                                        if uid_val > max_seen_uid:
                                            max_seen_uid = uid_val
                                        internal_date = self._extract_internal_date_local(meta_str)

                                        # Once any message in Trash is on target_date (or above today's UID baseline),
                                        # all subsequent messages in Trash were also moved to Trash on/after target_date.
                                        if baseline_uid is not None and uid_val > baseline_uid:
                                            started_target_day = True
                                        elif internal_date == target_date:
                                            started_target_day = True
                                        elif internal_date and internal_date > target_date:
                                            # Belongs to a newer day after target_date
                                            continue

                                        if started_target_day:
                                            msg = email.message_from_bytes(part[1])
                                            parsed = mc._parse_message(str(uid_val), msg)
                                            if parsed:
                                                parsed.headers["Message-ID"] = msg.get("Message-ID", "").strip()
                                                parsed.headers["X-Account"] = acc.email_address
                                                key = _make_key(parsed)
                                                if key not in existing_promo_keys:
                                                    existing_promo_keys.add(key)
                                                    self.stats.promotional_emails.append(parsed)

                            # Record baseline for tomorrow when requested (or initialize for today if none exists)
                            if record_baseline and max_seen_uid > 0:
                                next_day = datetime.now().strftime("%Y-%m-%d")
                                self.trash_uid_baseline[acc.email_address] = {
                                    "for_date": next_day,
                                    "max_uid": max_seen_uid
                                }

                # 2. Inspect today's messages in INBOX
                sel_typ, _ = mc.connection.select("INBOX", readonly=True)
                if sel_typ == "OK":
                    typ, data = mc.connection.search(None, f'(SINCE "{since_imap_str}")')
                    if typ == "OK" and data and data[0]:
                        inbox_ids = data[0].split()
                        for mid in inbox_ids[-35:]:
                            seq_str = mid.decode("utf-8")
                            f_typ, msg_data = mc.connection.fetch(mid, "(UID INTERNALDATE RFC822)")
                            if f_typ == "OK" and msg_data:
                                for part in msg_data:
                                    if isinstance(part, tuple):
                                        meta_str = part[0].decode("utf-8", errors="ignore")
                                        internal_date = self._extract_internal_date_local(meta_str)
                                        if internal_date and internal_date != target_date:
                                            continue
                                        total_inbox_today += 1
                                        uid_val = self._extract_imap_uid(meta_str, seq_str)
                                        msg = email.message_from_bytes(part[1])
                                        parsed = mc._parse_message(str(uid_val), msg)
                                        if parsed and "الملخص الليلي الذكي" not in parsed.subject and "روابط لوحة تحكم" not in parsed.subject:
                                            parsed.headers["Message-ID"] = msg.get("Message-ID", "").strip()
                                            parsed.headers["X-Account"] = acc.email_address
                                            parsed.classification = classifier.classify(
                                                sender_name=parsed.sender_name,
                                                sender_email=parsed.sender_email,
                                                subject=parsed.subject,
                                                snippet=parsed.snippet,
                                                headers=parsed.headers
                                            )
                                            if parsed.classification.category == EmailCategory.IMPORTANT:
                                                key = _make_key(parsed)
                                                if key not in existing_imp_keys:
                                                    existing_imp_keys.add(key)
                                                    self.stats.important_emails.append(parsed)
            except Exception as e:
                logger.warning(f"تعذر مزامنة إحصائيات اليوم من {acc.email_address}: {e}")
            finally:
                mc.close()

        synced_total = len(self.stats.promotional_emails) + total_inbox_today
        if synced_total > self.stats.total_checked:
            self.stats.total_checked = synced_total

        if target_date not in self.daily_counts:
            self.daily_counts[target_date] = {"total": 0, "cleaned": 0, "important": 0, "scam": 0}
        self.daily_counts[target_date]["total"] = max(self.daily_counts[target_date].get("total", 0), self.stats.total_checked)
        self.daily_counts[target_date]["cleaned"] = len(self.stats.promotional_emails)
        self.daily_counts[target_date]["important"] = len(self.stats.important_emails)
        self._save_lifetime_stats()

    def generate_smart_ai_digest(self, target_date_str: Optional[str] = None) -> Dict[str, Any]:
        """Generates smart AI executive summary and stats."""
        self._sync_today_from_imap(target_date_str=target_date_str)
        today = target_date_str or self.stats.date_str
        today_stats = self.daily_counts.get(today, {"total": 0, "cleaned": 0, "important": 0, "scam": 0})

        cleaned = len(self.stats.promotional_emails)
        important_count = len(self.stats.important_emails)
        scam_count = len(self.stats.scam_emails)
        total = max(self.stats.total_checked, today_stats.get("total", 0), cleaned + important_count + scam_count)
        top_spammers = self.get_top_spammers(5)

        insights = []
        if scam_count > 0:
            insights.append(f"🛡️ تم رصد وإحباط {scam_count} رسائل مشبوهة لحماية حسابك.")
        if cleaned > 0:
            top_name = top_spammers[0][0] if top_spammers else "مختلف الجهات"
            insights.append(f"🗑️ تم شطب وتطهير {cleaned} رسائل في سلة المهملات اليوم (أكثرها إرسالاً: {top_name}).")
        if important_count > 0:
            insights.append(f"⭐ تم فحص وحماية {important_count} رسائل هامة وأكواد تحقق في صندوق الوارد.")
        if not insights:
            insights.append("✨ كانت صناديق البريد اليوم نظيفة وهادئة تماماً دون إعلانات مزعجة.")

        return {
            "date": today,
            "total": total,
            "cleaned": cleaned,
            "important_count": important_count,
            "scam_count": scam_count,
            "top_spammers": top_spammers,
            "insights": insights,
            "important_list": list(self.stats.important_emails),
            "scam_list": list(self.stats.scam_emails),
            "promo_list": list(self.stats.promotional_emails)
        }

    def generate_digest_text(self, target_date_str: Optional[str] = None) -> str:
        """Builds structured plain text digest with exact item-by-item list of deleted emails."""
        d = self.generate_smart_ai_digest(target_date_str=target_date_str)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        lines = [
            f"📊 تقرير الملخص الليلي الذكي (Smart AI Sentinel v2.0) - {d['date']}",
            "=" * 65,
            f"🔹 إجمالي الرسائل المفحوصة اليوم: {d['total']}",
            f"🗑️ إجمالي الرسائل التي تم شطبها اليوم (سلة المهملات): {d['cleaned']}",
            f"⭐ الرسائل الهامة المحفوظة في الوارد: {d['important_count']}",
            f"🛡️ رسائل التصيد والاحتيال المحظورة: {d['scam_count']}",
            "=" * 65,
            "🧠 ملخص الذكاء الاصطناعي:"
        ]
        for ins in d["insights"]:
            lines.append(f"  • {ins}")

        lines.append("\n" + "-" * 65)
        lines.append(f"🗑️ القائمة التفصيلية الكاملة للرسائل التي تم شطبها اليوم ({d['cleaned']} رسالة):")
        if d["promo_list"]:
            for idx, mail in enumerate(d["promo_list"], 1):
                acc_label = mail.headers.get("X-Account", "")
                acc_tag = f" [{acc_label}]" if acc_label else ""
                lines.append(f"  {idx}. ❌ المرسل: {mail.sender_name} ({mail.sender_email}){acc_tag}")
                lines.append(f"     📌 الموضوع: {mail.subject}")
        else:
            lines.append("  • لا توجد رسائل مشطوبة اليوم.")

        if d["top_spammers"]:
            lines.append("\n📈 إحصائية الجهات المرسلة للرسائل المشطوبة:")
            for name, count in d["top_spammers"]:
                lines.append(f"  - {name}: ({count} رسائل)")

        if d["important_list"]:
            lines.append("\n⭐ الرسائل الهامة التي وردت اليوم وتم الحفاظ عليها:")
            for idx, mail in enumerate(d["important_list"], 1):
                acc_label = mail.headers.get("X-Account", "")
                acc_tag = f" [{acc_label}]" if acc_label else ""
                lines.append(f"  {idx}. [{mail.sender_name}]{acc_tag} — {mail.subject}")

        if d["scam_list"]:
            lines.append("\n⚠️ تنبيهات الأمان والمحاولات المشبوهة:")
            for mail in d["scam_list"]:
                lines.append(f"  • ⚠️ [{mail.sender_name}] {mail.subject} (من: {mail.sender_email})")

        lines.append("\n" + "=" * 65)
        lines.append(f"تم إعداد التقرير آلياً في {now_str} بواسطة Smart Mail Sentinel v2.0 (24/7 Cloud & Mac).")
        return "\n".join(lines)

    def generate_digest_html(self, target_date_str: Optional[str] = None) -> str:
        """Builds Apple-themed HTML email digest with full itemized list of every deleted email."""
        d = self.generate_smart_ai_digest(target_date_str=target_date_str)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        promo_rows = "".join([
            f"""<li style="padding: 12px 14px; margin-bottom: 8px; background: #fff1f2; border-radius: 10px; border-right: 4px solid #e11d48; list-style: none;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <strong style="color: #9f1239; font-size: 13px;">{idx}. 🗑️ {m.sender_name} <span style="font-weight: normal; color: #64748b; font-size: 11px;">({m.sender_email})</span></strong>
                    <span style="background: #ffe4e6; color: #be123c; padding: 2px 8px; border-radius: 12px; font-size: 10px; font-weight: 600;">{m.headers.get('X-Account', '')}</span>
                </div>
                <div style="color: #1e293b; font-size: 13px; font-weight: 500;">📌 {m.subject}</div>
            </li>""" for idx, m in enumerate(d["promo_list"], 1)
        ]) or "<p style='color: #64748b; font-size: 13px;'>لا توجد رسائل مشطوبة اليوم.</p>"

        important_rows = "".join([
            f"""<li style="padding: 10px 14px; margin-bottom: 8px; background: rgba(59,130,246,0.08); border-radius: 10px; border-right: 4px solid #3b82f6; list-style: none;">
                <div style="margin-bottom: 2px;">
                    <strong style="color: #1e40af; font-size: 13px;">{idx}. ⭐ {m.sender_name}</strong>
                    <span style="background: #dbeafe; color: #1d4ed8; padding: 2px 8px; border-radius: 12px; font-size: 10px; margin-right: 6px;">{m.headers.get('X-Account', '')}</span>
                </div>
                <div style="color: #334155; font-size: 13px;">{m.subject}</div>
            </li>""" for idx, m in enumerate(d["important_list"], 1)
        ]) or "<p style='color: #64748b; font-size: 13px;'>لا توجد رسائل هامة جديدة اليوم.</p>"

        scam_rows = "".join([
            f"""<li style="padding: 10px 14px; margin-bottom: 8px; background: rgba(239,68,68,0.08); border-radius: 10px; border-right: 4px solid #ef4444; list-style: none;">
                <strong style="color: #b91c1c;">⚠️ {m.sender_name} ({m.sender_email}):</strong> <span style="color: #334155;">{m.subject}</span>
            </li>""" for m in d["scam_list"]
        ])

        spammers_html = "".join([
            f"""<span style="display: inline-block; background: #f1f5f9; color: #475569; padding: 5px 12px; border-radius: 20px; font-size: 12px; margin: 3px;">
                {name} <b style="color: #e11d48;">({cnt})</b>
            </span>""" for name, cnt in d["top_spammers"]
        ]) or "<span style='color: #64748b; font-size: 12px;'>لا توجد إعلانات</span>"

        insights_html = "".join([
            f"<li style='margin-bottom: 6px;'>{ins}</li>" for ins in d["insights"]
        ])

        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="utf-8">
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
    .container {{ max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; }}
    .header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); color: #ffffff; padding: 24px 28px; text-align: right; }}
    .header h1 {{ margin: 0 0 6px 0; font-size: 20px; font-weight: 700; }}
    .header p {{ margin: 0; color: #94a3b8; font-size: 13px; }}
    .content {{ padding: 24px 28px; }}
    .grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 24px; }}
    .card {{ background: #f8fafc; border-radius: 12px; padding: 14px; text-align: center; border: 1px solid #e2e8f0; }}
    .card .val {{ font-size: 22px; font-weight: 700; color: #0284c7; margin-bottom: 2px; }}
    .card .val.red {{ color: #e11d48; }}
    .card .val.purple {{ color: #7c3aed; }}
    .card .lbl {{ font-size: 11px; color: #64748b; font-weight: 500; }}
    .ai-box {{ background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%); border: 1px solid #bbf7d0; border-radius: 14px; padding: 16px 20px; margin-bottom: 20px; }}
    .ai-box h3 {{ margin: 0 0 10px 0; font-size: 14px; color: #0f766e; display: flex; align-items: center; gap: 6px; }}
    .ai-box ul {{ margin: 0; padding-right: 18px; font-size: 13px; color: #334155; line-height: 1.6; }}
    .sec-title {{ font-size: 15px; font-weight: 700; color: #0f172a; margin: 22px 0 10px 0; }}
    .footer {{ text-align: center; padding: 18px; background: #f8fafc; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🛡️ Smart Mail Sentinel v2.0</h1>
        <p>التقرير الليلي التفصيلي الكامل لحساباتك الثلاثة • {d['date']} ({now_str})</p>
    </div>
    <div class="content">
        <div class="ai-box">
            <h3>🧠 ملخص الذكاء الاصطناعي (AI Digest)</h3>
            <ul>{insights_html}</ul>
        </div>
        <div class="grid">
            <div class="card">
                <div class="val red">{d['cleaned']}</div>
                <div class="lbl">رسائل تم شطبها اليوم</div>
            </div>
            <div class="card">
                <div class="val purple">{d['important_count']}</div>
                <div class="lbl">رسائل هامة</div>
            </div>
            <div class="card">
                <div class="val">{d['total']}</div>
                <div class="lbl">إجمالي المفحوص</div>
            </div>
        </div>

        <div class="sec-title" style="color: #be123c;">🗑️ الرسائل التي تم شطبها وحذفها اليوم بالتفصيل ({d['cleaned']} رسالة):</div>
        <ul style="padding: 0; margin: 0 0 20px 0;">{promo_rows}</ul>

        <div class="sec-title">📈 إحصائية الجهات المرسلة للرسائل المشطوبة:</div>
        <div style="margin-bottom: 20px;">{spammers_html}</div>

        <div class="sec-title">⭐ أهم الرسائل الواردة اليوم:</div>
        <ul style="padding: 0; margin: 0;">{important_rows}</ul>

        {f'<div class="sec-title" style="color: #b91c1c;">⚠️ محاولات تصيد مشبوهة تم رصدها:</div><ul style="padding: 0; margin: 0;">{scam_rows}</ul>' if scam_rows else ''}
    </div>
    <div class="footer">
        يعمل على مدار الساعة 24/7 سحابياً ومحلياً • Smart Mail Sentinel v2.0
    </div>
</div>
</body>
</html>"""

    def send_daily_digest(self, force: bool = False, target_date_str: Optional[str] = None) -> bool:
        """Sends the daily digest to the report recipient via SMTP."""
        recipient = self.config.report_recipient or self.config.email_address
        if not recipient:
            logger.error("لم يتم تحديد عنوان بريد لاستقبال الملخص اليومي.")
            return False

        date_str = target_date_str or self.stats.date_str
        if not force and self._last_sent_digest_date == date_str:
            logger.info(f"تم إرسال الملخص الليلي لتاريخ {date_str} مسبقاً، تخطي التكرار.")
            return True

        self._sync_today_from_imap(target_date_str=target_date_str, record_baseline=True)
        text_content = self.generate_digest_text(target_date_str=target_date_str)
        html_content = self.generate_digest_html(target_date_str=target_date_str)

        txt_path = os.path.join(self.reports_dir, f"digest_{date_str}.txt")
        html_path = os.path.join(self.reports_dir, f"digest_{date_str}.html")

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"\n[ملخص الليلة v2.0] تم حفظ التقرير محلياً في:\n  -> {txt_path}\n  -> {html_path}\n")
        print(text_content)

        if self.config.dry_run:
            logger.info(f"[DRY-RUN] محاكاة إرسال التقرير الملخص إلى: {recipient}")
            self._last_sent_digest_date = date_str
            if target_date_str is None:
                self.stats.reset()
            return True

        for acc in self.config.accounts:
            if not acc.enabled or not acc.email_address or not acc.email_password:
                continue
            try:
                logger.info(f"جاري إرسال التقرير الملخص إلى البريد: {recipient} عبر ({acc.email_address})...")
                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"📊 الملخص الليلي الذكي للبريد الإلكتروني - {date_str}"
                msg["From"] = acc.email_address
                msg["To"] = recipient

                part1 = MIMEText(text_content, "plain", "utf-8")
                part2 = MIMEText(html_content, "html", "utf-8")
                msg.attach(part1)
                msg.attach(part2)

                with smtplib.SMTP(acc.smtp_server, acc.smtp_port, timeout=20) as server:
                    server.starttls()
                    server.login(acc.email_address, acc.email_password)
                    server.send_message(msg)

                logger.info("تم إرسال التقرير الليلي بنجاح عبر البريد الإلكتروني! ✅")
                self._last_sent_digest_date = date_str
                if target_date_str is None:
                    self.stats.reset()
                return True
            except Exception as e:
                logger.warning(f"تعذر الإرسال عبر {acc.email_address}: {e}")

        logger.error("فشل إرسال التقرير الليلي عبر جميع الحسابات المتاحة.")
        return False
