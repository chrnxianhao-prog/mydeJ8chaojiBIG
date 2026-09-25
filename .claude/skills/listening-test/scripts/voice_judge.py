"""音色裁判：每个候选音色念同一批易错句，交给 whisper-small 转写，数目标词听对了几个。

用法：把候选模型（sherpa-onnx 的 vits-piper-* / kokoro-multi-lang-v1_0）和
sherpa-onnx-whisper-small 解压到 .piper-cache/，然后 python3 voice_judge.py。

局限：whisper 有语言模型兜底，句子里有上下文时念得含糊也可能被「猜对」。
2026-09-25 学生报的 llevar / barato / telas，旧音色 claude 在这里全被听对了 ——
所以分数只用来刷掉明显不行的，最后一定让学生用耳朵定。
"""
import json, re, time, unicodedata
from pathlib import Path
import numpy as np, sherpa_onnx

T = Path(".piper-cache")   # 候选模型和 whisper 都解压到这里

FRASES = [
    ("Mañana le vamos a llevar las telas.", ["llevar", "telas"]),
    ("Este abrigo es muy barato.", ["barato", "abrigo"]),
    ("Perdí el equipaje en el viaje.", ["equipaje", "viaje"]),
    ("El río pasa cerca del árbol.", ["rio", "arbol"]),
    ("La calefacción no funciona en la reunión.", ["calefaccion", "reunion"]),
    ("Fuimos a urgencias por la calle principal.", ["urgencias", "calle"]),
    ("Quiero pedir la cuenta, por favor.", ["pedir", "cuenta"]),
    ("Su pedido está listo para la entrega.", ["pedido", "entrega"]),
    ("Siga derecho y gire a la izquierda.", ["siga", "izquierda"]),
    ("La cuchara está junto al cuchillo.", ["cuchara", "cuchillo"]),
]

def piper(nombre, onnx):
    d = T / nombre
    return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(d / onnx), tokens=str(d / "tokens.txt"), data_dir=str(d / "espeak-ng-data")),
            num_threads=4), max_num_sentences=1))

def kokoro(lang):
    d = T / "kokoro-multi-lang-v1_0"
    return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=str(d / "model.onnx"), voices=str(d / "voices.bin"), tokens=str(d / "tokens.txt"),
                data_dir=str(d / "espeak-ng-data"), dict_dir=str(d / "dict"),
                lexicon=f"{d}/lexicon-us-en.txt,{d}/lexicon-zh.txt", lang=lang),
            num_threads=4), max_num_sentences=1))

motores = {}
def motor(clave, fabrica):
    if clave not in motores:
        motores[clave] = fabrica()
    return motores[clave]

VOCES = [
    # (标签, 口音组, 引擎键, 引擎工厂, sid)
    ("墨西哥 claude（现在用的）", "拉美", "claude", lambda: piper("vits-piper-es_MX-claude-high", "es_MX-claude-high.onnx"), 0),
    ("墨西哥 ald", "拉美", "ald", lambda: piper("vits-piper-es_MX-ald-medium", "es_MX-ald-medium.onnx"), 0),
    ("阿根廷 daniela", "拉美", "daniela", lambda: piper("vits-piper-es_AR-daniela-high", "es_AR-daniela-high.onnx"), 0),
    ("西班牙 davefx", "西班牙", "davefx", lambda: piper("vits-piper-es_ES-davefx-medium", "es_ES-davefx-medium.onnx"), 0),
    ("西班牙 sharvard 男", "西班牙", "sharvard", lambda: piper("vits-piper-es_ES-sharvard-medium", "es_ES-sharvard-medium.onnx"), 0),
    ("西班牙 sharvard 女", "西班牙", "sharvard", lambda: piper("vits-piper-es_ES-sharvard-medium", "es_ES-sharvard-medium.onnx"), 1),
    ("Kokoro dora 女 · 西班牙读法", "西班牙", "kk_es", lambda: kokoro("es"), 28),
    ("Kokoro alex 男 · 西班牙读法", "西班牙", "kk_es", lambda: kokoro("es"), 29),
    ("Kokoro dora 女 · 拉美读法", "拉美", "kk_419", lambda: kokoro("es-419"), 28),
    ("Kokoro alex 男 · 拉美读法", "拉美", "kk_419", lambda: kokoro("es-419"), 29),
]

asr = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=str(T / "sherpa-onnx-whisper-small/small-encoder.int8.onnx"),
    decoder=str(T / "sherpa-onnx-whisper-small/small-decoder.int8.onnx"),
    tokens=str(T / "sherpa-onnx-whisper-small/small-tokens.txt"),
    language="es", task="transcribe", num_threads=4)

def plano(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-zñ ]", " ", s)

resultados = []
for etiqueta, grupo, clave, fabrica, sid in VOCES:
    t0 = time.time()
    tts = motor(clave, fabrica)
    aciertos, total, fallos = 0, 0, []
    for frase, objetivos in FRASES:
        a = tts.generate(frase, sid=sid, speed=1.0)
        st = asr.create_stream()
        st.accept_waveform(a.sample_rate, np.array(a.samples, dtype=np.float32))
        asr.decode_stream(st)
        oido = plano(st.result.text).split()
        for obj in objetivos:
            total += 1
            if obj in oido:
                aciertos += 1
            else:
                fallos.append(f"{obj}→「{st.result.text.strip()}」")
    resultados.append({"voz": etiqueta, "grupo": grupo, "aciertos": aciertos, "total": total, "fallos": fallos})
    print(f"{aciertos:>2}/{total}  {grupo}  {etiqueta}  ({time.time()-t0:.0f}s)", flush=True)
    for f in fallos:
        print("        ✗", f, flush=True)

Path("juez.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=1))
