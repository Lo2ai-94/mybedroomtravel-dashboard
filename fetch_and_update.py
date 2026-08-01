import os,json,base64,requests
from datetime import datetime,timedelta

WK=os.environ["WINDSOR_API_KEY"]
IG=os.environ.get("IG_ACCOUNT_ID","17841462763315127")
SU=os.environ["SUPABASE_URL"]
SK=os.environ["SUPABASE_KEY"]

def fetch():
    print("جلب البيانات...")
    today=datetime.utcnow()
    p={"api_key":WK,"connector":"instagram","date_from":(today-timedelta(days=30)).strftime("%Y-%m-%d"),"date_to":today.strftime("%Y-%m-%d"),"fields":"date,media_id,media_caption,media_type,media_product_type,media_views,media_reach,media_shares,media_saved,media_reel_total_interactions,media_permalink,timestamp","accounts":IG}
    r=requests.get("https://connectors.windsor.ai/instagram",params=p,timeout=120)
    print(f"Status:{r.status_code}")
    r.raise_for_status()
    d=r.json()
    posts=d if isinstance(d,list) else d.get("data",d.get("results",[]))
    print(f"جُلب {len(posts)} منشور")
    return posts

def cat(c):
    c=c.lower()
    if any(x in c for x in ['بودروم','vogue','bodrum','caresse','blanche','hyde','plaza']):return'bodrum'
    if any(x in c for x in ['أطفال','نيكولوديون','nickel','لاند','legends','غرناطة','granada']):return'kids'
    if'فتحية'in c:return'fethiye'
    if any(x in c for x in ['أنطاليا','بيليك','belek']):return'antalya'
    if any(x in c for x in ['إسطنبول','تقسيم','كاراكوي','moxy','aloft']):return'istanbul'
    return'other'

def hook(c):
    if any(x in c for x in ['أكبر غلطة','أكبر خطأ','تحذير','لا تحجز','مقلب','كابوس']):return'warn'
    if any(x in c for x in ['برأيك','من 1','أيش','كيف تقيّم','مفكر']):return'question'
    if any(x in c for x in ['آخر','لا تفوتك','بيطير']):return'fomo'
    if any(x in c for x in ['تخيل','سر']):return'secret'
    return'other'

def process(raw):
    out=[]
    for r in raw:
        try:
            reach=int(float(r.get("media_reach")or 1))or 1
            inter=int(float(r.get("media_reel_total_interactions")or 0))
            cap=str(r.get("media_caption")or"").replace('"','').replace("'",'').replace('<','').replace('>','')
            out.append({"date":str(r.get("date",""))[:10],"id":str(r.get("media_id","")),"cap":cap,"type":str(r.get("media_product_type","REELS")),"views":int(float(r.get("media_views")or 0)),"reach":reach,"shares":int(float(r.get("media_shares")or 0)),"saved":int(float(r.get("media_saved")or 0)),"inter":inter,"eng":round(inter/reach*100,2),"url":str(r.get("media_permalink","")),"cat":cat(cap),"hook":hook(cap)})
        except Exception as e:
            print(f"skip:{e}")
    if not out:return None
    n=len(out)
    cats={}
    for r in out:
        c=r["cat"]
        if c not in cats:cats[c]={"n":0,"views":[],"eng":[],"shares":[],"saved":[]}
        cats[c]["n"]+=1;cats[c]["views"].append(r["views"]);cats[c]["eng"].append(r["eng"]);cats[c]["shares"].append(r["shares"]);cats[c]["saved"].append(r["saved"])
    cs={k:{"n":v["n"],"avg_views":round(sum(v["views"])/len(v["views"])),"avg_eng":round(sum(v["eng"])/len(v["eng"]),2),"avg_shares":round(sum(v["shares"])/len(v["shares"])),"avg_saved":round(sum(v["saved"])/len(v["saved"]))} for k,v in cats.items()}
    hooks={}
    for r in out:
        h=r["hook"]
        if h not in hooks:hooks[h]={"n":0,"eng":[]}
        hooks[h]["n"]+=1;hooks[h]["eng"].append(r["eng"])
    hs={k:{"n":v["n"],"avg_eng":round(sum(v["eng"])/len(v["eng"]),2)} for k,v in hooks.items()}
    tv=sum(r["views"]for r in out)
    return{"posts":out,"stats":{"n":n,"n_reels":len([r for r in out if"REEL"in r["type"]]),"n_carousel":len([r for r in out if"REEL"not in r["type"]]),"total_views":tv,"total_shares":sum(r["shares"]for r in out),"total_saved":sum(r["saved"]for r in out),"total_inter":sum(r["inter"]for r in out),"avg_eng":round(sum(r["eng"]for r in out)/n,2),"top_eng":max(r["eng"]for r in out),"avg_views":round(tv/n),"updated_at":datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")},"cat_stats":cs,"hook_stats":hs}

def save(payload):
    h={"apikey":SK,"Authorization":f"Bearer {SK}","Content-Type":"application/json","Prefer":"resolution=merge-duplicates"}
    try:
        r=requests.post(f"{SU}/rest/v1/dashboard_data",headers=h,json={"id":"mybedroom_latest","data":json.dumps(payload,ensure_ascii=True),"updated_at":datetime.utcnow().isoformat(),"posts_count":payload["stats"]["n"],"avg_eng":payload["stats"]["avg_eng"],"total_views":payload["stats"]["total_views"]},timeout=30)
        print(f"Supabase:{r.status_code}")
    except Exception as e:
        print(f"Supabase err:{e}")
    json.dump(payload,open("dashboard_data.json","w"),ensure_ascii=True)

def build(payload):
    if not os.path.exists("dashboard_template.html"):return
    b64=base64.b64encode(json.dumps(payload,ensure_ascii=True).encode()).decode()
    html=open("dashboard_template.html",encoding="utf-8").read().replace("XDATAX",b64)
    os.makedirs("docs",exist_ok=True)
    open("docs/index.html","w",encoding="utf-8").write(html)
    print(f"Dashboard built: {len(html)//1024}KB")

raw=fetch()
if raw:
    p=process(raw)
    if p:
        save(p)
        build(p)
        print("✅ تم!")
    else:
        print("❌ فشل");exit(1)
else:
    print("❌ لا بيانات");exit(1)
