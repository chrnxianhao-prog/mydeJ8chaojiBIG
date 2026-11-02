"""听写词 MP3 解码后 whisper 听错时，重挑一条解码后也对的：python3 refija.py d1102b llamé [otra…]，完了再跑 dMMDD_page.py"""
import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from motor_dia import tts, SID, oir, fichas, bv, b64, MARCO_PALABRA, a_mp3, stitch, silence_like, SP
N, PAL = sys.argv[1], sys.argv[2:]
A = json.loads((SP/f"{N}_audio.json").read_text()); dic = json.loads((SP/f"{N}_data.json").read_text())["dictado"]
def bien(texto, w):
    o = " " + " ".join(bv(x) for x in fichas(texto)) + " "; m = " " + " ".join(bv(x) for x in fichas(w)) + " "
    return m in o or m.replace(" ", "") in o.replace(" ", "")
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium"); pg = b.new_page()
    for w in PAL:
        cands = {}
        for v in (0.9, 0.95, 1.0, 1.05, 1.1, 0.85):
            for r in range(3):
                a = tts.generate(MARCO_PALABRA.format(w), sid=SID, speed=v)
                mp3 = a_mp3(a.samples, a.sample_rate, 56); dos, _ = stitch([mp3, silence_like(mp3, 500), mp3])
                cands[f"{v}-{r}"] = [b64(mp3), b64(dos)]
        pcm = pg.evaluate("""async (C) => { const ctx = new OfflineAudioContext(1, 16000, 16000); const out = {};
          for (const [k, pair] of Object.entries(C)) { out[k] = [];
            for (const x of pair) { const bin = Uint8Array.from(atob(x), c => c.charCodeAt(0));
              const buf = await ctx.decodeAudioData(bin.buffer); out[k].push([buf.sampleRate, Array.from(buf.getChannelData(0))]); } }
          return out; }""", cands)
        elegido = next((k for k, pares in pcm.items() if all(bien(oir(s, sr), w) for sr, s in pares)), None)
        assert elegido, f"{w} 没有一条解码后过"
        i = [q["resp"] for q in dic].index(w)
        A[f"t{i}"], A[f"t{i}_dos"] = cands[elegido]; print(w, "→", elegido, flush=True)
    b.close()
(SP/f"{N}_audio.json").write_text(json.dumps(A))
