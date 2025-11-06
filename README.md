Build a Streamlit App: AI Entrepreneur – Weekly Prompt Generator

Goal
Create a production-ready Streamlit app that helps entrepreneurs generate weekly, high-engagement social prompts and simple business automations. The app should support QR payloads, trending infusion, platform-aware phrasing, and a QR code generator to link back to the app or an Etsy planner page.

Tech Stack & Libraries

Python 3.10+

streamlit (UI)

pydantic (input/validation)

pandas (data handling, CSV export)

qrcode (QR code generation)

Pillow (image handling)

pyzbar (optional; decode uploaded QR images; handle absence gracefully)

python-dateutil (date utilities)

pytest (unit tests)

(Optional) requests for future trend APIs (stub now; feature-gated by env vars)

App Requirements
1) Header & Onboarding

App title: AI Entrepreneur – Weekly Prompt Generator

Short description: what it does (weekly prompts + automation ideas).

Non-blocking “How it works” collapsible panel.

2) QR & Brand/Context Input

Paste QR JSON text area. Example schema:

{
  "EtsyPlannerURL": "https://your-etsy-link",
  "AILesson": "Batch prompts with role, context, examples, and constraints.",
  "brand": {"industry": "coffee", "niche": "local café"},
  "trends": ["#SmallBusinessSaturday", "#HolidayGiftGuide", "cozy vibes"],
  "platform": "Instagram"
}


OR optional Upload QR image (PNG/JPG). If pyzbar is installed, decode it into text; otherwise, show a gentle note that decoding is unavailable and fallback to manual paste.

Extract and display detected fields with validation (Pydantic):

Etsy planner link (with “Open in new tab” link)

AI lesson (text)

Brand (industry/niche)

Platform (must be in supported list below)

Trends (list)

3) Platform-Aware Hints

Supported platforms: Instagram, TikTok, LinkedIn, X (Twitter), YouTube Shorts, Facebook

Internal dictionary of platform hints (e.g., LinkedIn = “lead with an insight; end with a question”).

Dropdown to choose platform; default to QR payload platform or Instagram.

4) Prompt Library (Static Examples)

Provide 8 preset examples (verbatim):

Engagement Prompt
“Write a fun and engaging question I can ask my audience to boost comments. I run a small coffee shop.”

Product Highlight Prompt
“Create a short Instagram caption that highlights the benefits of my handmade candles. Make it cozy and inviting.”

Behind-the-Scenes Prompt
“Generate a caption for a behind-the-scenes photo of me preparing orders in my Etsy shop.”

Customer Testimonial Prompt
“Write a post using this customer review to build trust and encourage new buyers: ‘Loved the planner! It helped me stay organized all month.’”

Storytelling Prompt
“Tell a short story about why I started my jewelry business and how it connects to my passion for creativity.”

Promotion Prompt
“Write a caption for a limited-time offer: 20% off all digital downloads this weekend. Make it urgent but friendly.”

Educational Tip Prompt
“Create a tip-of-the-day post for a wellness coach about staying productive during the holidays.”

Holiday-Themed Prompt
“Write a festive caption for a small business holiday post that thanks customers and shares a seasonal product.”

Each card shows the prompt and a Copy button. Because clipboard can be sandboxed, implement:

Primary: a Download .txt button that saves the prompt text.

Secondary: a Copy button that tries JS clipboard via st.components.v1.html (gracefully fails; show subtle inline notice if blocked).

5) Dynamic “Trending Prompts”

Inputs:

Manual trends input (textarea; comma or newline separated).

Incorporated QR trends list.

Fetch Demo Trends button (season-aware demo list; NO external calls).

Fusion logic:

Deduplicate trends.

Separate hashtags vs phrases. Limit hashtags to 3 (or 1 for LinkedIn).

Append: Platform: <name>. <platform_hint>.

Append: Trending to include: <#a #b #c>.

Include optional brand context sentence if present: I’m in <industry|niche>.

Generate dynamic versions for the same 8 categories above.

Provide Download .txt and Copy (with fallback) per generated prompt.

6) Weekly Planner & CSV Export

Weekly grid (Mon–Sun) that shows for each day:

A themed suggestion label (e.g., Motivation Monday, etc.)

A generated prompt (choose one dynamic category per day; seeded deterministically by week start + payload)

An Automation idea (rotate from a small catalog; e.g., lead capture→CRM with Zapier/HubSpot; DM→helpdesk; scheduling; nurture; content calendar; bookkeeping)

“Week of” date picker (defaults to current week; snaps to Monday).

Export CSV with headers:
Date, Theme, Platform, Hook, Prompt, Automation Title, Automation Idea, Tools

7) QR Code Generator (Planner-Ready)

Inputs:

Destination URL (default your Streamlit deployment URL: https://ai-entrepreneur-mzmxwocwqhjcyffj6nu9xg.streamlit.app/)

Optional payload (JSON or text). If JSON, append as ?payload=<encoded>. If text, append utm_content=<encoded>.

Always add UTM parameters if not present:
utm_source=planner&utm_medium=qr&utm_campaign=planner_qr

Show generated QR as an image and a Download PNG button.

8) Diagnostics (Toggle)

Show a section with PASS/FAIL badges for these tests:

Prompt library length == 8

QR payload keys present (EtsyPlannerURL + AILesson + trends)

Trend fusion includes at least one hashtag

Platform hint present in fused prompt (simulated)

QR library available

Trend de-duplication works

Weekly CSV has header + 7 rows for any chosen week

9) Structure & Files

Create a minimal repo layout:

ai_entrepreneur/
├─ app.py               # Streamlit entry
├─ utils.py             # fusion logic, weekly plan, CSV/TXT helpers, QR helpers
├─ components.py        # small UI helpers (copy/download blocks)
├─ requirements.txt     # pin libs
├─ tests/
│  └─ test_utils.py     # pytest unit tests (see below)
└─ README.md            # run instructions

10) Unit Tests (pytest)

In tests/test_utils.py, add tests (don’t remove any; add more if missing):

test_prompt_library_len_is_8()

test_qr_payload_validation_keys_present()

test_fuse_trends_includes_hashtag()

test_platform_hint_injected()

test_dedup_trends()

test_weekly_csv_has_8_rows() (header + 7 days)

test_qr_generator_produces_data_url() (or returns PNG bytes)

If pyzbar is not available in CI, skip the QR decode test with a marker.

11) UX Notes

Use a subtle inline notice (amber banner) for clipboard failures (no modal).

Keep copy/download actions near each prompt; also allow Download All .txt and Export CSV for weekly plan.

Persist user inputs in st.session_state.

Keep content concise and friendly.

12) Determinism

Seed prompt selection per day using: seed = hash(qr_payload_as_string + week_start_iso_date).

Same payload + week → same prompts/automation for reproducibility.

13) README.md

Install: pip install -r requirements.txt

Run: streamlit run app.py

Notes on optional pyzbar (and OS packages) for QR decoding of uploaded images.

Environment variable placeholders for future real trend API integrations.

14) Requirements.txt (pin reasonable versions)
streamlit
pydantic
pandas
qrcode
Pillow
python-dateutil
pytest
pyzbar; platform_system != "Windows"  # optional; handle gracefully if missing

15) Nice-to-Haves (if time permits)

Provide a small “AI Lesson of the Week” panel if AILesson present.

Allow saving a planner “preset” JSON and downloading it.

Add a “Duplicate to next week” helper that shifts dates + keeps trends.

IMPORTANT:

Handle missing libraries gracefully (e.g., pyzbar absent → show friendly fallback).

Don’t rely on external trend APIs; only demo trends + manual input for now.

Include unit tests listed above. Never delete tests; only add more if needed.
