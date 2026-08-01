#!/usr/bin/env python3
"""
mybedroom.travel — Auto Dashboard Updater
يشتغل كل يوم تلقائياً عبر GitHub Actions
يسحب بيانات Instagram من Windsor.ai ويحدّث الداشبورد
"""

import os
import json
import base64
import requests
import re
from datetime import datetime, timedelta

# ══ CONFIG ══════════════════════════════════════════════════════
WINDSOR_API_KEY = os.environ["WINDSOR_API_KEY"]          # من GitHub Secrets
INSTAGRAM_ACCOUNT = os.environ.get("IG_ACCOUNT_ID", "17841462763315127")
SUPABASE_URL = os.environ["SUPABASE_URL"]                # من GitHub Secrets
SUPABASE_KEY = os.environ["SUPABASE_KEY"]                # من GitHub Secrets

WINDSOR_BASE = "https://api.windsor.ai/v1/data"

# ══ STEP 1: جلب البيانات من Windsor.ai ══════════════════════════
def fetch_windsor():
    print("📡 جلب بيانات Instagram من Windsor.ai...")
    
    fields = [
        "date", "media_id", "media_caption", "media_type",
        "media_product_type", "media_views", "media_reach",
        "media_shares", "media_saved", "media_reel_total_interactions",
        "media_engagement", "media_permalink", "timestamp"
    ]
    
    payload = {
        "api_key": WINDSOR_API_KEY,
        "connector": "instagram",
        "accounts": [INSTAGRAM_ACCOUNT],
        "date_preset": "last_30d",
        "fields": fields
    }
    
    r = requests.post(WINDSOR_BASE, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    
    posts = data.get("data", [])
    print(f"✅ جُلب {len(posts)} منشور")
    return posts

# ══ STEP 2: معالجة البيانات ══════════════════════════════════════
def process_posts(raw_posts):
    print("⚙️ معالجة البيانات...")
    
    def clean(t):
        if not t:
            return ""
        return (t.replace('"','').replace("'",'').replace('`','')
                 .replace('\\','').replace('<','').replace('>',''))
    
    def get_cat(cap):
        cap = cap.lower()
        if any(x in cap for x in ['بودروم','vogue','bodrum','caresse','la blanche','hyde','plaza bodrum']):
            return 'bodrum'
        if any(x in cap for x in ['أطفال','نيكولوديون','nickel','لاند','land of legends','غرناطة','granada','ريكسوس بارك']):
            return 'kids'
        if 'فتحية' in cap:
            return 'fethiye'
        if any(x in cap for x in ['أنطاليا','بيليك','belek','ريكسوس بريميوم']):
            return 'antalya'
        if any(x in cap for x in ['إسطنبول','تقسيم','كاراكوي','moxy','aloft','maestro','ديديمان']):
            return 'istanbul'
        if any(x in cap for x in ['طرابزون','ريزة','شمال','اوزنجول']):
            return 'north'
        return 'other'
    
    def get_hook(cap):
        if any(x in cap for x in ['أكبر غلطة','أكبر خطأ','أكبر كذبة','أكبر مقلب','أكبر كابوس','تحذير','لا تحجز']):
            return 'warn'
        if any(x in cap for x in ['ليش تدفع','برأيك','من 1 إلى 10','مفكر','مفكرينها','أيش','كيف تقيّم']):
            return 'question'
        if any(x in cap for x in ['تخيل','سر','اكتشف']):
            return 'secret'
        if any(x in cap for x in ['آخر','لا تفوتك','يبدأ الموسم','بيطير']):
            return 'fomo'
        return 'other'
    
    processed = []
    for r in raw_posts:
        views = int(r.get("media_views") or r.get("media_reach") or 0)
        reach = int(r.get("media_reach") or 1)
        shares = int(r.get("media_shares") or 0)
        saved = int(r.get("media_saved") or 0)
        inter = int(r.get("media_reel_total_interactions") or r.get("media_engagement") or 0)
        cap = clean(r.get("media_caption") or "")
        eng = round(inter / reach * 100, 2) if reach > 0 else 0
        
        ts = r.get("timestamp") or ""
        try:
            hr = int(ts.split("T")[1].split(":")[0]) if "T" in ts else 0
        except:
            hr = 0
        
        processed.append({
            "date": r.get("date", "")[:10],
            "id": r.get("media_id", ""),
            "cap": cap,
            "type": r.get("media_product_type", "REELS"),
            "views": views,
            "reach": reach,
            "shares": shares,
            "saved": saved,
            "inter": inter,
            "eng": eng,
            "share_r": round(shares / reach * 100, 2) if reach > 0 else 0,
            "save_r": round(saved / reach * 100, 2) if reach > 0 else 0,
            "url": r.get("media_permalink", ""),
            "cat": get_cat(cap),
            "hook": get_hook(cap),
            "hr": hr,
        })
    
    # حساب الإحصائيات
    n = len(processed)
    if n == 0:
        return None
    
    total_views = sum(r["views"] for r in processed)
    total_shares = sum(r["shares"] for r in processed)
    total_saved = sum(r["saved"] for r in processed)
    total_inter = sum(r["inter"] for r in processed)
    avg_eng = round(sum(r["eng"] for r in processed) / n, 2)
    
    # إحصائيات الفئات
    cats = {}
    for r in processed:
        c = r["cat"]
        if c not in cats:
            cats[c] = {"n":0,"views":[],"eng":[],"shares":[],"saved":[]}
        cats[c]["n"] += 1
        cats[c]["views"].append(r["views"])
        cats[c]["eng"].append(r["eng"])
        cats[c]["shares"].append(r["shares"])
        cats[c]["saved"].append(r["saved"])
    
    cat_stats = {}
    for k, v in cats.items():
        cat_stats[k] = {
            "n": v["n"],
            "avg_views": round(sum(v["views"]) / len(v["views"])),
            "avg_eng": round(sum(v["eng"]) / len(v["eng"]), 2),
            "avg_shares": round(sum(v["shares"]) / len(v["shares"])),
            "avg_saved": round(sum(v["saved"]) / len(v["saved"])),
        }
    
    # إحصائيات الـ Hook
    hooks = {}
    for r in processed:
        h = r["hook"]
        if h not in hooks:
            hooks[h] = {"n":0,"eng":[]}
        hooks[h]["n"] += 1
        hooks[h]["eng"].append(r["eng"])
    
    hook_stats = {k: {"n":v["n"],"avg_eng":round(sum(v["eng"])/len(v["eng"]),2)} for k,v in hooks.items()}
    
    payload = {
        "posts": processed,
        "stats": {
            "n": n,
            "n_reels": len([r for r in processed if r["type"]=="REELS"]),
            "n_carousel": len([r for r in processed if r["type"]!="REELS"]),
            "total_views": total_views,
            "total_shares": total_shares,
            "total_saved": total_saved,
            "total_inter": total_inter,
            "avg_eng": avg_eng,
            "top_eng": max(r["eng"] for r in processed),
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        },
        "cat_stats": cat_stats,
        "hook_stats": hook_stats,
    }
    
    print(f"✅ معالجة {n} منشور | متوسط تفاعل: {avg_eng}% | إجمالي مشاهدات: {total_views:,}")
    return payload

# ══ STEP 3: حفظ في Supabase ══════════════════════════════════════
def save_to_supabase(payload):
    print("💾 حفظ في Supabase...")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
    }
    
    record = {
        "id": "mybedroom_latest",
        "data": json.dumps(payload, ensure_ascii=True),
        "updated_at": datetime.utcnow().isoformat(),
        "posts_count": payload["stats"]["n"],
        "avg_eng": payload["stats"]["avg_eng"],
        "total_views": payload["stats"]["total_views"],
    }
    
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/dashboard_data",
        headers=headers,
        json=record,
        timeout=30
    )
    
    if r.status_code in [200, 201]:
        print("✅ حُفظ في Supabase بنجاح")
        return True
    else:
        print(f"⚠️ Supabase error: {r.status_code} — {r.text}")
        # fallback: احفظ محلياً
        with open("dashboard_data.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=True)
        print("✅ حُفظ محلياً كـ fallback")
        return False

# ══ STEP 4: توليد HTML الداشبورد ══════════════════════════════
def build_dashboard(payload):
    print("🏗️ بناء الداشبورد...")
    
    b64 = base64.b64encode(
        json.dumps(payload, ensure_ascii=True).encode()
    ).decode("ascii")
    
    # قراءة template الداشبورد
    template_path = "dashboard_template.html"
    if not os.path.exists(template_path):
        print("⚠️ لم يجد dashboard_template.html — تخطي بناء HTML")
        return None
    
    with open(template_path, encoding="utf-8") as f:
        html = f.read()
    
    # حقن البيانات
    html = html.replace("XDATAX", b64)
    
    # حقن تاريخ التحديث
    html = html.replace(
        "آخر 30 يوم",
        f"آخر 30 يوم · آخر تحديث: {payload['stats']['updated_at']}"
    )
    
    output_path = "docs/index.html"
    os.makedirs("docs", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ الداشبورد جاهز: {output_path} ({len(html)//1024}KB)")
    return output_path

# ══ MAIN ═════════════════════════════════════════════════════════
def main():
    print("=" * 55)
    print("🛏️  mybedroom.travel — Auto Dashboard Updater")
    print(f"⏰  {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)
    
    try:
        # 1. جلب البيانات
        raw = fetch_windsor()
        if not raw:
            print("❌ لا توجد بيانات من Windsor")
            return 1
        
        # 2. معالجة
        payload = process_posts(raw)
        if not payload:
            print("❌ فشل في معالجة البيانات")
            return 1
        
        # 3. حفظ في Supabase
        save_to_supabase(payload)
        
        # 4. بناء الداشبورد
        build_dashboard(payload)
        
        print("\n" + "=" * 55)
        print("✅ تم بنجاح!")
        print(f"📊 {payload['stats']['n']} منشور")
        print(f"👁  {payload['stats']['total_views']:,} مشاهدة")
        print(f"💯 {payload['stats']['avg_eng']}% متوسط تفاعل")
        print("=" * 55)
        return 0
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
