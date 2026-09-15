import json
import html
import os
import sys
import time
import urllib.request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID   = os.environ.get("CHAT_ID")
if not BOT_TOKEN or not CHAT_ID:
    sys.exit("ОШИБКА: задайте BOT_TOKEN и CHAT_ID в Secrets Replit")

NODES = {
    "arc-official": "https://rpc.testnet.arc.io",
    "blockdaemon":  "https://rpc.blockdaemon.testnet.arc.io",
    "drpc":         "https://rpc.drpc.testnet.arc.io",
    "quicknode":    "https://rpc.quicknode.testnet.arc.io",
}
ALCHEMY_KEY = os.environ.get("ALCHEMY_KEY")
if ALCHEMY_KEY:
    NODES["alchemy"] = f"https://arc-testnet.g.alchemy.com/v2/{ALCHEMY_KEY}"

CHECK_EVERY     = 300
TIMEOUT         = 6
HEARTBEAT_EVERY = 12

UPDATE_OFFSET = 0
LAST_RESULT   = {}
PREV_STATE    = {}
NET_ALIVE     = False
CURRENT_LANG  = "ru"
LANG_SET      = False

STR = {
    "en": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · block {block} · {ms} ms",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "No nodes in list!",
        "status_header": "📡 Arc node status:\n",
        "start_help": "Sentinel v2.5. Commands: /status — dashboard; /ping — check now; /best — fastest; /lang xx — language; /help — this help",
        "credit": "👤 Created by testnetter",
        "started_alive": "🟢 Sentinel v2.5 started!",
        "started_down": "🟡 Sentinel v2.5 started, but ALL nodes are down!",
        "command_hint": "Command: /status",
        "node_up": "🟢 Node {name} is back! Block {block}, {ms} ms",
        "node_down": "🔴 Node {name} is down! ({err})",
        "network_up": "🟢 Arc network is alive again! Working through node {name}.",
        "network_down": "🚨 ALL Arc nodes are down! This is a network outage, not a single RPC issue.",
        "heartbeat": "💓 Sentinel alive, cycle #{cycles}\n",
        "lang_bad": "Unknown language. Available codes: {codes}",
        "lang_cur": "Current language: {lang}. Available codes: {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} ms</code> (block {block})",
        "best_none": "No alive nodes right now.",
    },
    "ru": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · блок {block} · {ms} мс",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "Список нод пуст!",
        "status_header": "📡 Статус нод Arc:\n",
        "start_help": "Я Sentinel v2.5. Команды: /status — дашборд; /ping — проверка; /best — самая быстрая; /lang xx — язык; /help — помощь",
        "credit": "👤 Создатель: testnetter",
        "started_alive": "🟢 Sentinel v2.5 запущен!",
        "started_down": "🟡 Sentinel v2.5 запущен, но ВСЕ ноды уже лежат!",
        "command_hint": "Команда: /status",
        "node_up": "🟢 Нода {name} ожила! Блок {block}, {ms} мс",
        "node_down": "🔴 Нода {name} умерла! ({err})",
        "network_up": "🟢 Сеть Arc снова жива! Работаем через ноду {name}.",
        "network_down": "🚨 ВСЕ ноды Arc лежат! Это аутаж сети, а не каприз одного RPC.",
        "heartbeat": "💓 Sentinel жив, цикл #{cycles}\n",
        "lang_bad": "Неверный язык. Доступные коды: {codes}",
        "lang_cur": "Текущий язык: {lang}. Доступные коды: {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} мс</code> (блок {block})",
        "best_none": "Сейчас нет живых нод.",
    },
    "zh": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · 区块 {block} · {ms} 毫秒",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "节点列表为空！",
        "status_header": "📡 Arc 节点状态：\n",
        "start_help": "Sentinel v2.5。命令：/status — 面板；/ping — 立即检查；/best — 最快；/lang xx — 语言；/help — 帮助",
        "credit": "👤 创作者: testnetter",
        "started_alive": "🟢 Sentinel v2.5 已启动！",
        "started_down": "🟡 Sentinel v2.5 已启动，但所有节点都已宕机！",
        "command_hint": "命令：/status",
        "node_up": "🟢 节点 {name} 已恢复！区块 {block}，{ms} 毫秒",
        "node_down": "🔴 节点 {name} 已宕机！（{err}）",
        "network_up": "🟢 Arc 网络恢复！当前使用节点 {name}。",
        "network_down": "🚨 Arc 所有节点都已宕机！这是网络故障，不是单个 RPC 的问题。",
        "heartbeat": "💓 Sentinel 运行正常，周期 #{cycles}\n",
        "lang_bad": "未知语言。可用代码：{codes}",
        "lang_cur": "当前语言：{lang}。可用代码：{codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} 毫秒</code>（区块 {block}）",
        "best_none": "当前没有可用节点。",
    },
    "hi": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · ब्लॉक {block} · {ms} मि.से.",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "नोड सूची खाली है!",
        "status_header": "📡 Arc नोड स्थिति:\n",
        "start_help": "Sentinel v2.5। कमांड: /status — डैशबोर्ड; /ping — अभी जांचें; /best — सबसे तेज; /lang xx — भाषा; /help — मदद",
        "credit": "👤 निर्माता: testnetter",
        "started_alive": "🟢 Sentinel v2.5 शुरू हो गया!",
        "started_down": "🟡 Sentinel v2.5 शुरू हो गया, लेकिन सभी नोड बंद हैं!",
        "command_hint": "कमांड: /status",
        "node_up": "🟢 नोड {name} वापस आ गया! ब्लॉक {block}, {ms} मि.से.",
        "node_down": "🔴 नोड {name} बंद है! ({err})",
        "network_up": "🟢 Arc नेटवर्क फिर से चालू है! नोड {name} के जरिए काम कर रहे हैं।",
        "network_down": "🚨 Arc के सभी नोड बंद हैं! यह नेटवर्क आउटेज है, किसी एक RPC की समस्या नहीं।",
        "heartbeat": "💓 Sentinel चालू है, चक्र #{cycles}\n",
        "lang_bad": "अज्ञात भाषा। उपलब्ध कोड: {codes}",
        "lang_cur": "वर्तमान भाषा: {lang}। उपलब्ध कोड: {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} मि.से.</code> (ब्लॉक {block})",
        "best_none": "अभी कोई सक्रिय नोड नहीं है।",
    },
    "es": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · bloque {block} · {ms} ms",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "¡La lista de nodos está vacía!",
        "status_header": "📡 Estado de los nodos Arc:\n",
        "start_help": "Sentinel v2.5. Comandos: /status — panel; /ping — comprobar ahora; /best — más rápido; /lang xx — idioma; /help — ayuda",
        "credit": "👤 Creado por testnetter",
        "started_alive": "🟢 ¡Sentinel v2.5 iniciado!",
        "started_down": "🟡 Sentinel v2.5 iniciado, ¡pero todos los nodos están caídos!",
        "command_hint": "Comando: /status",
        "node_up": "🟢 ¡El nodo {name} volvió! Bloque {block}, {ms} ms",
        "node_down": "🔴 ¡El nodo {name} está caído! ({err})",
        "network_up": "🟢 ¡La red Arc vuelve a estar activa! Trabajamos con el nodo {name}.",
        "network_down": "🚨 ¡Todos los nodos Arc están caídos! Es una interrupción de red, no un problema de un RPC.",
        "heartbeat": "💓 Sentinel activo, ciclo #{cycles}\n",
        "lang_bad": "Idioma desconocido. Códigos disponibles: {codes}",
        "lang_cur": "Idioma actual: {lang}. Códigos disponibles: {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} ms</code> (bloque {block})",
        "best_none": "No hay nodos activos ahora mismo.",
    },
    "fr": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · bloc {block} · {ms} ms",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "La liste des nœuds est vide !",
        "status_header": "📡 État des nœuds Arc :\n",
        "start_help": "Sentinel v2.5. Commandes : /status — tableau ; /ping — vérifier ; /best — plus rapide ; /lang xx — langue ; /help — aide",
        "credit": "👤 Créé par testnetter",
        "started_alive": "🟢 Sentinel v2.5 est lancé !",
        "started_down": "🟡 Sentinel v2.5 est lancé, mais tous les nœuds sont hors service !",
        "command_hint": "Commande : /status",
        "node_up": "🟢 Le nœud {name} est de nouveau actif ! Bloc {block}, {ms} ms",
        "node_down": "🔴 Le nœud {name} est hors service ! ({err})",
        "network_up": "🟢 Le réseau Arc est de nouveau actif ! Utilisation du nœud {name}.",
        "network_down": "🚨 Tous les nœuds Arc sont hors service ! C’est une panne réseau, pas un problème RPC isolé.",
        "heartbeat": "💓 Sentinel est actif, cycle n°{cycles}\n",
        "lang_bad": "Langue inconnue. Codes disponibles : {codes}",
        "lang_cur": "Langue actuelle : {lang}. Codes disponibles : {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} ms</code> (bloc {block})",
        "best_none": "Aucun nœud actif pour le moment.",
    },
    "ar": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · الكتلة {block} · {ms} مللي ثانية",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "قائمة العقد فارغة!",
        "status_header": "📡 حالة عقد Arc:\n",
        "start_help": "Sentinel v2.5. الأوامر: /status — اللوحة؛ /ping — فحص الآن؛ /best — الأسرع؛ /lang xx — اللغة؛ /help — المساعدة",
        "credit": "👤 أنشأه testnetter",
        "started_alive": "🟢 تم تشغيل Sentinel v2.5!",
        "started_down": "🟡 تم تشغيل Sentinel v2.5، لكن جميع العقد متوقفة!",
        "command_hint": "الأمر: /status",
        "node_up": "🟢 عادت العقدة {name}! الكتلة {block}، {ms} مللي ثانية",
        "node_down": "🔴 العقدة {name} متوقفة! ({err})",
        "network_up": "🟢 عادت شبكة Arc للعمل! نستخدم العقدة {name}.",
        "network_down": "🚨 جميع عقد Arc متوقفة! هذا عطل في الشبكة، وليس مشكلة RPC واحدة.",
        "heartbeat": "💓 Sentinel يعمل، الدورة #{cycles}\n",
        "lang_bad": "لغة غير معروفة. الرموز المتاحة: {codes}",
        "lang_cur": "اللغة الحالية: {lang}. الرموز المتاحة: {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} مللي ثانية</code> (الكتلة {block})",
        "best_none": "لا توجد عقدة متصلة الآن.",
    },
    "pt": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · bloco {block} · {ms} ms",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "A lista de nós está vazia!",
        "status_header": "📡 Status dos nós Arc:\n",
        "start_help": "Sentinel v2.5. Comandos: /status — painel; /ping — verificar agora; /best — mais rápido; /lang xx — idioma; /help — ajuda",
        "credit": "👤 Criado por testnetter",
        "started_alive": "🟢 Sentinel v2.5 iniciado!",
        "started_down": "🟡 Sentinel v2.5 iniciado, mas todos os nós estão fora do ar!",
        "command_hint": "Comando: /status",
        "node_up": "🟢 O nó {name} voltou! Bloco {block}, {ms} ms",
        "node_down": "🔴 O nó {name} caiu! ({err})",
        "network_up": "🟢 A rede Arc está ativa novamente! Usando o nó {name}.",
        "network_down": "🚨 Todos os nós Arc estão fora do ar! É uma falha de rede, não de um único RPC.",
        "heartbeat": "💓 Sentinel ativo, ciclo #{cycles}\n",
        "lang_bad": "Idioma desconhecido. Códigos disponíveis: {codes}",
        "lang_cur": "Idioma atual: {lang}. Códigos disponíveis: {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} ms</code> (bloco {block})",
        "best_none": "Não há nós ativos no momento.",
    },
    "ja": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · ブロック {block} · {ms} ms",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "ノード一覧が空です！",
        "status_header": "📡 Arc ノードの状態：\n",
        "start_help": "Sentinel v2.5。コマンド：/status — ダッシュボード；/ping — 今すぐ確認；/best — 最速；/lang xx — 言語；/help — ヘルプ",
        "credit": "👤 作者: testnetter",
        "started_alive": "🟢 Sentinel v2.5 を起動しました！",
        "started_down": "🟡 Sentinel v2.5 を起動しましたが、すべてのノードが停止中です！",
        "command_hint": "コマンド：/status",
        "node_up": "🟢 ノード {name} が復旧しました！ブロック {block}、{ms} ms",
        "node_down": "🔴 ノード {name} が停止しました！（{err}）",
        "network_up": "🟢 Arc ネットワークが復旧しました！ノード {name} を使用中です。",
        "network_down": "🚨 Arc の全ノードが停止中です！単一 RPC ではなくネットワーク障害です。",
        "heartbeat": "💓 Sentinel は稼働中、サイクル #{cycles}\n",
        "lang_bad": "不明な言語です。利用可能なコード：{codes}",
        "lang_cur": "現在の言語：{lang}。利用可能なコード：{codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} ms</code>（ブロック {block}）",
        "best_none": "現在、稼働中のノードはありません。",
    },
    "de": {
        "node_ok": "🟢 <a href=\"{url}\">{name}</a> · Block {block} · {ms} ms",
        "node_bad": "🔴 <a href=\"{url}\">{name}</a> · {err}",
        "nodes_empty": "Die Node-Liste ist leer!",
        "status_header": "📡 Arc-Node-Status:\n",
        "start_help": "Sentinel v2.5. Befehle: /status — Dashboard; /ping — jetzt prüfen; /best — schnellste; /lang xx — Sprache; /help — Hilfe",
        "credit": "👤 Erstellt von testnetter",
        "started_alive": "🟢 Sentinel v2.5 gestartet!",
        "started_down": "🟡 Sentinel v2.5 gestartet, aber ALLE Nodes sind ausgefallen!",
        "command_hint": "Befehl: /status",
        "node_up": "🟢 Node {name} ist wieder da! Block {block}, {ms} ms",
        "node_down": "🔴 Node {name} ist ausgefallen! ({err})",
        "network_up": "🟢 Das Arc-Netzwerk ist wieder aktiv! Wir arbeiten über Node {name}.",
        "network_down": "🚨 ALLE Arc-Nodes sind ausgefallen! Das ist ein Netzwerkausfall, kein einzelnes RPC-Problem.",
        "heartbeat": "💓 Sentinel läuft, Zyklus #{cycles}\n",
        "lang_bad": "Unbekannte Sprache. Verfügbare Codes: {codes}",
        "lang_cur": "Aktuelle Sprache: {lang}. Verfügbare Codes: {codes}",
        "best_ok": "⚡ <b><a href=\"{url}\">{name}</a></b> — <code>{ms} ms</code> (Block {block})",
        "best_none": "Derzeit sind keine Nodes aktiv.",
    },
}

def tr(key, **values):
    return STR[CURRENT_LANG][key].format(**values)

MAIN_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "📡 Status", "callback_data": "status"},
            {"text": "⚡ Ping", "callback_data": "ping"},
            {"text": "🏆 Best", "callback_data": "best"},
        ],
        [
            {"text": "🇷🇺 RU", "callback_data": "lang_ru"},
            {"text": "🇬🇧 EN", "callback_data": "lang_en"},
        ],
    ]
}

def _post(url, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "arc-rpc-sentinel/2.6",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)

def ping(url):
    t0 = time.time()
    data = _post(url, {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_blockNumber",
        "params": [],
    })
    if "result" not in data:
        raise RuntimeError("bad response")
    return int(data["result"], 16), int((time.time() - t0) * 1000)

def tg(text, reply_markup=None):
    try:
        payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        _post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
              payload)
    except Exception as e:
        print("TG send error:", e)

def answer_callback(callback_id):
    if not callback_id:
        return
    try:
        _post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery",
              {"callback_query_id": callback_id})
    except Exception as e:
        print("TG callback error:", e)

def check_all():
    out = {}
    for name, url in NODES.items():
        try:
            block, ms = ping(url)
            out[name] = {"ok": True, "block": block, "ms": ms, "err": None}
        except Exception as e:
            out[name] = {"ok": False, "block": None, "ms": None,
                         "err": type(e).__name__}
    return out

def status_lines(res):
    lines = [f"<b>{html.escape(tr('status_header').strip())}</b>", "--------------------"]
    for name, r in res.items():
        values = {
            "url": html.escape(NODES[name], quote=True),
            "name": html.escape(name),
        }
        if r["ok"]:
            values.update(block=r["block"], ms=r["ms"])
            lines.append(tr("node_ok", **values))
        else:
            values["err"] = html.escape(str(r["err"]))
            lines.append(tr("node_bad", **values))
    if not res:
        lines.append(tr("nodes_empty"))
    return "\n".join(lines)

def first_alive(res):
    for name, r in res.items():
        if r["ok"]:
            return name
    return None

def check_and_alert():
    global LAST_RESULT, PREV_STATE, NET_ALIVE
    res = check_all()
    LAST_RESULT = res
    cur = {n: r["ok"] for n, r in res.items()}
    for n in cur:
        if cur[n] != PREV_STATE.get(n):
            if cur[n]:
                tg(tr("node_up", name=n, block=res[n]["block"], ms=res[n]["ms"]))
            else:
                tg(tr("node_down", name=n, err=res[n]["err"]))
    now_net = any(cur.values())
    if now_net != NET_ALIVE:
        if now_net:
            tg(tr("network_up", name=first_alive(res)))
        else:
            tg(tr("network_down"))
        NET_ALIVE = now_net
    PREV_STATE = cur
    return res

def send_best():
    alive = [
        (r["ms"], name, r["block"])
        for name, r in LAST_RESULT.items()
        if r["ok"]
    ]
    if alive:
        ms, name, block = min(alive)
        tg(tr(
            "best_ok",
            name=html.escape(name),
            url=html.escape(NODES[name], quote=True),
            ms=ms,
            block=block,
        ))
    else:
        tg(tr("best_none"))

def flush_old_updates():
    global UPDATE_OFFSET
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset=-1&timeout=0"
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            data = json.load(r)
        ups = data.get("result", [])
        if ups:
            UPDATE_OFFSET = ups[-1]["update_id"] + 1
    except Exception as e:
        print("flush error:", e)

def handle_commands(res):
    global UPDATE_OFFSET, CURRENT_LANG, LANG_SET
    url = (f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
           f"?offset={UPDATE_OFFSET}&timeout=0")
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as r:
            data = json.load(r)
    except Exception as e:
        print("getUpdates error:", e)
        return
    for up in data.get("result", []):
        UPDATE_OFFSET = up["update_id"] + 1
        callback = up.get("callback_query")
        if callback:
            msg = callback.get("message") or {}
            chat = (msg.get("chat") or {}).get("id")
            action = callback.get("data")
            if str(chat) == str(CHAT_ID):
                answer_callback(callback.get("id"))
                if action == "status":
                    tg(status_lines(LAST_RESULT))
                elif action == "ping":
                    tg(status_lines(check_and_alert()))
                elif action == "best":
                    send_best()
                elif action == "lang_ru":
                    CURRENT_LANG = "ru"
                    LANG_SET = True
                    tg(tr("lang_cur", lang=CURRENT_LANG, codes=", ".join(STR.keys())))
                elif action == "lang_en":
                    CURRENT_LANG = "en"
                    LANG_SET = True
                    tg(tr("lang_cur", lang=CURRENT_LANG, codes=", ".join(STR.keys())))
            continue
        msg  = up.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        text = (msg.get("text") or "").strip()
        if str(chat) == str(CHAT_ID):
            if text == "/status":
                tg(status_lines(LAST_RESULT))
            elif text == "/ping":
                tg(status_lines(check_and_alert()))
            elif text == "/best":
                send_best()
            elif text == "/lang" or text.startswith("/lang "):
                parts = text.split()
                codes = ", ".join(STR.keys())
                if len(parts) < 2:
                    tg(tr("lang_cur", lang=CURRENT_LANG, codes=codes))
                else:
                    lang = parts[1].lower()
                    if lang not in STR:
                        tg(tr("lang_bad", codes=codes))
                    else:
                        CURRENT_LANG = lang
                        LANG_SET = True
                        tg(tr("lang_cur", lang=CURRENT_LANG, codes=codes))
            elif text in ("/start", "/help"):
                if text == "/start" and not LANG_SET:
                    sender_lang = ((msg.get("from") or {}).get("language_code") or "").lower().split("-")[0]
                    if sender_lang in STR:
                        CURRENT_LANG = sender_lang
                        LANG_SET = True
                tg(tr("start_help") + "\n" + tr("credit"), MAIN_KEYBOARD)

def main():
    global LAST_RESULT, PREV_STATE, NET_ALIVE
    flush_old_updates()
    res = check_all()
    LAST_RESULT = res
    head = (tr("started_alive")
            if first_alive(res)
            else tr("started_down"))
    tg(head + "\n" + status_lines(res) + "\n\n" + tr("command_hint") + "\n" + tr("credit"))
    PREV_STATE = {n: r["ok"] for n, r in res.items()}
    NET_ALIVE = any(PREV_STATE.values())
    cycles    = 0
    while True:
        for _ in range(CHECK_EVERY // 15):
            time.sleep(15)
            handle_commands(LAST_RESULT)
        cycles += 1
        try:
            handle_commands(LAST_RESULT)
            res = check_and_alert()
            if cycles % HEARTBEAT_EVERY == 0:
                tg(tr("heartbeat", cycles=cycles) + status_lines(res))
        except Exception as e:
            print("cycle error:", e)

main()