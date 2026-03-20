"""
notifiers.py  –  Gửi thông báo thật qua Telegram Bot & Gmail SMTP
Đặt file tại:  backend/module/notifiers.py

Cấu hình qua file .env ở thư mục gốc backend/:
  TELEGRAM_BOT_TOKEN=...
  TELEGRAM_CHAT_ID=...
  GMAIL_SENDER=...
  GMAIL_PASSWORD=...   (Gmail App Password 16 ký tự)
"""

import os, asyncio, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
import aiohttp

VN_TZ = timezone(timedelta(hours=7))

# ── Credentials (đọc từ biến môi trường) ─────────────────────
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID",   "")
GMAIL_SENDER       = os.getenv("GMAIL_SENDER",        "")
GMAIL_PASSWORD     = os.getenv("GMAIL_PASSWORD",      "")


# ── Nội dung thông báo ────────────────────────────────────────

def _format_rule_changes(triggered_rules: list) -> str:
    if not triggered_rules:
        return "\n\n✅ Không có kịch bản tự động nào được kích hoạt."
    
    lines = ["\n\n⚡ Kịch bản tự động đã kích hoạt:"]
    has_any_change = False
    
    for rule in triggered_rules:
        lines.append(f"  📋 {rule['rule_name']}")
        changes = rule.get("changes", [])
        
        # Trường hợp có note "không thay đổi"
        for c in changes:
            if c.get("note"):
                lines.append(f"    ℹ️ {c['note']}")
                continue
            if c.get("changed"):
                has_any_change = True
                def fmt(v):
                    if v is True  or v == 1:   return "BẬT"
                    if v is False or v == 0:   return "TẮT"
                    if isinstance(v, (int, float)):
                        return f"{v}%"
                    return str(v)
                lines.append(f"    → {c['device_name']}: {fmt(c['from'])} ➜ {fmt(c['to'])}")
        
        if not any(c.get("changed") or c.get("note") for c in changes):
            lines.append(f"    ℹ️ Không có thay đổi so với trạng thái hiện tại")
    
    return "\n".join(lines)


def _build_message(houseid: str, violations: list, sensor_data: dict,
                   triggered_rules: list = None) -> dict:
    now = datetime.now(VN_TZ).strftime("%H:%M:%S  %d/%m/%Y")
    sensor_icons = {"temp": "🌡️", "humi": "💧", "light": "💡"}
    sensor_names = {"temp": "Nhiệt độ", "humi": "Độ ẩm", "light": "Ánh sáng"}
    sensor_units = {"temp": "°C", "humi": "%", "light": "%"}

    vio_lines = []
    for v in violations:
        s     = v.get("sensor", "?")
        icon  = sensor_icons.get(s, "⚠️")
        name  = sensor_names.get(s, s.upper())
        val   = v.get("value", "?")
        th    = v.get("threshold", "?")
        limit = v.get("limit", "?")
        unit  = sensor_units.get(s, "")
        arrow = "↑ vượt MAX" if th == "max" else "↓ dưới MIN"
        vio_lines.append(f"  {icon} {name}: <b>{val}{unit}</b>  ({arrow} = {limit}{unit})")

    rule_text = _format_rule_changes(triggered_rules or [])

    plain = (
        f"🚨 <b>CẢNH BÁO SMART HOME – {houseid}</b>\n"
        f"🕐 {now}\n\n"
        f"<b>Vi phạm ngưỡng:</b>\n"
        + "\n".join(vio_lines) +
        f"\n\n📊 Dữ liệu hiện tại:\n"
        f"  🌡️ Nhiệt độ : {sensor_data.get('temp', '--')} °C\n"
        f"  💧 Độ ẩm    : {sensor_data.get('humi', '--')} %\n"
        f"  💡 Ánh sáng : {sensor_data.get('light', '--')} %"
        + (rule_text if rule_text else "") +
        f"\n\n👉 Mở App để xem chi tiết và tắt báo động."
    )

    html_rows = "".join(
        f"<tr>"
        f"<td>{sensor_icons.get(v.get('sensor',''),'⚠️')} {sensor_names.get(v.get('sensor',''), v.get('sensor','').upper())}</td>"
        f"<td style='color:#e53e3e;font-weight:bold'>{v.get('value','')} {sensor_units.get(v.get('sensor',''),'')}</td>"
        f"<td>{'↑ Vượt MAX' if v.get('threshold')=='max' else '↓ Dưới MIN'} = {v.get('limit','')} {sensor_units.get(v.get('sensor',''),'')}</td>"
        f"</tr>"
        for v in violations
    )
    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:560px;margin:auto;padding:24px">
      <div style="background:#fff5f5;border-left:5px solid #e53e3e;padding:16px 20px;border-radius:6px">
        <h2 style="color:#e53e3e;margin:0 0 6px">🚨 Cảnh báo Smart Home</h2>
        <p style="margin:0;color:#666">Nhà: <b>{houseid}</b> &nbsp;|&nbsp; 🕐 {now}</p>
      </div>
      <h3 style="margin-top:20px">⚠️ Vi phạm ngưỡng</h3>
      <table width="100%" border="1" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;border-color:#eee;font-size:14px">
        <thead style="background:#f7f7f7">
          <tr><th align="left">Cảm biến</th><th align="left">Giá trị</th><th align="left">Tình trạng</th></tr>
        </thead>
        <tbody>{html_rows}</tbody>
      </table>
      <h3 style="margin-top:20px">📊 Dữ liệu đầy đủ</h3>
      <table width="100%" cellpadding="6" style="font-size:14px">
        <tr><td>🌡️ Nhiệt độ</td><td><b>{sensor_data.get('temp','--')} °C</b></td></tr>
        <tr><td>💧 Độ ẩm</td>   <td><b>{sensor_data.get('humi','--')} %</b></td></tr>
        <tr><td>💡 Ánh sáng</td><td><b>{sensor_data.get('light','--')} %</b></td></tr>
      </table>
      {_build_rules_html(triggered_rules or [])}
      <p style="margin-top:24px;padding:12px 16px;background:#ebf8ff;border-radius:6px;font-size:13px">
        👉 Đăng nhập App để xem chi tiết và <b>tắt báo động</b>.
      </p>
    </body></html>
    """
    return {"plain": plain, "html": html}


def _build_rules_html(triggered_rules: list) -> str:
    if not triggered_rules:
        return ""
    rows = ""
    for rule in triggered_rules:
        for c in rule.get("changes", []):
            if c.get("changed"):
                def fmt(v):
                    if v is True  or v == 1:  return "<span style='color:#10b981'>BẬT</span>"
                    if v is False or v == 0:  return "<span style='color:#e53e3e'>TẮT</span>"
                    if isinstance(v, (int, float)):
                        return f"{v}%"
                    return str(v)
                rows += f"<tr><td>{rule['rule_name']}</td><td>{c['device_name']}</td><td>{fmt(c['from'])} ➜ {fmt(c['to'])}</td></tr>"
    if not rows:
        return ""
    return f"""
      <h3 style="margin-top:20px">⚡ Kịch bản tự động đã kích hoạt</h3>
      <table width="100%" border="1" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;border-color:#eee;font-size:14px">
        <thead style="background:#f0fff4">
          <tr><th align="left">Kịch bản</th><th align="left">Thiết bị</th><th align="left">Thay đổi</th></tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>"""


# ── Telegram ──────────────────────────────────────────────────

async def send_telegram(houseid: str, violations: list, sensor_data: dict,
                         bot_token: str = None, chat_id: str = None,
                         triggered_rules: list = None) -> dict:
    token = bot_token or TELEGRAM_BOT_TOKEN
    cid   = chat_id   or TELEGRAM_CHAT_ID

    if not token or not cid:
        return {"ok": False, "channel": "telegram",
                "error": "Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID"}

    msg  = _build_message(houseid, violations, sensor_data, triggered_rules)
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    body = {"chat_id": cid, "text": msg["plain"], "parse_mode": "HTML"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=body,
                                    timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
        if data.get("ok"):
            print(f"[NOTIFIER] ✅ Telegram → chat {cid}")
            return {"ok": True, "channel": "telegram"}
        print(f"[NOTIFIER] ❌ Telegram lỗi: {data.get('description','')}")
        return {"ok": False, "channel": "telegram", "error": data.get("description", str(data))}
    except Exception as e:
        print(f"[NOTIFIER] ❌ Telegram exception: {e}")
        return {"ok": False, "channel": "telegram", "error": str(e)}


# ── Email (Gmail SMTP) ─────────────────────────────────────────

async def send_email(houseid: str, violations: list, sensor_data: dict,
                      to_address: str, sender: str = None, password: str = None,
                      triggered_rules: list = None) -> dict:
    _sender = sender   or GMAIL_SENDER
    _pass   = password or GMAIL_PASSWORD

    if not _sender or not _pass:
        return {"ok": False, "channel": "email",
                "error": "Thiếu GMAIL_SENDER hoặc GMAIL_PASSWORD"}
    if not to_address:
        return {"ok": False, "channel": "email", "error": "Thiếu địa chỉ email nhận"}

    msg_content = _build_message(houseid, violations, sensor_data, triggered_rules)
    now_str = datetime.now(VN_TZ).strftime("%H:%M  %d/%m/%Y")

    mail = MIMEMultipart("alternative")
    mail["Subject"] = f"[Smart Home {houseid}] ⚠️ Cảnh báo vượt ngưỡng – {now_str}"
    mail["From"]    = f"Smart Home Alert <{_sender}>"
    mail["To"]      = to_address
    mail.attach(MIMEText(msg_content["plain"].replace("<b>","").replace("</b>",""), "plain", "utf-8"))
    mail.attach(MIMEText(msg_content["html"], "html", "utf-8"))

    def _smtp_send():
        with smtplib.SMTP("smtp.gmail.com", 587) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(_sender, _pass)
            srv.sendmail(_sender, to_address, mail.as_string())

    try:
        await asyncio.get_event_loop().run_in_executor(None, _smtp_send)
        print(f"[NOTIFIER] ✅ Email → {to_address}")
        return {"ok": True, "channel": "email"}
    except smtplib.SMTPAuthenticationError:
        err = "Xác thực Gmail thất bại – kiểm tra lại App Password."
        print(f"[NOTIFIER] ❌ Email: {err}")
        return {"ok": False, "channel": "email", "error": err}
    except Exception as e:
        print(f"[NOTIFIER] ❌ Email exception: {e}")
        return {"ok": False, "channel": "email", "error": str(e)}


# ── dispatch_all: gọi từ AlertDispatcher trong module2.py ──────

async def dispatch_all_channels(houseid: str, violations: list,
                                  sensor_data: dict, channels_doc: dict,
                                  triggered_rules: list = None) -> list:
    tasks = []

    tg = channels_doc.get("telegram", {})
    if tg.get("enabled"):
        tasks.append(send_telegram(
            houseid, violations, sensor_data,
            bot_token=tg.get("bot_token") or None,
            chat_id  =tg.get("chat_id")   or None,
            triggered_rules=triggered_rules,
        ))

    em = channels_doc.get("email", {})
    if em.get("enabled") and em.get("address"):
        tasks.append(send_email(
            houseid, violations, sensor_data,
            to_address=em["address"],
            triggered_rules=triggered_rules,
        ))

    if not tasks:
        return []
    return await asyncio.gather(*tasks, return_exceptions=False)