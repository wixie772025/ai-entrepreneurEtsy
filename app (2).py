# .streamlit/config.toml
[runner]
python_version = "3.10"

import json
import io
import base64
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

import streamlit as st
from pydantic import BaseModel, ValidationError, Field
import pandas as pd
from dateutil.relativedelta import relativedelta
import qrcode
from PIL import Image

# Optional: QR decode from uploaded images
try:
    from pyzbar.pyzbar import decode as qr_decode  # type: ignore
    _HAS_PYZBAR = True
except Exception:
    _HAS_PYZBAR = False

APP_TITLE = "AI Entrepreneur – Weekly Prompt Generator"

PLATFORM_HINT: Dict[str, str] = {
    "Instagram": "Use cozy, sensory language + 2–4 branded hashtags.",
    "TikTok": "Open with a hook in 1 sentence; suggest a 7–12s shot list.",
    "LinkedIn": "Lead with an insight; end with a thoughtful question.",
    "X (Twitter)": "Short, punchy. 1 hook + 1 CTA + 1 hashtag.",
    "YouTube Shorts": "One actionable takeaway + snappy CTA.",
    "Facebook": "Friendly tone; invite comments or DMs.",
}
SUPPORTED_PLATFORMS = list(PLATFORM_HINT.keys())

PROMPT_CATEGORIES: List[Tuple[str, str]] = [
    ("Engagement Prompt", "Write a fun and engaging question I can ask my audience to boost comments. I run a small coffee shop."),
    ("Product Highlight Prompt", "Create a short Instagram caption that highlights the benefits of my handmade candles. Make it cozy and inviting."),
    ("Behind-the-Scenes Prompt", "Generate a caption for a behind-the-scenes photo of me preparing orders in my Etsy shop."),
    ("Customer Testimonial Prompt", "Write a post using this customer review to build trust and encourage new buyers: ‘Loved the planner! It helped me stay organized all month.’"),
    ("Storytelling Prompt", "Tell a short story about why I started my jewelry business and how it connects to my passion for creativity."),
    ("Promotion Prompt", "Write a caption for a limited-time offer: 20% off all digital downloads this weekend. Make it urgent but friendly."),
    ("Educational Tip Prompt", "Create a tip-of-the-day post for a wellness coach about staying productive during the holidays."),
    ("Holiday-Themed Prompt", "Write a festive caption for a small business holiday post that thanks customers and shares a seasonal product."),
]

AUTOMATIONS = [
    ("Lead Capture → CRM", "Auto‑push leads from website forms into your CRM and assign follow‑ups.", "Zapier/Make; HubSpot/Pipedrive"),
    ("DMs → Helpdesk", "Convert Instagram/FB DMs with keywords into support tickets or sales tasks.", "Zapier; Intercom/Help Scout"),
    ("Content Calendar", "Queue posts for the week; auto‑repurpose long posts to Shorts/Reels/Threads.", "Buffer/Later/Hootsuite; Repurpose.io"),
    ("Invoice & Bookkeeping", "Auto‑send invoices and sync payments to your books.", "QuickBooks/Xero; Stripe/Square"),
    ("Meeting Scheduling", "Auto‑route bookings and send reminders.", "Calendly/TidyCal; Google Calendar"),
    ("Email Nurture", "Welcome new leads with a 5‑email sequence; tag by interest.", "Mailchimp/Beehiiv; ConvertKit"),
    ("Task Intake", "Turn form or email requests into tasks with due dates and owners.", "Asana/ClickUp; Zapier"),
    ("Sales Pipeline Alerts", "Notify Slack when a deal moves stage or sits idle 7 days.", "Slack; HubSpot/Zapier"),
]

class Brand(BaseModel):
    industry: Optional[str] = None
    niche: Optional[str] = None

class QrPayload(BaseModel):
    EtsyPlannerURL: Optional[str] = None
    AILesson: Optional[str] = None
    brand: Optional[Brand] = None
    trends: Optional[List[str]] = None
    platform: Optional[str] = Field(default=None, description="One of supported platforms")

# ---------- Utilities ----------

def start_of_week(d: date) -> date:
    # Monday as first day
    return d - timedelta(days=(d.weekday()))

def seeded_random(seed_str: str) -> int:
    # Simple deterministic hash to choose items
    return abs(hash(seed_str))


def fuse_trends(text: str, platform: str, trend_list: List[str], max_hashtags: int = 3) -> str:
    trend_list = [t.strip() for t in trend_list if str(t).strip()]
    uniq = []
    for t in trend_list:
        if t not in uniq:
            uniq.append(t)
    tags = [t for t in uniq if t.startswith("#")]
    phrases = [t for t in uniq if not t.startswith("#")]
    chosen_tags = tags[: (1 if platform == "LinkedIn" else max_hashtags)]
    phrase = f" {phrases[0]}" if phrases else ""
    hint = f"\\nPlatform: {platform}. {PLATFORM_HINT.get(platform, '')}".strip()
    tag_line = f"\\nTrending to include: {' '.join(chosen_tags)}" if chosen_tags else ""
    return (text + phrase + ("\\n" + hint if hint else "") + tag_line).strip()


def demo_trends(today: Optional[date] = None) -> List[str]:
    today = today or date.today()
    m = today.month
    if m in (11, 12):
        return ["#SmallBusinessSaturday", "#HolidayGiftGuide", "#ShopLocal", "cozy vibes"]
    if m in (1, 2):
        return ["#NewYearNewYou", "#GoalSetting", "#Productivity", "content planning"]
    return ["#MondayMotivation", "#TipTuesday", "#CustomerLove", "behind the scenes"]


def make_dynamic(base_prompt: str, platform: str, brand: Optional[Brand], trends: List[str]) -> str:
    context = ""
    if brand and (brand.industry or brand.niche):
        context = f" I’m in {brand.industry or brand.niche}."
    base = f"{base_prompt}{context} Optimize it for {platform}. Keep it concise and conversational."
    return fuse_trends(base, platform, trends)


def choose(lst: List[Any], idx: int) -> Any:
    if not lst:
        return None
    return lst[idx % len(lst)]


def build_weekly_plan(payload: Dict[str, Any], week_start: date, platform: str, trends: List[str]) -> Dict[str, Any]:
    # Deterministic plan selection based on payload + week
    seed = seeded_random(json.dumps(payload, sort_keys=True) + week_start.isoformat())
    days = []
    weekday_themes = [
        ("Motivation Monday", "Share founder story or mission"),
        ("Tip Tuesday", "Quick, high‑value tactical tip"),
        ("Win Wednesday", "Show progress / case study"),
        ("Tutorial Thursday", "Mini how‑to with steps"),
        ("FAQ Friday", "Answer a common objection"),
        ("Social Proof Saturday", "Testimonial / UGC"),
        ("Planning Sunday", "Goals & CTA for next week"),
    ]
    for i in range(7):
        d = week_start + timedelta(days=i)
        cat = PROMPT_CATEGORIES[(seed + i) % len(PROMPT_CATEGORIES)]
        auto = AUTOMATIONS[(seed // 7 + i) % len(AUTOMATIONS)]
        dynamic = make_dynamic(cat[1], platform, Brand(**payload.get("brand", {})) if payload.get("brand") else None, trends)
        days.append({
            "date": d.isoformat(),
            "theme": weekday_themes[i][0],
            "platform": platform,
            "prompt_title": cat[0],
            "prompt": dynamic,
            "automation_title": auto[0],
            "automation_idea": auto[1],
            "tools": auto[2],
        })
    return {"meta": {"week_start": week_start.isoformat(), "platform": platform}, "days": days}


def plan_to_csv(plan: Dict[str, Any]) -> str:
    rows = []
    headers = ["Date","Theme","Platform","Hook","Prompt","Automation Title","Automation Idea","Tools"]
    for d in plan["days"]:
        rows.append([
            d["date"],
            d["theme"],
            d["platform"],
            d["prompt_title"],
            d["prompt"].replace("\\n", " "),
            d["automation_title"],
            d["automation_idea"],
            d["tools"],
        ])
    df = pd.DataFrame(rows, columns=headers)
    return df.to_csv(index=False)


def png_bytes_from_qr(data: str, scale: int = 6, border: int = 2) -> bytes:
    qr = qrcode.QRCode(version=None, box_size=scale, border=border)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = io.BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


def decode_qr_image(img: Image.Image) -> Optional[str]:
    if not _HAS_PYZBAR:
        return None
    try:
        res = qr_decode(img)
        if not res:
            return None
        return res[0].data.decode("utf-8")
    except Exception:
        return None

# ---------- UI ----------

st.set_page_config(page_title=APP_TITLE, page_icon="📅", layout="wide")
st.title(APP_TITLE)
st.write("Generate weekly, high‑engagement social prompts and simple automations. Supports QR payloads, platform‑aware phrasing, trends, CSV export, and planner‑ready QR codes.")

with st.expander("How it works"):
    st.markdown("""
1) Paste QR JSON or upload a QR image from your planner.  
2) Pick a platform and add trends (or fetch demo trends).  
3) Use the Prompt Library or generate **Trending Prompts**.  
4) Build your **Weekly Planner** and **Export CSV**.  
5) Create and download a **QR Code** that links to this app (with optional payload).
""")

# --- QR / Brand / Context ---
st.subheader("QR / Brand & Trending Settings")
col_a, col_b = st.columns(2)

with col_a:
    payload_text = st.text_area(
        "Paste QR JSON (optional)",
        height=160,
        placeholder='{"EtsyPlannerURL":"https://…","AILesson":"…","brand":{"industry":"coffee"},"trends":["#ShopLocal"],"platform":"Instagram"}',
    )

    uploaded = st.file_uploader("Or upload QR image (PNG/JPG)", type=["png","jpg","jpeg"])
    decoded_text = None
    if uploaded is not None:
        try:
            img = Image.open(uploaded)
            decoded_text = decode_qr_image(img)
            if decoded_text:
                st.success("QR decoded from image.")
                payload_text = decoded_text
            else:
                if _HAS_PYZBAR:
                    st.warning("No QR found in the uploaded image.")
                else:
                    st.info("QR decoding not available (pyzbar missing). Paste JSON instead.")
        except Exception as e:
            st.error(f"Failed to read image: {e}")

    payload: Dict[str, Any] = {}
    parsed: Optional[QrPayload] = None
    if payload_text:
        try:
            payload = json.loads(payload_text)
            parsed = QrPayload(**payload)
            st.success("QR payload parsed.")
            if parsed.EtsyPlannerURL:
                st.markdown(f"[Open Etsy Planner]({parsed.EtsyPlannerURL})")
            if parsed.AILesson:
                st.info(f"AI Lesson: {parsed.AILesson}")
        except (json.JSONDecodeError, ValidationError) as e:
            st.error(f"Invalid QR JSON or schema: {e}")

with col_b:
    platform = st.selectbox("Platform", SUPPORTED_PLATFORMS, index=SUPPORTED_PLATFORMS.index(parsed.platform) if parsed and parsed.platform in SUPPORTED_PLATFORMS else 0)
    manual_trends = st.text_area("Add trending terms or hashtags", placeholder="#ShopLocal, #HolidayGiftGuide, cozy vibes", height=80)
    trends: List[str] = []
    if parsed and parsed.trends:
        trends += parsed.trends
    if manual_trends:
        trends += [s.strip() for s in manual_trends.replace("\n", ",").split(",")]
    # dedup
    trends = [t for i, t in enumerate(trends) if t and t not in trends[:i]]

    if st.button("Fetch Demo Trends"):
        trends = demo_trends()

    if trends:
        st.caption(f"{len(trends)} trends loaded")
        st.write(", ".join(trends))

# --- Prompt Library ---
st.subheader("Prompt Library (static examples)")
lib_cols = st.columns(2)
for i, (title, example) in enumerate(PROMPT_CATEGORIES):
    with lib_cols[i % 2]:
        st.markdown(f"**{title}**")
        st.write(example)
        st.download_button("Download .txt", data=example.encode("utf-8"), file_name=f"{title.replace(' ','_').lower()}.txt", mime="text/plain")

# --- Dynamic / Trending Prompts ---
st.subheader("Trending Prompts (auto‑infused)")
if not trends:
    st.info("Add or fetch trends above to generate dynamic prompts.")
else:
    dyn_cols = st.columns(2)
    for i, (title, example) in enumerate(PROMPT_CATEGORIES):
        dynamic = make_dynamic(example, platform, parsed.brand if parsed and parsed.brand else None, trends)
        with dyn_cols[i % 2]:
            st.markdown(f"**{title}**")
            st.code(dynamic)
            st.download_button("Download .txt", data=dynamic.encode("utf-8"), file_name=f"{title.replace(' ','_').lower()}_dynamic.txt", mime="text/plain")

# --- Weekly Planner & CSV ---
st.subheader("Weekly Planner")
week_input = st.date_input("Week of (snaps to Monday)", value=start_of_week(date.today()))
week_start = start_of_week(week_input if isinstance(week_input, date) else week_input.date())
plan = build_weekly_plan(payload, week_start, platform, trends or [])
df_plan = pd.DataFrame(plan["days"])
st.dataframe(df_plan[["date","theme","platform","prompt_title","prompt","automation_title","automation_idea","tools"]], use_container_width=True)

csv_str = plan_to_csv(plan)
st.download_button("Export CSV", data=csv_str.encode("utf-8"), file_name=f"weekly_prompts_{week_start.isoformat()}.csv", mime="text/csv")

# --- QR Code Generator ---
st.subheader("Create a QR Code for Your Planner")
dest = st.text_input("Destination URL", value="https://ai-entrepreneur-mzmxwocwqhjcyffj6nu9xg.streamlit.app/")
qr_payload_text = st.text_area("Optional payload (JSON or text)")

final_url = dest
if qr_payload_text:
    try:
        obj = json.loads(qr_payload_text)
        encoded = json.dumps(obj, separators=(",",":"))
        final_url += ("&" if "?" in dest else "?") + "payload=" + st.experimental_uri.encode_component(encoded) if hasattr(st.experimental_uri, "encode_component") else ("&" if "?" in dest else "?") + "payload=" + base64.urlsafe_b64encode(encoded.encode()).decode()
    except Exception:
        final_url += ("&" if "?" in dest else "?") + "utm_content=" + base64.urlsafe_b64encode(qr_payload_text.encode()).decode()

if "utm_campaign=" not in final_url:
    final_url += ("&" if "?" in final_url else "?") + "utm_source=planner&utm_medium=qr&utm_campaign=planner_qr"

qr_png = png_bytes_from_qr(final_url)
st.image(qr_png, caption="Planner QR (PNG)", width=220)
st.download_button("Download QR PNG", data=qr_png, file_name="planner-qr.png", mime="image/png")
st.code(final_url, language="text")

# --- Diagnostics ---
st.subheader("Diagnostics")
tests: List[Tuple[str, bool, Optional[str]]] = []
tests.append(("Prompt library length = 8", len(PROMPT_CATEGORIES) == 8, f"len={len(PROMPT_CATEGORIES)}"))
tests.append(("QR payload schema parse (optional)", True if (not payload_text or parsed is not None) else False, None))
tests.append(("Trend fusion includes hashtag (simulated)", "#HolidayGiftGuide" in fuse_trends("Test", platform, ["#HolidayGiftGuide"]), None))
tests.append(("Platform hint present (simulated)", "Platform:" in fuse_trends("Test", "LinkedIn", []), None))
tests.append(("Trend de-duplication", len(list(dict.fromkeys(["#A", "#A", "B"]))) == 2, None))
tests.append(("Weekly CSV header + 7 rows", csv_str.count("\\n") == 7, f"rows={csv_str.count('\\n')}"))
# QR generator smoke test
try:
    _ = png_bytes_from_qr("https://example.com")
    tests.append(("QR generator produces PNG", True, None))
except Exception as e:
    tests.append(("QR generator produces PNG", False, str(e)))

for name, ok, detail in tests:
    st.write(("✅" if ok else "❌") + f" {name}" + (f" — {detail}" if detail else ""))
