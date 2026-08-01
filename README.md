# 🛏️ mybedroom.travel — Auto Dashboard

داشبورد يتحدث **تلقائياً كل يوم** من بيانات Instagram الحقيقية.

## 🗺️ كيف يشتغل

```
كل يوم 6:00 ص
    ↓
GitHub Action يشتغل
    ↓
يسحب بيانات Instagram من Windsor.ai
    ↓
يحدّث Supabase + يبني HTML جديد
    ↓
يرفع الداشبورد على GitHub Pages
    ↓
رابطك يفتح الداشبورد المحدّث 🎉
```

---

## ⚡ خطوات الإعداد (مرة واحدة فقط)

### الخطوة ١ — Supabase (5 دقائق)
1. روح [supabase.com](https://supabase.com) → Create New Project
2. اسم المشروع: `mybedroom-dashboard`
3. بعد الإنشاء → SQL Editor → انسخ محتوى `supabase_setup.sql` وشغّله
4. روح Settings → API → انسخ:
   - **Project URL** → هذا `SUPABASE_URL`
   - **service_role key** → هذا `SUPABASE_KEY`

### الخطوة ٢ — GitHub Repository (5 دقائق)
1. أنشئ Repo جديد اسمه `mybedroom-dashboard`
2. ارفع كل الملفات من هذا الزيب
3. Settings → Pages → Source: `GitHub Actions`

### الخطوة ٣ — Secrets (3 دقائق)
في GitHub Repo → Settings → Secrets → Actions:

| الاسم | القيمة |
|-------|--------|
| `WINDSOR_API_KEY` | `ed4a6ffaa6b4b0511ffb6cf7582b38a8782d` |
| `IG_ACCOUNT_ID` | `17841462763315127` |
| `SUPABASE_URL` | من خطوة ١ |
| `SUPABASE_KEY` | من خطوة ١ |

### الخطوة ٤ — تشغيل أول مرة
1. Actions → "Update Dashboard Daily" → Run workflow
2. انتظر 2-3 دقائق
3. رابطك: `https://USERNAME.github.io/mybedroom-dashboard`

---

## 📅 الجدول التلقائي
- كل يوم الساعة **6:00 صباحاً** تلقائياً
- أو اضغط "Run workflow" متى تريد

## 💰 التكلفة
| الخدمة | التكلفة |
|--------|---------|
| GitHub Actions | مجاني (2000 دقيقة/شهر) |
| GitHub Pages | مجاني |
| Supabase | مجاني (500MB) |
| **المجموع** | **$0** |

