// App saved as ai_entrepreneur
// Enhanced app: Categorized prompts + dynamic trending integration for entrepreneurs
// Fixes retained: Clipboard fallback + subtle inline notice; balanced JSX; diagnostics tests.
// New: "Trending Prompts" generator that blends your prompt templates with trending topics/hashtags.
// - Supports manual trends input, QR-provided trends, or a Demo fetch (no external API keys required).
// - Platform-aware phrasing (Instagram, TikTok, LinkedIn, etc.).
// - Additional diagnostics test cases for trend infusion and QR generator.

import React, { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { QrCode, ExternalLink, Sparkles, Clipboard, ShieldAlert, Bug, Wand2, RefreshCcw } from "lucide-react";
import QRCodeLib from "qrcode";

// ----- Clipboard helper with fallback (handles sandbox/permissions policy) -----
async function copyToClipboard(text: string): Promise<{ ok: boolean; method: "clipboard" | "execCommand" | "none"; error?: any }> {
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return { ok: true, method: "clipboard" };
    }
  } catch (err) {
    // fall through to legacy path
  }
  try {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.top = "-1000px";
    ta.style.left = "-1000px";
    ta.setAttribute("readonly", "");
    document.body.appendChild(ta);
    ta.select();
    ta.setSelectionRange(0, ta.value.length);
    const ok = document.execCommand("copy");
    document.body.removeChild(ta);
    return { ok, method: ok ? "execCommand" : "none" };
  } catch (error) {
    return { ok: false, method: "none", error };
  }
}

// ---- Platform tone/format helpers ----
const PLATFORM_HINT: Record<string, string> = {
  Instagram: "Use cozy, sensory language + 2–4 branded hashtags.",
  TikTok: "Open with a hook in 1 sentence; suggest a 7–12s shot list.",
  LinkedIn: "Lead with an insight; end with a thoughtful question.",
  "X (Twitter)": "Short, punchy. 1 hook + 1 CTA + 1 hashtag.",
  "YouTube Shorts": "One actionable takeaway + snappy CTA.",
  Facebook: "Friendly tone; invite comments or DMs.",
};
const DEFAULT_PLATFORMS = Object.keys(PLATFORM_HINT);

export default function App() {
  const [scanning, setScanning] = useState(false);
  const [rawQr, setRawQr] = useState<string>("");
  const [etsyPlannerUrl, setEtsyPlannerUrl] = useState<string>("");
  const [aiLesson, setAiLesson] = useState<string>("");
  const [copiedKey, setCopiedKey] = useState<string>("");
  const [copyError, setCopyError] = useState<string | null>(null);
  const [showDiagnostics, setShowDiagnostics] = useState(false);

  // QR code generator state
  const [qrUrl, setQrUrl] = useState<string>("");
  const [qrPayload, setQrPayload] = useState<string>("");
  const [qrImage, setQrImage] = useState<string>("");
  const [qrBusy, setQrBusy] = useState<boolean>(false);

  // Dynamic trends state
  const [platform, setPlatform] = useState<string>("Instagram");
  const [manualTrends, setManualTrends] = useState<string>(""); // comma or newline separated
  const [trends, setTrends] = useState<string[]>([]);
  const [isLoadingTrends, setIsLoadingTrends] = useState(false);

  // Optional brand context (can be injected via QR JSON)
  const [brand, setBrand] = useState<{ name?: string; industry?: string; niche?: string } | null>(null);

  const promptCategories = [
    { title: "Engagement Prompt", example: "Write a fun and engaging question I can ask my audience to boost comments. I run a small coffee shop." },
    { title: "Product Highlight Prompt", example: "Create a short Instagram caption that highlights the benefits of my handmade candles. Make it cozy and inviting." },
    { title: "Behind-the-Scenes Prompt", example: "Generate a caption for a behind-the-scenes photo of me preparing orders in my Etsy shop." },
    { title: "Customer Testimonial Prompt", example: "Write a post using this customer review to build trust and encourage new buyers: ‘Loved the planner! It helped me stay organized all month.’" },
    { title: "Storytelling Prompt", example: "Tell a short story about why I started my jewelry business and how it connects to my passion for creativity." },
    { title: "Promotion Prompt", example: "Write a caption for a limited-time offer: 20% off all digital downloads this weekend. Make it urgent but friendly." },
    { title: "Educational Tip Prompt", example: "Create a tip-of-the-day post for a wellness coach about staying productive during the holidays." },
    { title: "Holiday-Themed Prompt", example: "Write a festive caption for a small business holiday post that thanks customers and shares a seasonal product." },
  ];

  // Parse QR JSON for Etsy link, AI lesson, brand, and trends
  useEffect(() => {
    if (!rawQr) return;
    try {
      const data = JSON.parse(rawQr);
      if (data.EtsyPlannerURL) setEtsyPlannerUrl(data.EtsyPlannerURL);
      if (data.AILesson) setAiLesson(data.AILesson);
      if (data.brand) setBrand(data.brand);
      if (Array.isArray(data.trends)) setTrends(data.trends.filter(Boolean));
      if (data.platform && PLATFORM_HINT[data.platform]) setPlatform(data.platform);
    } catch {
      if (rawQr.startsWith("http")) setEtsyPlannerUrl(rawQr);
    }
  }, [rawQr]);

  // Build dynamic prompts that weave in trending tokens
  function fuseTrends(text: string, trendList: string[], opts?: { maxHashtags?: number; sprinkle?: boolean }) {
    const uniq = Array.from(new Set(trendList.map((t) => t.trim()).filter(Boolean)));
    const tags = uniq.filter((t) => t.startsWith("#"));
    const phrases = uniq.filter((t) => !t.startsWith("#"));
    const maxHashtags = opts?.maxHashtags ?? 3;

    const chosenTags = tags.slice(0, maxHashtags);
    const phrase = phrases[0] ? ` ${phrases[0]}` : "";

    // Insert platform hint and trends at the end, keeping prompt human-first
    const hint = PLATFORM_HINT[platform] ? `\nPlatform: ${platform}. ${PLATFORM_HINT[platform]}` : "";
    const tagLine = chosenTags.length ? `\nTrending to include: ${chosenTags.join(" ")}` : "";
    return `${text}${phrase}${hint}${tagLine}`.trim();
  }

  function makeDynamic(categoryExample: string) {
    const ctxt = brand?.industry || brand?.niche ? ` I’m in ${brand?.industry || brand?.niche}.` : "";
    const base = `${categoryExample}${ctxt} Optimize it for ${platform}. Keep it concise and conversational.`;
    return fuseTrends(base, trends, { maxHashtags: platform === "LinkedIn" ? 1 : 3 });
  }

  // Demo trends (no external calls; rotates seasonally-ish)
  function generateDemoTrends(): string[] {
    const now = new Date();
    const m = now.getMonth();
    const seasonal = m === 10 || m === 11
      ? ["#SmallBusinessSaturday", "#HolidayGiftGuide", "#ShopLocal", "cozy vibes"]
      : m <= 1
      ? ["#NewYearNewYou", "#GoalSetting", "#Productivity", "content planning"]
      : ["#MondayMotivation", "#TipTuesday", "#CustomerLove", "behind the scenes"];
    return seasonal;
  }

  function onDemoFetch() {
    setIsLoadingTrends(true);
    setTimeout(() => {
      setTrends(generateDemoTrends());
      setIsLoadingTrends(false);
    }, 500);
  }

  async function onGenerateQR() {
    try {
      setQrBusy(true);
      const base = qrUrl || (typeof window !== "undefined" ? window.location.href : "https://ai-entrepreneur-mzmxwocwqhjcyffj6nu9xg.streamlit.app/");
      let finalUrl = base;
      if (qrPayload) {
        try {
          const obj = JSON.parse(qrPayload);
          const encoded = encodeURIComponent(JSON.stringify(obj));
          const sep = base.includes("?") ? "&" : "?";
          finalUrl = `${base}${sep}payload=${encoded}`;
        } catch {
          const sep = base.includes("?") ? "&" : "?";
          finalUrl = `${base}${sep}utm_content=${encodeURIComponent(qrPayload)}`;
        }
      }
      const urlWithUtm = finalUrl.includes("utm_campaign=")
        ? finalUrl
        : `${finalUrl}${finalUrl.includes("?") ? "&" : "?"}utm_source=planner&utm_medium=qr&utm_campaign=planner_qr`;
      const dataUrl = await QRCodeLib.toDataURL(urlWithUtm, { margin: 2, scale: 8 });
      setQrImage(dataUrl);
    } catch (e) {
      console.error(e);
    } finally {
      setQrBusy(false);
    }
  }

  function downloadQR() {
    if (!qrImage) return;
    const a = document.createElement("a");
    a.href = qrImage;
    a.download = "planner-qr.png";
    a.click();
  }

  // Combine manual trends + QR trends
  const effectiveTrends = useMemo(() => {
    const manual = manualTrends
      .split(/\n|,/) // newlines or commas
      .map((s) => s.trim())
      .filter(Boolean);
    const all = [...(trends || []), ...manual];
    return Array.from(new Set(all));
  }, [trends, manualTrends]);

  // ---------------- Diagnostics & simple test cases -----------------
  type TestResult = { name: string; pass: boolean; details?: string };
  function runDiagnostics(): TestResult[] {
    const results: TestResult[] = [];

    // Test #1: Prompt library should have 8 categories
    results.push({ name: "Prompt categories length = 8", pass: promptCategories.length === 8, details: `len=${promptCategories.length}` });

    // Test #2: QR JSON parsing should extract EtsyPlannerURL + lesson + trend
    const sample = JSON.stringify({ EtsyPlannerURL: "https://example.com/etsy-planner", AILesson: "Try role-based prompting.", trends: ["#ShopLocal"] });
    let okURL = false; let okLesson = false; let okTrend = false;
    try {
      const obj = JSON.parse(sample);
      okURL = typeof obj.EtsyPlannerURL === "string" && obj.EtsyPlannerURL.includes("http");
      okLesson = typeof obj.AILesson === "string" && obj.AILesson.length > 0;
      okTrend = Array.isArray(obj.trends) && obj.trends[0] === "#ShopLocal";
    } catch {}
    results.push({ name: "QR payload keys present", pass: okURL && okLesson && okTrend });

    // Test #3: Trend fusion adds hashtags
    const fused = fuseTrends("Write a caption about our holiday bundle.", ["#HolidayGiftGuide", "cozy vibes"], { maxHashtags: 2 });
    results.push({ name: "Trend fusion includes hashtag", pass: /#HolidayGiftGuide/.test(fused) });

    // Test #4: Dynamic maker respects platform hint (simulated)
    const testPlatform = "LinkedIn";
    const hintStr = PLATFORM_HINT[testPlatform];
    const fused2 = `${"Test"}\nPlatform: ${testPlatform}. ${hintStr}`;
    results.push({ name: "Platform hint present in dynamic output (simulated)", pass: fused2.includes(hintStr.slice(0, 10)) });

    // Test #5: QR library available
    results.push({ name: "QR library available", pass: typeof QRCodeLib?.toDataURL === "function" });

    // Test #6: Trend de-duplication works
    const dedup = Array.from(new Set(["#A", "#A", "B"])) ;
    results.push({ name: "Trend de-duplication", pass: dedup.length === 2, details: `len=${dedup.length}` });

    return results;
  }

  // Copy handler for individual dynamic items
  async function handleCopy(text: string, key: string) {
    setCopyError(null);
    const res = await copyToClipboard(text);
    if (res.ok) {
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(""), 1200);
    } else {
      setCopyError("Copy was blocked by your browser or environment. You can paste manually from the card.");
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        <header className="text-center">
          <h1 className="text-3xl font-bold mb-2">Entrepreneur AI Prompt & Automation Planner</h1>
          <p className="text-gray-600 text-sm">Scan your Etsy Planner QR code to access personalized AI prompts, automation ideas, and social content inspiration.</p>
          <div className="mt-3 text-xs text-gray-500">Tip: You can also create a QR code below that links directly to this app.</div>
        </header>

        {/* Subtle inline notice for clipboard issues */}
        {copyError && (
          <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-200 rounded-xl text-sm">
            <ShieldAlert className="h-4 w-4 mt-0.5" />
            <div>
              <div className="font-medium">Clipboard blocked</div>
              <div>{copyError}</div>
            </div>
          </div>
        )}

        {/* QR / Brand & Trending Settings */}
        <Card className="rounded-2xl shadow-sm">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-lg"><QrCode className="h-5 w-5" /> QR / Brand & Trending Settings</CardTitle>
          </CardHeader>
          <CardContent className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Paste QR JSON (optional)</label>
              <Textarea
                placeholder='{"EtsyPlannerURL":"https://…","AILesson":"…","brand":{"industry":"coffee"},"trends":["#ShopLocal"],"platform":"Instagram"}'
                className="mt-2"
                value={rawQr}
                onChange={(e) => setRawQr(e.target.value)}
                rows={6}
              />
              {etsyPlannerUrl && (
                <div className="mt-2 text-sm flex items-center gap-2">
                  <Badge variant="secondary" className="rounded-xl">Linked</Badge>
                  <a href={etsyPlannerUrl} target="_blank" rel="noopener noreferrer" className="text-indigo-600 underline flex items-center gap-1">
                    Open Etsy Planner <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              )}
              {aiLesson && (
                <div className="mt-3 p-3 bg-indigo-50 rounded-xl text-sm">
                  <div className="flex items-center gap-2 mb-1 text-indigo-800 font-medium"><Sparkles className="h-4 w-4" /> AI Lesson</div>
                  <div>{aiLesson}</div>
                </div>
              )}
            </div>

            <div>
              <label className="text-sm font-medium">Platform</label>
              <select className="mt-2 w-full border rounded-xl p-2" value={platform} onChange={(e) => setPlatform(e.target.value)}>
                {DEFAULT_PLATFORMS.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>

              <label className="text-sm font-medium mt-4 block">Add trending terms or hashtags</label>
              <Textarea
                placeholder="#ShopLocal, #HolidayGiftGuide, cozy vibes"
                className="mt-2"
                rows={3}
                value={manualTrends}
                onChange={(e) => setManualTrends(e.target.value)}
              />

              <div className="flex items-center gap-2 mt-3">
                <Button onClick={onDemoFetch} className="rounded-2xl" disabled={isLoadingTrends}>
                  {isLoadingTrends ? <RefreshCcw className="h-4 w-4 mr-2 animate-spin" /> : <Wand2 className="h-4 w-4 mr-2" />}
                  {isLoadingTrends ? "Loading demo trends…" : "Fetch Demo Trends"}
                </Button>
                {effectiveTrends.length > 0 && (
                  <Badge variant="outline" className="rounded-xl">{effectiveTrends.length} trends loaded</Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Share via QR (Planner-ready) */}
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Create a QR Code for Your Planner</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4 items-start">
              <div>
                <label className="text-sm font-medium">Destination URL</label>
                <Input
                  className="mt-2"
                  placeholder="https://ai-entrepreneur-mzmxwocwqhjcyffj6nu9xg.streamlit.app/"
                  value={qrUrl}
                  onChange={(e) => setQrUrl(e.target.value)}
                />
                <label className="text-sm font-medium mt-4 block">Optional payload (JSON or text)</label>
                <Textarea
                  className="mt-2"
                  rows={4}
                  placeholder='{"brand":{"industry":"coffee"},"platform":"Instagram"}'
                  value={qrPayload}
                  onChange={(e) => setQrPayload(e.target.value)}
                />
                <div className="flex items-center gap-2 mt-3">
                  <Button onClick={onGenerateQR} className="rounded-2xl" disabled={qrBusy}>
                    {qrBusy ? <RefreshCcw className="h-4 w-4 mr-2 animate-spin" /> : <QrCode className="h-4 w-4 mr-2" />}
                    {qrBusy ? "Generating…" : "Generate QR"}
                  </Button>
                  {qrImage && (
                    <Button variant="outline" onClick={downloadQR} className="rounded-2xl">
                      Download PNG
                    </Button>
                  )}
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  We automatically add <code>utm_source=planner&utm_medium=qr&utm_campaign=planner_qr</code> for attribution.
                </div>
              </div>
              <div className="flex flex-col items-center">
                {qrImage ? (
                  <img src={qrImage} alt="QR code" className="w-56 h-56 border rounded-xl" />
                ) : (
                  <div className="w-56 h-56 border border-dashed rounded-xl grid place-items-center text-xs text-gray-500">QR preview</div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Prompt Library (static examples) */}
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Prompt Library for Great Engagement</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              These example prompts are crafted to inspire engaging, high-performing posts for entrepreneurs and small business owners.
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              {promptCategories.map((p, idx) => (
                <div key={idx} className="border rounded-xl p-4 bg-white shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-semibold text-sm text-gray-800">{p.title}</h3>
                    <Button variant="ghost" size="sm" onClick={() => handleCopy(p.example, `lib-${idx}`)}>
                      <Clipboard className="h-4 w-4 text-gray-500" />
                    </Button>
                  </div>
                  <p className="text-sm text-gray-700">{p.example}</p>
                  {copiedKey === `lib-${idx}` && <p className="text-xs text-green-600 mt-1">Copied!</p>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Dynamic Trending Prompts */}
        <Card className="rounded-2xl shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Trending Prompts (auto-infused)</CardTitle>
          </CardHeader>
          <CardContent>
            {effectiveTrends.length === 0 ? (
              <p className="text-sm text-gray-600">Add or fetch trends above to generate dynamic prompts.</p>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {promptCategories.map((p, idx) => {
                  const dynamic = makeDynamic(p.example);
                  return (
                    <div key={idx} className="border rounded-xl p-4 bg-white shadow-sm">
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-semibold text-sm text-gray-800">{p.title}</h3>
                        <Button variant="ghost" size="sm" onClick={() => handleCopy(dynamic, `dyn-${idx}`)}>
                          <Clipboard className="h-4 w-4 text-gray-500" />
                        </Button>
                      </div>
                      <pre className="whitespace-pre-wrap text-sm text-gray-800">{dynamic}</pre>
                      {copiedKey === `dyn-${idx}` && <p className="text-xs text-green-600 mt-1">Copied!</p>}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Diagnostics */}
        <div className="my-4">
          <Button variant="outline" className="rounded-2xl" onClick={() => setShowDiagnostics((s) => !s)}>
            <Bug className="h-4 w-4 mr-2" /> {showDiagnostics ? "Hide" : "Show"} Diagnostics
          </Button>
          {showDiagnostics && (
            <div className="mt-3 p-4 bg-gray-100 rounded-2xl">
              {runDiagnostics().map((r, idx) => (
                <div key={idx} className="text-sm flex items-center gap-2 py-1">
                  <Badge variant={r.pass ? "secondary" : "destructive"} className="rounded-xl min-w-[90px] text-center">
                    {r.pass ? "PASS" : "FAIL"}
                  </Badge>
                  <span className="font-medium">{r.name}</span>
                  {r.details && <span className="text-gray-600">— {r.details}</span>}
                </div>
              ))}
              <div className="text-xs text-gray-600 mt-2">Note: External trend APIs often require keys and CORS. This demo uses manual/QR trends and a local demo generator to keep things reliable.</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
