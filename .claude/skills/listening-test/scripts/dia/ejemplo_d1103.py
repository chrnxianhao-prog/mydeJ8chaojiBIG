"""2026-11-03：本周场景「打电话订缠绕膜」第一天。电话句型 ¿Puede…? / ¿Cuánto cuesta…? + 单 r 像 d（-ré -rá）+ 软 b（-aba）+ 口语快答"""
from motor_dia import construir
C = {}
C["TRES"] = [
    ("打电话订货：¿Puede + 原形?（您能……吗）", [
        ("¿Puede mandar cien rollos de playo?", "您能送一百卷缠绕膜吗？", "puede + 原形", "puede mandar"),
        ("¿Cuánto cuesta cada rollo?", "每卷多少钱？", "cuesta（多少钱）· cada（每）", "cuesta cada rollo"),
        ("¿Para cuándo puede llegar?", "什么时候能到？", "para cuándo（哪天之前）", "puede llegar"),
    ]),
    ("单个 r 弹一下，听着像 d：将来 -ré / -rá", [
        ("Mañana llamaré al proveedor.", "明天我给供应商打电话", "不是 llamade → llamaré", "llamaré"),
        ("El camión llegará el jueves.", "卡车周四到", "不是 llegada → llegará", "llegará"),
        ("Pediré más rollos mañana.", "明天我多订些", "不是 pedide → pediré", "pediré"),
    ]),
    ("词中间的 b 很软，听着像 d：以前常 -aba", [
        ("Antes llamaba por teléfono.", "以前我常打电话", "不是 llamada → llamaba", "llamaba"),
        ("Antes compraba el playo en una tienda.", "以前我常在店里买缠绕膜", "compraba", "compraba"),
        ("Antes trabajaba en una tienda de ropa.", "以前我在服装店上班", "trabajaba", "trabajaba"),
    ]),
]
C["RAPIDO"] = [
    ("我得多订些缠绕膜。", "Necesito pedir más rollos de playo, por favor.", "playo por favor"),
    ("这周我就要。", "Lo necesito esta semana.", "lo necesito esta semana"),
    ("每卷多少钱？", "¿Cuánto cuesta cada rollo?", "cuesta cada rollo"),
    ("明天我再打电话。", "Mañana llamaré otra vez.", "llamaré otra vez"),
    ("（指着东西问）这个叫什么？", "¿Cómo se llama esto?", "cómo se llama esto"),
    ("得给托盘缠膜。", "Hay que envolver la tarima.", "envolver la tarima"),
]
C["CIEGAS"] = [
    ("Apague el montacargas, por favor.", "请把叉车关了。", "apague"),
    ("Hay que envolver todas las tarimas hoy.", "今天所有托盘都得缠膜。", "envolver"),
    ("Firme la hoja aquí abajo.", "在单子下面这儿签字。", "hoja"),
    ("¿Cuánto cuesta cada rollo de playo?", "每卷缠绕膜多少钱？", "cuesta"),
    ("El proveedor llegará a las diez.", "供应商十点到。", "llegará"),
    ("Antes llamaba todos los días.", "以前我天天打电话。", "llamaba"),
]
C["BLOQUES"] = [
    ("Hola, buenos días, le llamo de la bodega.", "您好，我是仓库这边打来的。", "le llamo de la bodega"),
    ("Necesito pedir cien rollos de playo, por favor.", "我要订一百卷缠绕膜。", "playo por favor"),
    ("¿Cuánto cuesta cada rollo?", "每卷多少钱？", "cuesta cada rollo"),
    ("Lo necesito esta semana, por favor.", "这周我就要，麻烦了。", "lo necesito esta semana"),
    ("Muy bien, muchas gracias.", "好的，非常感谢。", "muchas gracias"),
]
C["VIEJAS"] = [
    ("llamaré", "「明天我再打（将）」→ Mañana ______ otra vez.", "Mañana llamaré al proveedor.", "明天我给供应商打电话。"),
    ("llegará", "「卡车周四到（将）」→ El camión ______ el jueves.", "El camión llegará el jueves.", "卡车周四到。"),
    ("pediré", "「我将多订（将）」→ ______ más rollos mañana.", "Pediré más rollos mañana.", "明天我多订些。"),
    ("llamaba", "「以前我常打电话（以前常）」→ Antes ______ por teléfono.", "Antes llamaba por teléfono.", "以前我常打电话。"),
    ("compraba", "「以前我常买（以前常）」→ Antes ______ el playo en una tienda.", "Antes compraba el playo en una tienda.", "以前我常在店里买缠绕膜。"),
    ("apagar", "「关掉（原形）」→ Hay que ______ la luz.", "Apague el montacargas, por favor.", "请把叉车关了。"),
    ("envolver", "「缠、包（原形）」→ Hay que ______ la tarima.", "Hay que envolver la tarima.", "得给托盘缠膜。"),
    ("la hoja", "（货）单（带 la）", "Firme la hoja aquí abajo.", "在单子下面这儿签字。"),
]
C["ESTRICTO"] = {"llamaré", "llegará", "pediré"}
C["PREVIO"] = [
    ("cuánto cuesta", "多少钱", "¿Cuánto cuesta? 问价钱；cuesta 来自 costar"),
    ("cada", "每、每一个", "cada rollo = 每卷；cada semana = 每周。这个是真的 d"),
    ("el precio", "价格", "像英语 price"),
    ("mandar", "寄、送（货）", "上次 marcar 你写成 mandar —— mandar 是送，marcar 是做记号"),
    ("apagar", "关掉（机器、灯）", "上次写成 acrredo。a-pa-gar，encender 的反义词"),
    ("envolver", "缠、包（膜）", "en + volver：envolver la tarima = 给托盘缠膜"),
    ("la hoja", "（货）单", "上次写成 la ha。h 不发音：o-ja，j 像拼音 h"),
]
C["DICTADO"] = ["llamaré", "pediré", "llegará", "mandaré", "llamaba", "compraba", "cargaba", "cada", "nada", "apagar"]
C["PALABRAS"] = [
    ("货物（名词，带 la）", "la mercancía", "La mercancía llega el jueves."),
    ("打开（机器、灯）（动词原形）", "encender", "Hay que encender el montacargas."),
    ("缠绕膜（墨西哥说法，带 el）", "el playo", "Necesito más rollos de playo."),
    ("货架（墨西哥说法，带 el）", "el anaquel", "El anaquel ya está lleno."),
    ("做记号、标记（动词原形）", "marcar", "Hay que marcar las cajas dañadas."),
    ("要、订（货）（动词原形）", "pedir", "Voy a pedir más mercancía."),
]
C["TEXTO"] = [
    "Hoy por la mañana hablé con el proveedor.",
    "Le pregunté: «¿Cuánto cuesta el rollo de plástico?»",
    "Me dijo: «Ochenta pesos».",
    "Es más caro que antes.",
    "Antes costaba setenta.",
    "Pero lo necesito, entonces voy a comprar cincuenta.",
    "Van a llegar el miércoles.",
]
C["LECTURA"] = [
    ("现在比以前便宜。", False, "Es más caro que antes —— 比以前贵"),
    ("货周四到。", False, "Van a llegar el miércoles —— 周三"),
    ("现在一卷八十比索。", True, "«Ochenta pesos»"),
    ("他要买五十卷。", True, "voy a comprar cincuenta"),
]
C["HABLA"] = [
    "「您能送一百卷缠绕膜吗？」→ ¿Puede ______ cien rollos de playo?",
    "「每卷多少钱？」→ ¿Cuánto ______ cada rollo?",
    "「这周我就要。」→ Lo ______ esta semana.",
]
C["ESCRITO"] = {
    "titulo": "Una llamada",
    "pide": "这次<b>不给原形</b>，只给意思和时间。先看时间，再定词尾，每个空填<b>一个词</b>。",
    "lineas": [
        ["Ayer ______ al proveedor.", "打电话 · 那一次"],
        ["Antes ______ el playo en una tienda.", "买 · 以前常"],
        ["Ahora cada rollo ______ ochenta pesos.", "多少钱的『要』 · 现在"],
        ["Mañana el camión ______ a las diez.", "到 · 将来"],
        ["La bodega ______ vacía.", "状态"],
        ["______ que envolver las tarimas.", "得 · 不说谁"],
    ],
}
construir(C, "d1103")
