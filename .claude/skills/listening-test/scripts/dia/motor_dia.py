"""每日页出题引擎：合成 + whisper 逐条验 + 写 audio/data json。用法：from motor_dia import construir"""
import base64, json, re, sys, unicodedata
from pathlib import Path
import numpy as np, sherpa_onnx
sys.path.insert(0, "/home/user/mydeJ8chaojiBIG")
from profe.voz import hablar as di, CACHE, MARCO_PALABRA
from profe.providers.local import motor, a_mp3
from profe.audio import stitch, silence_like

SP = Path(__file__).parent
W = SP / "tts/sherpa-onnx-whisper-small"
asr = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=str(W / "small-encoder.int8.onnx"), decoder=str(W / "small-decoder.int8.onnx"),
    tokens=str(W / "small-tokens.txt"), language="es", task="transcribe", num_threads=4)
tts, SID = motor("latam", CACHE)

def oir(samples, sr):
    st = asr.create_stream(); st.accept_waveform(sr, np.array(samples, dtype=np.float32))
    asr.decode_stream(st); return st.result.text.strip()

# whisper 把数词写成阿拉伯数字：按整数映射回去
_U = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete veintiocho veintinueve treinta".split()
NUMEROS = {str(i): w for i, w in enumerate(_U)}
NUMEROS.update({"32": "treinta y dos", "100": "cien", "300": "trescientos"})
# whisper 不认识的生僻词，按发音拼出来的写法 —— 发音是对的
ALIAS = {"anackel": "anaquel"}

def fichas(s):
    s = re.sub(r"\d+", lambda m: " " + NUMEROS.get(m.group(), m.group()) + " ", s)
    s = s.lower()
    for k, v in ALIAS.items():
        s = s.replace(k, v)
    return re.findall(r"[a-záéíóúñü]+", s)

def plano(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

bv = lambda x: re.sub(r"\bh", "", x.replace("v", "b"))   # b/v 同音；h 不发音

def toma(texto, objetivo, exacto=True, velocidades=(0.9, 0.95, 1.0, 0.85, 1.05)):
    """合成到 whisper 听对为止；exacto=True 时连重音都要对。返回 (mp3 bytes, 速度, 听到的)。"""
    visto = []
    for v in velocidades:
        a = tts.generate(texto, sid=SID, speed=v)
        t = oir(a.samples, a.sample_rate)
        oido = fichas(t)
        f = (lambda x: bv(x)) if exacto else (lambda x: bv(plano(x)))
        ok = all(f(w) in [f(x) for x in oido] for w in fichas(objetivo))
        if not ok and " " in objetivo.strip():   # whisper 会把 me trajo 连成 metrajo：去掉空格再比
            ok = f("".join(fichas(objetivo))) in f("".join(oido))
        visto.append(f"{v}:{t}")
        if ok:
            return a_mp3(a.samples, a.sample_rate, 56), v, t
    raise SystemExit(f"✗ {objetivo} 没有一个速度听对: {visto}")

b64 = lambda b: base64.b64encode(b).decode()

def pista(w):
    """首字母 + 下划线：冠词/短词原样保留。"""
    return " ".join(x if len(x) <= 2 else x[0] + "_" * (len(x) - 1) for x in w.split())

def construir(C, nombre):
    """C：TRES CIEGAS BLOQUES VIEJAS ESTRICTO PREVIO DICTADO PALABRAS TEXTO LECTURA HABLA ESCRITO"""
    palabras_texto = set(fichas(" ".join(C["TEXTO"])))
    sueltas = [x for w in C["DICTADO"] for x in fichas(w) if x not in ("la", "el", "que", "los", "las")]
    fugas = [w for w in sueltas + [p[1].split()[-1] for p in C["PALABRAS"]] if w in palabras_texto]
    assert not fugas, f"短文泄答案: {fugas}"
    audio, informe = {}, []
    for n, w in enumerate(C["DICTADO"]):
        mp3, v, t = toma(MARCO_PALABRA.format(w), w)
        audio[f"t{n}"] = b64(mp3)
        dos, _ = stitch([mp3, silence_like(mp3, 500), mp3])
        audio[f"t{n}_dos"] = b64(dos)
        informe.append(f"听写 {w:<10} {v}  「{t}」")
    for g, (verbo, filas) in enumerate(C["TRES"]):
        for k, (es, _, _, clave) in enumerate(filas):
            mp3, v, t = toma(es, clave, velocidades=(0.95, 0.9, 1.0, 0.85))
            audio[f"g{g}_{k}"] = b64(mp3); informe.append(f"练习 {es:<38} {v}  「{t}」")
    for k, (es, _, clave) in enumerate(C["CIEGAS"]):
        mp3, v, t = toma(es, clave, exacto=False, velocidades=(0.95, 0.9, 1.0, 0.85))
        audio[f"c{k}"] = b64(mp3); informe.append(f"盲听 {es:<38} {v}  「{t}」")
    for k, (es, _, clave) in enumerate(C["BLOQUES"]):
        mp3, v, t = toma(es, clave, exacto=False, velocidades=(0.95, 0.9, 1.0, 0.85))
        audio[f"gb0_{k}"] = b64(mp3); informe.append(f"句块 {es:<38} {v}  「{t}」")
    for n, (es, _, ej, _) in enumerate(C["VIEJAS"]):
        mp3, v, t = toma(MARCO_PALABRA.format(es), es, exacto=False)
        audio[f"v{n}"] = b64(mp3); audio[f"v{n}_ej"] = di(ej, 0.95)
        informe.append(f"自写 {es:<14} {v}  「{t}」")
    for n, (es, _, _) in enumerate(C["PREVIO"]):
        mp3, v, t = toma(MARCO_PALABRA.format(es), es, exacto=False)
        audio[f"pv{n}"] = b64(mp3); informe.append(f"认词 {es:<14} {v}  「{t}」")
    for n, (_, es, ej) in enumerate(C["PALABRAS"]):
        mp3, v, t = toma(MARCO_PALABRA.format(es), es, exacto=False)
        audio[f"w{n}"] = b64(mp3); audio[f"w{n}_ej"] = di(ej, 0.95)
    for n, f in enumerate(C["TEXTO"]):
        audio[f"tx{n}"] = di(f, 0.95)
    data = {
        "tres": [{"g": g, "verbo": v, "filas": [{"k": k, "es": es, "zh": zh, "regla": r} for k, (es, zh, r, _) in enumerate(f)]}
                 for g, (v, f) in enumerate(C["TRES"])],
        "ciegas": [{"k": k, "es": es, "zh": zh} for k, (es, zh, _) in enumerate(C["CIEGAS"])],
        "bloques": [{"g": "b0", "verbo": "跟读 3 遍 · 今天对同事说一句", "filas": [{"k": k, "es": es, "zh": zh, "regla": "仓库里用"} for k, (es, zh, _) in enumerate(C["BLOQUES"])]}],
        "viejas": [{"i": i, "es": e, "zh": z, "pista": pista(e), "ej": j, "ejzh": jz, "estricto": e in C["ESTRICTO"]} for i, (e, z, j, jz) in enumerate(C["VIEJAS"])],
        "previo": [{"i": i, "es": e, "zh": z, "gancho": g} for i, (e, z, g) in enumerate(C["PREVIO"])],
        "dictado": [{"i": i, "resp": w, "tilde": True} for i, w in enumerate(C["DICTADO"])],
        "palabras": [{"i": i, "zh": z + "　提示 " + pista(e), "resp": e, "ej": j} for i, (z, e, j) in enumerate(C["PALABRAS"])],
        "texto": [{"i": i, "es": s} for i, s in enumerate(C["TEXTO"])],
        "lectura": [{"i": i, "t": q, "v": v, "por": p} for i, (q, v, p) in enumerate(C["LECTURA"])],
        "habla": C["HABLA"], "escrito": C["ESCRITO"],
    }
    (SP / f"{nombre}_audio.json").write_text(json.dumps(audio))
    (SP / f"{nombre}_data.json").write_text(json.dumps(data, ensure_ascii=False))
    print("\n".join(informe))
    print(f"{len(audio)} 段 / {sum(len(v) for v in audio.values())//1024} KB　短文无泄答案")
