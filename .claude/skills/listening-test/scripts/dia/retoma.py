"""重做个别练习句：python3 retoma.py d1029 g0_0="Hay que revisar todas las cajas hoy." ..."""
import json, sys
from pathlib import Path
from motor_dia import toma, b64, SP
N = sys.argv[1]
A = json.loads((SP/f"{N}_audio.json").read_text()); D = json.loads((SP/f"{N}_data.json").read_text())
for arg in sys.argv[2:]:
    k, es = arg.split("=", 1)
    mp3, v, t = toma(es, es, velocidades=(0.95, 0.9, 1.0, 0.85, 1.05))
    A[k] = b64(mp3); print(k, v, t)
    g, i = k[1:].split("_")
    D["tres"][int(g)]["filas"][int(i)]["es"] = es
(SP/f"{N}_audio.json").write_text(json.dumps(A)); (SP/f"{N}_data.json").write_text(json.dumps(D, ensure_ascii=False))
