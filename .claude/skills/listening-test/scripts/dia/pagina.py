"""拿最新的每日模板，换掉当天的文字，嵌音频 / 数据 / Dalia 原文。"""
import json, re
from pathlib import Path
SP = Path(__file__).parent
BASE = Path("/home/user/mydeJ8chaojiBIG/.claude/skills/listening-test/assets/daily-page-dalia.template.html")
M = "Digo {}, otra vez."

def armar(nombre, *, titulo, eyebrow, h1, lede, regla, secciones, mmdd, fecha, tema):
    """secciones：{h2 开头几个字: (新 h2, 新说明 html 或 None)}"""
    t = BASE.read_text()
    def re1(pat, fn):
        nonlocal t
        t, n = re.subn(pat, fn, t, count=1, flags=re.S)
        assert n == 1, pat
    re1(r"<title>.*?</title>", lambda m: f"<title>{titulo}</title>")
    re1(r'<p class="eyebrow">.*?</p>', lambda m: f'<p class="eyebrow">{eyebrow}</p>')
    re1(r"<h1>.*?</h1>", lambda m: f"<h1>{h1}</h1>")
    re1(r'<p class="lede">.*?</p>', lambda m: f'<p class="lede">\n      {lede}\n    </p>')
    re1(r'<div class="tarea" style="border-left-color:var\(--ud\)">.*?</div>',
        lambda m: f'<div class="tarea" style="border-left-color:var(--ud)">\n        {regla}\n      </div>')
    for cab, (h2, sub) in secciones.items():
        if sub is None:
            re1(r"<h2>" + re.escape(cab) + r"[^<]*</h2>", lambda m: f"<h2>{h2}</h2>")
        else:
            re1(r"<h2>" + re.escape(cab) + r'[^<]*</h2>(\s*)<p class="sub">.*?</p>',
                lambda m: f'<h2>{h2}</h2>{m.group(1)}<p class="sub">{sub}</p>')
    t = re.sub(r'localStorage\.(set|get)Item\("dia\d+\.tab"', lambda m: f'localStorage.{m.group(1)}Item("dia{mmdd}.tab"', t)
    re1(r'db\.doc\("resultados/dia-\d+"\)', lambda m: f'db.doc("resultados/dia-{mmdd}")')
    re1(r'fecha: "[^"]*", tema: "[^"]*"', lambda m: f'fecha: "{fecha}", tema: "{tema}"')
    (SP / f"{nombre}.template.html").write_text(t)

    D = json.loads((SP / f"{nombre}_data.json").read_text())
    T = {}
    for q in D["dictado"]: T[f"t{q['i']}"] = M.format(q["resp"])
    for g in D["tres"]:
        for f in g["filas"]: T[f"g{g['g']}_{f['k']}"] = f["es"]
    for c in D["ciegas"]: T[f"c{c['k']}"] = c["es"]
    for f in D["bloques"][0]["filas"]: T[f"gb0_{f['k']}"] = f["es"]
    for v in D["viejas"]: T[f"v{v['i']}"] = M.format(v["es"]); T[f"v{v['i']}_ej"] = v["ej"]
    for p in D["previo"]: T[f"pv{p['i']}"] = M.format(p["es"])
    for p in D["palabras"]: T[f"w{p['i']}"] = M.format(p["resp"]); T[f"w{p['i']}_ej"] = p["ej"]
    for x in D["texto"]: T[f"tx{x['i']}"] = x["es"]
    A = json.loads((SP / f"{nombre}_audio.json").read_text())
    falt = [k for k in A if not k.endswith("_dos") and k not in T]
    assert not falt, falt
    (SP / f"{nombre}_textos.json").write_text(json.dumps(T, ensure_ascii=False))
    html = t.replace("__AUDIO__", json.dumps(A)).replace("__DATA__", json.dumps(D, ensure_ascii=False)).replace("__TEXTOS__", json.dumps(T, ensure_ascii=False))
    (SP / f"{nombre}.html").write_text(html)
    print("ok", nombre, len(T), "textos")
