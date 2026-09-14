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
            lines.append(f"🟢 {name}: блок {r['block']}, {r['ms']} мс")
        else:
            lines.append(f"🔴 {name}: {r['err']}")
    return "\n".join(lines) if lines else "Список нод пуст!"

def first_alive(res):
    for name, r in res.items():
        if r["ok"]:
            return name
    return None

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
    global UPDATE_OFFSET
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
                tg("📡 Статус нод Arc:\n" + status_lines(res))
            elif text in ("/start", "/help"):
                tg("Я Sentinel v2.1. Команда: /status — дашборд нод")

def main():
    global LAST_RESULT
    flush_old_updates()
    res = check_all()
    LAST_RESULT = res
    head = ("🟢 Sentinel v2.1 запущен!"
            if first_alive(res)
            else "🟡 Sentinel v2.1 запущен, но ВСЕ ноды уже лежат!")
    tg(head + "\n" + status_lines(res) + "\n\nКоманда: /status")
    prev      = {n: r["ok"] for n, r in res.items()}
    net_alive = any(prev.values())
    cycles    = 0
    while True:
        for _ in range(CHECK_EVERY // 15):
            time.sleep(15)
            handle_commands(LAST_RESULT)
        cycles += 1
        try:
            handle_commands(LAST_RESULT)
            res = check_all()
            LAST_RESULT = res
            cur = {n: r["ok"] for n, r in res.items()}
            for n in cur:
                if cur[n] != prev.get(n):
                    if cur[n]:
                        tg(f"🟢 Нода {n} ожила! Блок {res[n]['block']}, {res[n]['ms']} мс")
                    else:
                        tg(f"🔴 Нода {n} умерла! ({res[n]['err']})")
            now_net = any(cur.values())
            if now_net != net_alive:
                if now_net:
                    tg(f"🟢 Сеть Arc снова жива! Работаем через ноду {first_alive(res)}.")
                else:
                    tg("🚨 ВСЕ ноды Arc лежат! Это аутаж сети, а не каприз одного RPC.")
                net_alive = now_net
            prev = cur
            if cycles % HEARTBEAT_EVERY == 0:
                tg(f"💓 Sentinel жив, цикл #{cycles}\n" + status_lines(res))
        except Exception as e:
            print("cycle error:", e)

main()