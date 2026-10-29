"""每日页发布前检查：真点一遍 + 发布版听写 MP3 解码回测。python3 prueba_pagina.py d1029"""
import json, re, sys
from pathlib import Path
import numpy as np, sherpa_onnx
from playwright.sync_api import sync_playwright
SP = Path(__file__).parent
N = sys.argv[1]
D = json.loads((SP / f"{N}_data.json").read_text())
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("file://" + str(SP / f"{N}.html")); pg.wait_for_timeout(300)
    print("h2:", pg.locator("#practica h2").all_inner_texts())
    pv = pg.locator("#previo .card").first
    print("认词常显:", pv.locator(".resp").is_visible(), "| 记法:", "记法" in pv.inner_text())
    c = pg.locator("#ciegas .card").first
    print("盲听", pg.locator("#ciegas .card").count(), "张 | 原文初始藏:", not c.locator("[data-caja=es]").is_visible())
    c.locator("button[data-que=es]").click(); print("  看原文:", c.locator("[data-caja=es]").inner_text())
    print("语法组:", pg.locator("#tres .card").count(), "| 句块:", pg.locator("#bloques .card .par").count())
    for i, v in enumerate(D["viejas"]):
        card = pg.locator("#viejas .card").nth(i)
        card.locator("input").fill(v["es"]); card.locator('[data-a="chk"]').click()
        fb = card.locator(".fb").inner_text()
        if not fb.startswith("✓"): print("  ✗ 自写卡写对却没过:", v["es"], fb)
        if v["estricto"]:
            sin = re.sub("[áéíóú]", lambda m: "aeiou"["áéíóú".index(m.group())], v["es"])
            card.locator("input").fill(sin); card.locator('[data-a="chk"]').click()
            print("  严判", sin, "→", card.locator(".fb").inner_text())
    pg.screenshot(path=str(SP / f"{N}_practica.png"), full_page=True)
    pg.click(".tabs button[data-panel=prueba]"); pg.wait_for_timeout(200)
    btn = pg.locator("#lectura .q").first.locator(".opts button").first
    props = ["background-color", "color", "border-top-width", "outline-style", "font-weight"]
    get = f"e=>{json.dumps(props)}.map(p=>getComputedStyle(e)[p])"
    a0 = btn.evaluate(get); btn.click(); pg.mouse.move(0, 0); pg.wait_for_timeout(100); a1 = btn.evaluate(get)
    print("选中变化属性数:", sum(x != y for x, y in zip(a0, a1)))
    def llenar(ok):
        for n, q in enumerate(D["dictado"]):
            pg.locator("#test .q").nth(n).locator("input").fill(q["resp"] if ok else "zzz")
        for n, q in enumerate(D["palabras"]):
            pg.locator("#palabras .q").nth(n).locator("input").fill(q["resp"] if ok else "zzz")
        for n, q in enumerate(D["lectura"]):
            v = q["v"] if ok else not q["v"]
            pg.locator("#lectura .q").nth(n).locator(f".opts button[data-v='{1 if v else 0}']").click()
        pg.click("#entregar"); pg.wait_for_timeout(200)
        return pg.inner_text("#marcador h3")
    print("全对 →", llenar(True)); pg.screenshot(path=str(SP / f"{N}_prueba.png"), full_page=True)
    print("全错 →", llenar(False))
    print("④:", pg.locator("#habla li").count(), "题 | ⑤:", pg.locator("#es-lineas > *").count(), "行")
    pcm = pg.evaluate("""async () => {
      const ctx = new OfflineAudioContext(1, 16000, 16000); const out = {};
      for (const k of Object.keys(CLIPS).filter(k => /^t\\d+(_dos)?$/.test(k))) {
        const bin = Uint8Array.from(atob(CLIPS[k]), c => c.charCodeAt(0));
        const buf = await ctx.decodeAudioData(bin.buffer);
        out[k] = [buf.sampleRate, Array.from(buf.getChannelData(0))];
      } return out; }""")
    b.close()
sys.path.insert(0, str(SP))
from motor_dia import asr, fichas, bv
bien = 0
for n, q in enumerate(D["dictado"]):
    for suf in ("", "_dos"):
        sr, s = pcm[f"t{n}{suf}"]
        st = asr.create_stream(); st.accept_waveform(sr, np.array(s, dtype=np.float32)); asr.decode_stream(st)
        oido = " " + " ".join(bv(x) for x in fichas(st.result.text)) + " "
        meta = " " + " ".join(bv(x) for x in fichas(q["resp"])) + " "
        ok = meta in oido or meta.replace(" ", "") in oido.replace(" ", "")
        bien += ok
        if not ok: print("  ✗", q["resp"], suf, st.result.text)
print(f"发布版听写回测: {bien}/{2*len(D['dictado'])}")
print("JS 报错:", errs or "无")
