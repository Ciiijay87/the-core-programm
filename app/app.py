# THE CORE PROGRAMM – Vollversion (v2.4 extra-robust)
# • Deutsche Übungsbibliothek: app/data/exercises_user.csv
# • Robustes CSV-Laden (Komma/Semikolon, Smart-Quotes, kaputte Zeilen)
# • Erzwingt Pflichtspalten (name, category, environment, positions, levels, …)
# • Tabs (4 Wochen), Caps, PDF-Export, RPE-Erklärung + Reserve-Hinweis

import csv, re, io
from pathlib import Path
from io import BytesIO
import streamlit as st
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)

def write_csv(path: Path, header: list, rows: list):
    if not path.exists():
        with open(path,"w",encoding="utf-8",newline="") as f:
            w = csv.writer(f); w.writerow(header); w.writerows(rows)

# ---------- Defaults (falls Dateien fehlen) ----------
DEFAULT_PERIODIZATION = [
    ("postseason","Postseason","1115","1231","1;2","Recovery/ROM","0","0","RPE5–6, Technik","Walk/Bike/Flow"),
    ("off_foundation","Offseason Foundation","1101","1231","2;3","Basics/Hypertrophie","10","4","RPE6–7, Volumen↑","Tempo Runs/leicht"),
    ("off_strength","Offseason Strength","0101","0228","2;3","Maxkraft","12","6","RPE7–8, schwere Lifts","Shuttles moderat"),
    ("off_power","Offseason Power","0301","0430","2;3","Power/Speed","18","10","RPE6–8, Contrast","30:30 / Repeat Sprint"),
    ("preseason","Preseason","0501","0630","2","Game-like","15","8","Maint. RPE6–7","110s/Gassers/300yd"),
    ("inseason","Inseason","0901","1031","1;2","Erhalt/Frisch","8","4","kurz & scharf RPE6–7","Sehr dosiert"),
]
DEFAULT_POSITIONS = [
    ("OL",0.40,0.20,0.10,0.10,0.10,0.10,"Kollision/Kraft, kurze Accel"),
    ("DL",0.40,0.20,0.10,0.10,0.10,0.10,"Kollision/Kraft, kurze Accel"),
    ("LB",0.30,0.20,0.15,0.15,0.10,0.10,"Hybrid"),
    ("TE",0.30,0.20,0.15,0.15,0.10,0.10,"Hybrid Lineman/Skill"),
    ("WR",0.20,0.20,0.25,0.20,0.10,0.05,"Speed/COD, Hamstrings"),
    ("DB",0.20,0.20,0.25,0.20,0.10,0.05,"Speed/COD, Hamstrings"),
    ("RB",0.25,0.20,0.25,0.15,0.10,0.05,"Accel/COD, Hip"),
    ("QB",0.20,0.15,0.10,0.10,0.10,0.35,"Core/Mobility/Arm-care"),
    ("KP",0.15,0.15,0.10,0.10,0.15,0.35,"Bein-Explosiv/Balance"),
]
DEFAULT_LEVELS = [
    ("Rookie",0.85,0.85,"basic",0.70,0.70),
    ("Advanced",0.95,1.00,"std",1.00,1.00),
    ("Pro",1.00,1.10,"advanced",1.20,1.15),
    ("Elite",1.05,1.20,"elite",1.30,1.25),
]
DEFAULT_WUCD = [
    ("warmup","ALL","RAMP Warm-up","Jumping Jacks 2x20|Hip Circles 2x8|Glute Bridge 2x10|Monster Walk 2x10|A-Skips 2x20m"),
    ("cooldown","ALL","Light Stretch","Hip Flexor 60s|Hamstring 60s|Calf 60s|T-Spine Rotation 10/10"),
]
DEFAULT_TEMPLATES = [
    ("off_foundation",2,"OF2_A","WarmUp|Plyo:low|Strength:lower|Strength:upper|Accessory|Accessory|Core/Prehab|Mobility|CoolDown"),
    ("off_foundation",2,"OF2_B","WarmUp|Strength:main|Accessory|Accessory|Speed/Agility|Conditioning|Core/Prehab|CoolDown"),
    ("off_foundation",3,"OF3_A","WarmUp|Plyo:low|Power|Strength:lower|Accessory|Accessory|Core/Prehab|CoolDown"),
    ("off_foundation",3,"OF3_B","WarmUp|Strength:upper|Accessory|Accessory|Core/Prehab|Mobility|CoolDown"),
    ("off_foundation",3,"OF3_C","WarmUp|Speed/Agility|Conditioning|Accessory|Core/Prehab|Mobility|CoolDown"),
    ("off_strength",2,"OS2_A","WarmUp|Plyo:low|Strength:lower|Strength:upper|Accessory|Accessory|Core/Prehab|CoolDown"),
    ("off_strength",2,"OS2_B","WarmUp|Strength:main|Accessory|Accessory|Speed/Agility|Core/Prehab|CoolDown"),
    ("off_strength",3,"OS3_A","WarmUp|Plyo:low|Strength:lower|Accessory|Accessory|Core/Prehab|CoolDown"),
    ("off_strength",3,"OS3_B","WarmUp|Strength:upper|Accessory|Accessory|Core/Prehab|CoolDown"),
    ("off_strength",3,"OS3_C","WarmUp|Speed/Agility|Conditioning|Accessory|Core/Prehab|CoolDown"),
    ("off_power",2,"OP2_A","WarmUp|Plyo:mid|Power|Strength:main|Accessory|Accessory|Speed/Agility|Core/Prehab|CoolDown"),
    ("off_power",2,"OP2_B","WarmUp|Power|Strength:main|Accessory|Accessory|Conditioning|Core/Prehab|CoolDown"),
    ("off_power",3,"OP3_A","WarmUp|Plyo:mid|Power|Strength:lower|Accessory|Accessory|Core/Prehab|CoolDown"),
    ("off_power",3,"OP3_B","WarmUp|Strength:upper|Accessory|Accessory|Speed/Agility|Core/Prehab|CoolDown"),
    ("off_power",3,"OP3_C","WarmUp|Conditioning|Speed/Agility|Accessory|Core/Prehab|CoolDown"),
    ("preseason",2,"PS2_A","WarmUp|Plyo:mid|Speed/Agility|Strength:maint|Accessory|Conditioning|Core/Prehab|CoolDown"),
    ("preseason",2,"PS2_B","WarmUp|Speed/Agility|Conditioning|Accessory|Accessory|Core/Prehab|CoolDown"),
    ("inseason",1,"IS1_A","WarmUp|Strength:maint|Accessory|Core/Prehab|Mobility|CoolDown"),
    ("inseason",2,"IS2_A","WarmUp|Strength:maint|Accessory|Accessory|Core/Prehab|CoolDown"),
    ("inseason",2,"IS2_B","WarmUp|Mobility|Speed/Agility|Accessory|Core/Prehab|CoolDown"),
    ("postseason",1,"PO1_A","WarmUp|Mobility|Core/Prehab|Recovery|CoolDown"),
    ("postseason",2,"PO2_A","WarmUp|Mobility|Core/Prehab|Accessory|Recovery|CoolDown"),
]
DEFAULT_RULES = [
    ("no_1rm","global","allow_1rm","false","Keine 1RM-Tests"),
    ("exclude_bosu","global","exclude_exercise_ids","bosu_*","Keine Zirkusübungen"),
]

write_csv(DATA/"periodization.csv",
          ["phase_id","name","default_start_mmdd","default_end_mmdd","weekly_sessions_options","primary_focus","plyo_cap_contacts","sprint_cap_reps20y_plus","strength_intensity_hint","conditioning_hint"],
          DEFAULT_PERIODIZATION)
write_csv(DATA/"positions.csv",
          ["pos","strength_weight","power_weight","speed_weight","agility_weight","conditioning_weight","core_prehab_weight","notes"],
          DEFAULT_POSITIONS)
write_csv(DATA/"levels.csv",
          ["level","intensity_factor","volume_factor","complexity","plyo_cap_factor","sprint_cap_factor"],
          DEFAULT_LEVELS)
write_csv(DATA/"warmup_cooldown.csv",
          ["block","phase_id","name","items"],
          DEFAULT_WUCD)
write_csv(DATA/"session_templates.csv",
          ["phase_id","sessions_per_week","template_id","blocks"],
          DEFAULT_TEMPLATES)
write_csv(DATA/"rules.csv",
          ["rule_id","scope","key","value","note"],
          DEFAULT_RULES)

# ---------- RPE ----------
RPE_RESERVE = {
    "RPE6":"≈ 4 WDH Reserve",
    "RPE7":"≈ 3 WDH Reserve",
    "RPE8":"≈ 2 WDH Reserve",
    "RPE9":"≈ 1 WDH Reserve",
    "RPE10":"0 WDH Reserve",
}
def rpe_with_reserve(text: str) -> str:
    if not isinstance(text,str): return ""
    m = re.search(r"@RPE(\d+(\.\d)?)", text)
    if m:
        key = f"RPE{m.group(1).split('.')[0]}"
        if key in RPE_RESERVE:
            return f"{text} ({RPE_RESERVE[key]})"
    return text

# ---------- CSV robust laden ----------
def read_text_clean(path: Path) -> str:
    txt = path.read_text(encoding="utf-8", errors="ignore")
    txt = txt.replace("„", '"').replace("“", '"').replace("”", '"')
    txt = txt.replace("‚", "'").replace("’", "'")
    return txt

def try_read_csv_variants(text: str) -> pd.DataFrame:
    for params in [dict(sep=None, engine="python"),
                   dict(sep=",", engine="python"),
                   dict(sep=";", engine="python")]:
        try:
            return pd.read_csv(io.StringIO(text), on_bad_lines="skip", **params)
        except Exception:
            pass
    lines = [ln for ln in text.splitlines() if ln.strip()]
    head = lines[0]
    sep = ";" if head.count(";") > head.count(",") else ","
    rows = [ln.split(sep) for ln in lines]
    wid = max(len(r) for r in rows)
    rows = [r+[""]*(wid-len(r)) for r in rows]
    return pd.DataFrame(rows[1:], columns=[c.strip() for c in rows[0]])

def ensure_cols(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    mapping = {
        "Übung":"name","Kategorie":"category","Ziel":"goal","Environment":"environment",
        "Position(en)":"positions","Level (R/A/P/E)":"levels","Standard-Dosis":"volume_hint",
        "Cues (2x)":"coaching_points","Progression":"progression","Regression":"regression",
        "Contra":"contra","Standard-Pause":"rest","Hinweis (Phase-Default)":"note",
    }
    for de,en in mapping.items():
        if de in df.columns and en not in df.columns:
            df = df.rename(columns={de:en})
    for must in ["name","category","environment","positions","levels","volume_hint",
                 "coaching_points","progression","regression","contra","rest"]:
        if must not in df.columns: df[must] = ""
    if "id" not in df.columns:
        df["id"] = df["name"].astype(str).str.lower().str.replace(r"[^a-z0-9]+","_",regex=True).str.strip("_")
    def tidy_cat(x:str):
        s = str(x).lower()
        if s.startswith("strength"): return "Strength"
        if s.startswith("power"): return "Power"
        if s.startswith("plyo"): return "Plyo"
        if s.startswith("speed"): return "Speed"
        if s.startswith("agility"): return "Agility"
        if s.startswith("conditioning"): return "Conditioning"
        if s.startswith("core") or "prehab" in s: return "Core/Prehab"
        if s.startswith("mobility") or s.startswith("recovery"): return "Mobility"
        return "Accessory"
    df["category"] = df["category"].apply(tidy_cat)
    repl = {"Gym/Platz":"Gym;Platz","Platz/Gym":"Platz;Gym","Home/Gym":"Home;Gym","Tools/Gym":"Tools;Gym"}
    df["environment"] = df["environment"].astype(str).str.strip().replace(repl)
    def tidy_positions(x:str):
        s = str(x).upper()
        if s in ["ALL","ALLE","ALLE POSITIONEN","*","ANY",""]: return "ALL"
        s = re.sub(r"[\/,]", ";", s)
        s = ";".join([p.strip() for p in s.split(";") if p.strip()])
        return s if s else "ALL"
    def tidy_levels(x:str):
        s = str(x)
        if not s: return "ALL"
        u = s.upper()
        if "R/A/P/E" in u: return "Rookie;Advanced;Pro;Elite"
        u = re.sub(r"[\/,]", ";", u)
        u = (u.replace("ROOKIE","Rookie")
               .replace("ADVANCED","Advanced")
               .replace("PRO","Pro")
               .replace("ELITE","Elite")
               .replace("R","Rookie").replace("A","Advanced").replace("P","Pro").replace("E","Elite"))
        return u
    df["positions"] = df["positions"].apply(tidy_positions)
    df["levels"]    = df["levels"].apply(tidy_levels)
    df["coaching_points"] = df["coaching_points"].astype(str).str.replace("·","|")
    for opt in ["plyo_impact","equipment_detail","goal","note"]:
        if opt not in df.columns: df[opt] = ""
    return df

def load_exercises_robust() -> pd.DataFrame:
    user_path = DATA/"exercises_user.csv"
    legacy_path = DATA/"exercises.csv"
    if user_path.exists():
        text = read_text_clean(user_path)
        df = try_read_csv_variants(text)
        return ensure_cols(df)
    if legacy_path.exists():
        return ensure_cols(pd.read_csv(legacy_path))
    base = pd.DataFrame([{
        "id":"goblet_squat","name":"Goblet Squat","category":"Strength","environment":"Home;Tools;Gym",
        "positions":"ALL","levels":"ALL","volume_hint":"4x8@RPE7","coaching_points":"Core fest|Knie raus","rest":"60-90s"
    }])
    return ensure_cols(base)

PER = pd.read_csv(DATA/"periodization.csv").set_index("phase_id").to_dict(orient="index")
POS = pd.read_csv(DATA/"positions.csv").set_index("pos").to_dict(orient="index")
LVL = pd.read_csv(DATA/"levels.csv").set_index("level").to_dict(orient="index")
WUCD = pd.read_csv(DATA/"warmup_cooldown.csv")
TPL  = pd.read_csv(DATA/"session_templates.csv")
RULES = pd.read_csv(DATA/"rules.csv")
EX   = ensure_cols(load_exercises_robust())

def env_ok(env: str, eq_set: list) -> bool:
    envs = [e.strip() for e in str(env).split(";") if e.strip()]
    return any(e in eq_set for e in envs)

def level_ok(levels: str, level: str) -> bool:
    L = [x.strip() for x in str(levels).split(";")]
    return "ALL" in L or level in L

def pos_ok(positions: str, pos: str) -> bool:
    P = [x.strip().upper() for x in str(positions).split(";")]
    return "ALL" in P or pos.upper() in P

def scale_sets(presc: str, vol_factor: float) -> str:
    m = re.match(r"\s*(\d+)x(.*)", str(presc))
    if not m: return presc
    sets = max(1, round(int(m.group(1)) * vol_factor))
    rest = m.group(2).strip()
    return f"{sets}x{rest}"

def estimate_plyo_contacts(presc: str) -> int:
    m = re.match(r"\s*(\d+)x(\d+)", str(presc).replace(" ",""))
    return int(m.group(1))*int(m.group(2)) if m else 0

def warmup_items():
    row = WUCD[WUCD["block"]=="warmup"].iloc[0]
    return [x.strip() for x in str(row["items"]).split("|") if x.strip()]

def cooldown_items():
    row = WUCD[WUCD["block"]=="cooldown"].iloc[0]
    return [x.strip() for x in str(row["items"]).split("|") if x.strip()]

def choose_templates(phase_id: str, spw: int, week: int):
    cand = TPL[(TPL["phase_id"]==phase_id) & (TPL["sessions_per_week"]==int(spw))]
    cand = cand.sort_values("template_id")
    idx = (int(week)-1) % len(cand)
    order = list(cand["template_id"])
    chosen = [order[(idx+i) % len(order)] for i in range(spw)]
    return list(cand[cand["template_id"].isin(chosen)].itertuples(index=False))

def pick_exercise(category_key: str, qualifiers: list, eq_set: list, pos: str, level: str, used_ids: set):
    df = EX.copy()
    for must in ["category","environment","positions","levels","volume_hint","id","name","coaching_points"]:
        if must not in df.columns: df[must] = ""
    if category_key == "Core/Prehab":
        df = df[df["category"].str.startswith("Core")]
    else:
        df = df[df["category"].str.lower().str.startswith(category_key.lower())]
    df = df[df["environment"].apply(lambda e: env_ok(e, eq_set))]
    df = df[df["positions"].apply(lambda p: pos_ok(p, pos))]
    df = df[df["levels"].apply(lambda l: level_ok(l, level))]
    df = df[~df["id"].astype(str).str.startswith("bosu_")]
    if df.empty: return None, None
    df = df.sort_values(by=["id"])
    for _, r in df.iterrows():
        if r["id"] in used_ids: 
            continue
        presc = str(r.get("volume_hint","")).strip() or "3x8@RPE7"
        return r.to_dict(), presc
    return None, None

def apply_caps(blocks: list, plyo_cap: float, sprint20p_cap: float):
    total_contacts = 0
    sprint20p = 0
    out = []
    for b in blocks:
        t = b.get("type")
        if t == "Plyo":
            c = estimate_plyo_contacts(b.get("prescription",""))
            if total_contacts + c > plyo_cap:
                continue
            total_contacts += c
        if t in ("Speed","Speed/Agility"):
            if "20" in str(b.get("prescription","")) and "voll" in str(b.get("prescription","")).lower():
                sprint20p += 1
                if sprint20p > sprint20p_cap:
                    continue
        out.append(b)
    return out

def generate_plan(phase_id: str, week: int, pos: str, level: str, sessions_per_week: int, equipment_set: list):
    per = pd.Series(PER[phase_id])
    lvl = pd.Series(LVL[level])
    plyo_cap = float(per["plyo_cap_contacts"]) * float(lvl["plyo_cap_factor"])
    sprint_cap = float(per["sprint_cap_reps20y_plus"]) * float(lvl["sprint_cap_factor"])
    vol_factor = float(lvl["volume_factor"])
    used = set(); sessions = []
    templates = choose_templates(phase_id, sessions_per_week, week)
    for i in range(sessions_per_week):
        t = templates[i]
        blocks = [{"type":"WarmUp","items": warmup_items()}]
        parts = [p.strip() for p in str(t.blocks).split("|") if p.strip()]
        for part in parts:
            if part.lower() in ("warmup","cooldown"): 
                continue
            label = part.split(":")[0]
            qualifiers = part.split(":")[1:]
            if label == "Accessory":
                accs = []
                for _ in range(2):
                    r, presc = pick_exercise("Accessory" if "Accessory" in EX["category"].unique() else "Strength", qualifiers, equipment_set, pos, level, used)
                    if not r: break
                    used.add(r["id"])
                    accs.append({"id": r["id"], "name": r["name"], "prescription": rpe_with_reserve(scale_sets(presc, vol_factor))})
                if accs: 
                    blocks.append({"type":"Accessory","exercises":accs})
            elif label in ("Core/Prehab","Core","Prehab"):
                r, presc = pick_exercise("Core/Prehab","", equipment_set, pos, level, used)
                if r:
                    used.add(r["id"])
                    blocks.append({"type":"Core/Prehab","id": r["id"], "name": r["name"], "prescription": rpe_with_reserve(scale_sets(presc, vol_factor))})
            else:
                cat = "Strength" if label.startswith("Strength") or label in ("Strength","maint","main","upper","lower") else label
                r, presc = pick_exercise(cat, qualifiers, equipment_set, pos, level, used)
                if r:
                    used.add(r["id"])
                    blocks.append({"type": label if label!="Core" else "Core/Prehab", "id": r["id"], "name": r["name"], "prescription": rpe_with_reserve(scale_sets(presc, vol_factor))})
        blocks.append({"type":"CoolDown","items": cooldown_items()})
        blocks = apply_caps(blocks, plyo_cap, sprint_cap)
        sessions.append({"template": t.template_id, "blocks": blocks})
    return {"phase": phase_id,"week": int(week),"pos": pos,"level": level,"sessions_per_week": int(sessions_per_week),"sessions": sessions}

def plan_to_pdf(plans: list, team: str, author: str):
    buf = BytesIO(); c = canvas.Canvas(buf, pagesize=A4); W,H = A4
    for plan in plans:
        x, y = 2*cm, H-2*cm
        def line(txt, lh=12):
            nonlocal y
            if y < 2*cm: c.showPage(); y = H-2*cm
            c.drawString(x, y, txt); y -= lh
        header = f"Team: {team} | Phase: {plan['phase']} W{plan['week']} | Pos: {plan['pos']} | Level: {plan['level']} | Sessions/W: {plan['sessions_per_week']} | Coach: {author}"
        line(header); line("-"*95)
        for i, sess in enumerate(plan["sessions"], 1):
            line(f"Session {i} – Template {sess['template']}")
            for b in sess["blocks"]:
                if b["type"] in ("WarmUp","CoolDown"):
                    line(f"{b['type']}: " + " | ".join(b["items"]))
                elif b["type"]=="Accessory":
                    for ex in b["exercises"]:
                        line(f"Accessory: {ex['name']} — {ex['prescription']}")
                else:
                    line(f"{b['type']}: {b.get('name','')} — {b.get('prescription','')}")
            line("-"*95)
        y = 2*cm; c.setFont("Helvetica", 9)
        c.drawString(2*cm, y, "RPE: 6≈4 WDH Res · 7≈3 · 8≈2 · 9≈1 · 10=0"); c.showPage()
    c.save(); return buf.getvalue()

st.set_page_config(page_title="The Core Programm", page_icon="🏈", layout="wide")
st.title("🏈 The Core Programm – Athletik-Plangenerator (v2.4)")
st.caption("Robustes CSV-Parsing, 4-Wochen-Tabs, Caps & PDF. RPE mit Reserve-Hinweis.")

with st.sidebar:
    st.header("Einstellungen")
    PER_D = pd.read_csv(DATA/"periodization.csv").set_index("phase_id").to_dict(orient="index")
    LVL_D = pd.read_csv(DATA/"levels.csv").set_index("level").to_dict(orient="index")
    POS_D = pd.read_csv(DATA/"positions.csv").set_index("pos").to_dict(orient="index")
    phase = st.selectbox("Phase", list(PER_D.keys()), index=list(PER_D.keys()).index("off_strength") if "off_strength" in PER_D else 0)
    week = st.number_input("Start-Woche", 1, 52, 1, 1)
    position = st.selectbox("Position", list(POS_D.keys()), index=list(POS_D.keys()).index("WR") if "WR" in POS_D else 0)
    level = st.selectbox("Level", list(LVL_D.keys()), index=list(LVL_D.keys()).index("Advanced") if "Advanced" in LVL_D else 0)
    sessions_per_week = st.radio("Sessions/Woche", [2,3], index=0, horizontal=True)
    block_len = st.selectbox("Block-Länge (Wochen)", [1,2,3,4], index=3)
    equipment = st.multiselect("Equipment/Umgebung", ["Home","Gym","Tools","Platz"], default=["Gym","Platz","Tools","Home"])
    st.markdown("---")
    team = st.text_input("Team", "Spandau Bulldogs")
    author = st.text_input("Coach/Autor", "Coach Curtis")
    go = st.button("Plan generieren", type="primary")

if go:
    with st.spinner("Generiere 4-Wochen-Block ..."):
        weeks = [int(week)+i for i in range(int(block_len))]
        tabs = st.tabs([f"Woche {w}" for w in weeks])
        plans = []
        for w, tab in zip(weeks, tabs):
            with tab:
                plan = generate_plan(phase, w, position, level, int(sessions_per_week), equipment)
                plans.append(plan)
                st.success(f"Plan für Woche {w} erstellt.")
                for i, sess in enumerate(plan["sessions"], start=1):
                    with st.container(border=True):
                        st.markdown(f"### Session {i} – {sess['template']}")
                        for blk in sess["blocks"]:
                            if blk["type"] in ("WarmUp","CoolDown"):
                                st.write(f"**{blk['type']}**: " + " | ".join(blk["items"]))
                            elif blk["type"]=="Accessory":
                                st.write("**Accessory:**")
                                for ex in blk["exercises"]:
                                    st.write(f"- {ex['name']} — {ex['prescription']}")
                            else:
                                st.write(f"**{blk['type']}**: {blk.get('name','')} — {blk.get('prescription','')}")
        st.markdown("---")
        if st.button("📄 Gesamt-PDF (alle Wochen)"):
            pdf_bytes = plan_to_pdf(plans, team, author)
            fname = f"Block_{team.replace(' ','_')}_{position}_W{weeks[0]}-W{weeks[-1]}.pdf"
            st.download_button("Download", data=pdf_bytes, file_name=fname, mime="application/pdf")
else:
    st.info("Links einstellen und **Plan generieren** klicken. Die App liest **app/data/exercises_user.csv** – egal ob Komma/Semikolon.")
