import json
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
        "node_ok": "🟢 {name}: block {block}, {ms} ms",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "No nodes in list!",
        "status_header": "📡 Arc node status:\n",
        "start_help": "Sentinel v2.5. Commands: /status — dashboard; /ping — check now; /best — fastest; /lang xx — language; /help — this help",
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
        "best_ok": "⚡ Fastest node: {name} — {ms} ms (block {block})",
        "best_none": "No alive nodes right now.",
    },
    "ru": {
        "node_ok": "🟢 {name}: блок {block}, {ms} мс",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "Список нод пуст!",
        "status_header": "📡 Статус нод Arc:\n",
        "start_help": "Я Sentinel v2.5. Команды: /status — дашборд; /ping — проверка; /best — самая быстрая; /lang xx — язык; /help — помощь",
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
        "best_ok": "⚡ Самая быстрая нода: {name} — {ms} мс (блок {block})",
        "best_none": "Сейчас нет живых нод.",
    },
    "zh": {
        "node_ok": "🟢 {name}：区块 {block}，{ms} 毫秒",
        "node_bad": "🔴 {name}：{err}",
        "nodes_empty": "节点列表为空！",
        "status_header": "📡 Arc 节点状态：\n",
        "start_help": "Sentinel v2.5。命令：/status — 面板；/ping — 立即检查；/best — 最快；/lang xx — 语言；/help — 帮助",
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
        "best_ok": "⚡ 最快节点：{name} — {ms} 毫秒（区块 {block}）",
        "best_none": "当前没有可用节点。",
    },
    "hi": {
        "node_ok": "🟢 {name}: ब्लॉक {block}, {ms} मि.से.",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "नोड सूची खाली है!",
        "status_header": "📡 Arc नोड स्थिति:\n",
        "start_help": "Sentinel v2.5। कमांड: /status — डैशबोर्ड; /ping — अभी जांचें; /best — सबसे तेज; /lang xx — भाषा; /help — मदद",
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
        "best_ok": "⚡ सबसे तेज नोड: {name} — {ms} मि.से. (ब्लॉक {block})",
        "best_none": "अभी कोई सक्रिय नोड नहीं है।",
    },
    "es": {
        "node_ok": "🟢 {name}: bloque {block}, {ms} ms",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "¡La lista de nodos está vacía!",
        "status_header": "📡 Estado de los nodos Arc:\n",
        "start_help": "Sentinel v2.5. Comandos: /status — panel; /ping — comprobar ahora; /best — más rápido; /lang xx — idioma; /help — ayuda",
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
        "best_ok": "⚡ Nodo más rápido: {name} — {ms} ms (bloque {block})",
        "best_none": "No hay nodos activos ahora mismo.",
    },
    "fr": {
        "node_ok": "🟢 {name} : bloc {block}, {ms} ms",
        "node_bad": "🔴 {name} : {err}",
        "nodes_empty": "La liste des nœuds est vide !",
        "status_header": "📡 État des nœuds Arc :\n",
        "start_help": "Sentinel v2.5. Commandes : /status — tableau ; /ping — vérifier ; /best — plus rapide ; /lang xx — langue ; /help — aide",
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
        "best_ok": "⚡ Nœud le plus rapide : {name} — {ms} ms (bloc {block})",
        "best_none": "Aucun nœud actif pour le moment.",
    },
    "ar": {
        "node_ok": "🟢 {name}: الكتلة {block}، {ms} مللي ثانية",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "قائمة العقد فارغة!",
        "status_header": "📡 حالة عقد Arc:\n",
        "start_help": "Sentinel v2.5. الأوامر: /status — اللوحة؛ /ping — فحص الآن؛ /best — الأسرع؛ /lang xx — اللغة؛ /help — المساعدة",
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
        "best_ok": "⚡ أسرع عقدة: {name} — {ms} مللي ثانية (الكتلة {block})",
        "best_none": "لا توجد عقدة متصلة الآن.",
    },
    "pt": {
        "node_ok": "🟢 {name}: bloco {block}, {ms} ms",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "A lista de nós está vazia!",
        "status_header": "📡 Status dos nós Arc:\n",
        "start_help": "Sentinel v2.5. Comandos: /status — painel; /ping — verificar agora; /best — mais rápido; /lang xx — idioma; /help — ajuda",
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
        "best_ok": "⚡ Nó mais rápido: {name} — {ms} ms (bloco {block})",
        "best_none": "Não há nós ativos no momento.",
    },
    "ja": {
        "node_ok": "🟢 {name}: ブロック {block}、{ms} ms",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "ノード一覧が空です！",
        "status_header": "📡 Arc ノードの状態：\n",
        "start_help": "Sentinel v2.5。コマンド：/status — ダッシュボード；/ping — 今すぐ確認；/best — 最速；/lang xx — 言語；/help — ヘルプ",
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
        "best_ok": "⚡ 最速ノード：{name} — {ms} ms（ブロック {block}）",
        "best_none": "現在、稼働中のノードはありません。",
    },
    "de": {
        "node_ok": "🟢 {name}: Block {block}, {ms} ms",
        "node_bad": "🔴 {name}: {err}",
        "nodes_empty": "Die Node-Liste ist leer!",
        "status_header": "📡 Arc-Node-Status:\n",
        "start_help": "Sentinel v2.5. Befehle: /status — Dashboard; /ping — jetzt prüfen; /best — schnellste; /lang xx — Sprache; /help — Hilfe",
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
        "best_ok": "⚡ Schnellste Node: {name} — {ms} ms (Block {block})",
        "best_none": "Derzeit sind keine Nodes aktiv.",
    },
}

def tr(key, **values):
    return STR[CURRENT_LANG][key].format(**values)

def _post(url, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.load(r)

def ping(url):
    t0 = time.time()
    data = _post(url, {"jsonrpc": "2.0", "method": "eth_blockNumber",
                       "params": [], "id": 1})
    if "result" not in data:
        raise RuntimeError("bad response")
    return int(data["result"], 16), int((time.time() - t0) * 1000)

def tg(text):
    try:
        _post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
              {"chat_id": CHAT_ID, "text": text})
    except Exception as e:
        print("TG send error:", e)

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
    lines = []
    for name, r in res.items():
        if r["ok"]:
            lines.append(tr("node_ok", name=name, block=r["block"], ms=r["ms"]))
        else:
            lines.append(tr("node_bad", name=name, err=r["err"]))
    return "\n".join(lines) if lines else tr("nodes_empty")

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
        msg  = up.get("message") or {}
        chat = (msg.get("chat") or {}).get("id")
        text = (msg.get("text") or "").strip()
        if str(chat) == str(CHAT_ID):
            if text == "/status":
                tg(tr("status_header") + status_lines(LAST_RESULT))
            elif text == "/ping":
                res = check_and_alert()
                tg(tr("status_header") + status_lines(res))
            elif text == "/best":
                alive = [
                    (r["ms"], name, r["block"])
                    for name, r in LAST_RESULT.items()
                    if r["ok"]
                ]
                if alive:
                    ms, name, block = min(alive)
                    tg(tr("best_ok", name=name, ms=ms, block=block))
                else:
                    tg(tr("best_none"))
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
                tg(tr("start_help"))

def main():
    global LAST_RESULT, PREV_STATE, NET_ALIVE
    flush_old_updates()
    res = check_all()
    LAST_RESULT = res
    head = (tr("started_alive")
            if first_alive(res)
            else tr("started_down"))
    tg(head + "\n" + status_lines(res) + "\n\n" + tr("command_hint"))
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