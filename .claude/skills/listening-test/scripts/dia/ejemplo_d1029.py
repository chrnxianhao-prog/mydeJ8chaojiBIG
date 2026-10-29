"""2026-10-29：仓库第三天。hay que（不说谁：得）+ estar 说状态 + qué / por qué + c/t 不送气听辨"""
from motor_dia import construir
C = {}
C["TRES"] = [
    ("hay que + 原形 = 得、需要（不说是谁）", [
        ("Hay que revisar todas las cajas hoy.", "今天所有箱子都得检查", "谁都行 → hay que", "hay que revisar"),
        ("Hay que cargar el camión antes de las tres.", "三点前得装好车", "hay que + 原形", "hay que cargar"),
        ("No hay que esperar al jefe.", "不用等老板", "no hay que = 不用", "no hay que esperar"),
    ]),
    ("tengo que（我得）vs hay que（得，不说谁）", [
        ("Yo tengo que contar las cajas.", "我得点箱子（就是我）", "我 → tengo que", "tengo que contar"),
        ("Hay que contar las cajas otra vez.", "箱子得再点一遍（谁点都行）", "不说谁 → hay que", "hay que contar"),
        ("¿Qué tengo que hacer?", "我得做什么？", "问老板 → ¿Qué tengo que…?", "tengo que hacer"),
    ]),
    ("estar + 状态：坏了、满了、空了", [
        ("La caja está dañada.", "箱子坏了", "状态 → está，不用 es", "está dañada"),
        ("El camión está lleno.", "卡车满了", "lleno（满）", "está lleno"),
        ("La bodega está vacía.", "仓库空了", "vacía（空，阴性）", "está vacía"),
    ]),
    ("¿qué?（什么）vs ¿por qué?（为什么）", [
        ("¿Qué hay en esta caja?", "这箱里是什么？", "qué = 什么", "hay en esta caja"),
        ("¿Por qué llegó tarde el camión?", "卡车为什么晚到了？", "por qué = 为什么", "por qué llegó tarde"),
        ("¿Qué tienes que hacer hoy?", "你今天得做什么？", "老板常问这句", "tienes que hacer"),
    ]),
    ("c / t 不送气（别听成 g / d）", [
        ("Cuento las cajas en la tarima.", "我在托盘上点箱子", "c 像拼音 g，但写 c", "cuento las cajas"),
        ("Cargamos todo a las cuatro.", "我们四点全装车", "cargamos，不是 gargamos", "cargamos todo"),
        ("La tarima está en el camión.", "托盘在卡车上", "t 像拼音 d，但写 t", "la tarima"),
    ]),
]
C["CIEGAS"] = [
    ("Hay que firmar la hoja.", "得在单子上签字。", "firmar"),
    ("El camión ya está lleno.", "卡车已经满了。", "lleno"),
    ("La bodega está vacía los domingos.", "仓库周日是空的。", "vacía"),
    ("¿Por qué llegó tarde el chofer?", "司机为什么晚到了？", "por qué"),
    ("Hay que contar todo antes de las cinco.", "五点前得全部点完。", "hay que"),
    ("La puerta dos está cerrada.", "二号门关着。", "cerrada"),
    ("¿Qué dice la hoja?", "单子上写的什么？", "hoja"),
    ("Hay que poner la mercancía en el anaquel.", "得把货放到货架上。", "mercancía"),
]
C["BLOQUES"] = [
    ("Hay que revisar todo.", "全部都得检查。", "hay que revisar"),
    ("El camión ya está lleno.", "卡车已经满了。", "lleno"),
    ("¿Qué tengo que hacer?", "我得做什么？", "tengo que hacer"),
    ("Firme aquí, por favor.", "请在这儿签字。", "firme aquí"),
    ("Esta caja está dañada, mire.", "这箱坏了，您看。", "dañada"),
]
C["VIEJAS"] = [
    ("hay que", "「得检查所有箱子（不说谁）」→ ______ revisar todas las cajas.", "Hay que revisar todas las cajas.", "所有箱子都得检查。"),
    ("está", "「箱子坏了（状态）」→ La caja ______ dañada.", "La caja está dañada.", "箱子坏了。"),
    ("lleno", "「满了（camión 阳性）」→ El camión está ______.", "El camión ya está lleno.", "卡车已经满了。"),
    ("vacía", "「空了（bodega 阴性）」→ La bodega está ______.", "La bodega está vacía.", "仓库空了。"),
    ("qué", "「我得做什么？」→ ¿______ tengo que hacer?", "¿Qué tengo que hacer?", "我得做什么？"),
    ("por qué", "「为什么（两个词）」→ ¿______ llegó tarde?", "¿Por qué llegó tarde el camión?", "卡车为什么晚到了？"),
    ("firmar", "「签字（动词原形）」→ Hay que ______ la hoja.", "Hay que firmar la hoja.", "得在单子上签字。"),
    ("la mercancía", "货物（带 la，注意 n 和重音）", "Hay que poner la mercancía en el anaquel.", "得把货放到货架上。"),
]
C["ESTRICTO"] = {"está", "qué", "por qué", "la mercancía"}
C["PREVIO"] = [
    ("hay que", "得、需要（不说谁）", "hay 你认识（有）；hay que + 原形 = 大家都得这么做"),
    ("lleno", "满的（阴性 llena）", "camión 阳性 → lleno；caja 阴性 → llena"),
    ("vacío", "空的（阴性 vacía）", "跟 lleno 反义：bodega 阴性 → vacía"),
    ("cerrado", "关着的（阴性 cerrada）", "cerrar = 关；puerta 阴性 → cerrada"),
    ("la hoja", "（货）单、一张纸", "你跟老板说过 20 cajas en la hoja！"),
    ("firmar", "签字", "司机说的 Firme aquí = 在这儿签字"),
    ("por qué", "为什么", "两个词，qué 带重音；回答用 porque（一个词）= 因为"),
    ("la mercancía", "货物", "mer-can-cí-a：中间有 n，í 带重音。跟着念三遍"),
]
C["DICTADO"] = ["la caja", "el camión", "cargar", "contar", "la etiqueta", "hay que", "lleno", "vacía", "firmar", "cerrado"]
C["PALABRAS"] = [
    ("货物（名词，带 la）", "la mercancía", "La mercancía está en la bodega."),
    ("货架（墨西哥说法，带 el）", "el anaquel", "Las camisas están en el anaquel tres."),
    ("托盘（带 la）", "la tarima", "Ponga las cajas en la tarima."),
    ("六（数字，用字母写）", "seis", "Faltan seis piezas."),
    ("做记号、标记（动词原形）", "marcar", "Hay que marcar las cajas dañadas."),
    ("要、订（货）（动词原形，pido 的原形）", "pedir", "Mañana voy a pedir más mercancía."),
]
C["TEXTO"] = [
    "Hoy el chofer llegó a las siete de la mañana.",
    "Traía treinta cajas, pero en la hoja decía treinta y dos.",
    "Faltaban dos.",
    "Mi jefe me dijo: «¿Por qué faltan dos?»",
    "Yo no lo sé, y el chofer tampoco lo sabe.",
    "Mañana tengo que llamar al proveedor.",
    "Ahora todo está en la bodega.",
]
C["LECTURA"] = [
    ("司机早上七点到的。", True, "el chofer llegó a las siete de la mañana"),
    ("老板问为什么少了。", True, "«¿Por qué faltan dos?»"),
    ("单子上写的是三十箱。", False, "en la hoja decía treinta y dos —— 三十二箱"),
    ("今天就得给供应商打电话。", False, "Mañana tengo que llamar al proveedor —— 明天"),
]
C["HABLA"] = [
    "「得检查所有箱子。」（不说谁）→ ______ revisar todas las cajas.",
    "「卡车已经满了。」→ El camión ya ______ ______.",
    "「我得做什么？」（问老板）→ ¿______ tengo que hacer?",
]
C["ESCRITO"] = {
    "titulo": "Un problema en la bodega",
    "pide": "这次<b>不给原形了</b>，括号里只有意思。每个空填<b>一个词</b>（为什么填两个词），句子跟③的短文很像，可以照着套。",
    "lineas": [
        ["Hoy el camión ______ a las ______ .", "到了（那一次）· 几点"],
        ["Faltan ______ cajas.", "数字用字母写"],
        ["Una caja ______ dañada.", "状态：是…的"],
        ["Mi jefe me dijo: «¿ ______ faltan?»", "为什么"],
        ["Mañana ______ llamar al proveedor.", "得（不说谁）"],
        ["Yo ______ contar todo otra vez.", "我得（现在）"],
    ],
}
construir(C, "d1029")
