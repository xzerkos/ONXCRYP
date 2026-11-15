import re
import json
from datetime import datetime
from bs4 import BeautifulSoup
from http_client import safe_get, safe_post, get_api_key, tron_headers
from labels import get_label

_B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'

def _b58decode(s):
    n = 0
    for c in s:
        n = n * 58 + _B58.index(c)
    res = []
    while n > 0:
        res.append(n & 0xFF)
        n >>= 8
    return bytes([0] * (len(s) - len(s.lstrip('1'))) + res[::-1])

def _is_solana(a):
    if not re.fullmatch(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$', a):
        return False
    try:
        return len(_b58decode(a)) == 32
    except (ValueError, IndexError):
        return False

def detect_chain(a):
    a = a.strip()
    if re.fullmatch(r'^0x[a-fA-F0-9]{40}$', a):
        return "evm"
    if re.fullmatch(r'^T[1-9A-HJ-NP-Za-km-z]{33}$', a):
        return "trc20"
    if re.fullmatch(r'^(EQ|UQ)[A-Za-z0-9_-]{46}$', a):
        return "ton"
    if re.fullmatch(r'^bc1[a-zA-HJ-NP-Z0-9]{25,62}$', a):
        return "btc"
    if re.fullmatch(r'^[13][a-km-zA-HJ-NP-Z1-9]{25,34}$', a):
        return "btc"
    if re.fullmatch(r'^[LM][a-km-zA-HJ-NP-Z1-9]{26,33}$', a):
        return "ltc"
    if re.fullmatch(r'^D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}$', a):
        return "doge"
    if _is_solana(a):
        return "sol"
    return "unknown"

def _hdr(t):
    print("=" * 70)
    print(f"  {t}")
    print("=" * 70)

def _i(v, d=0):
    if v is None:
        return d
    try:
        return int(v)
    except (ValueError, TypeError):
        return d

def _f(v, d=0.0):
    if v is None:
        return d
    try:
        return float(v)
    except (ValueError, TypeError):
        return d

def _ts(u):
    if not u:
        return "n/a"
    try:
        return datetime.utcfromtimestamp(_i(u)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "n/a"

def _iso(s):
    if not s:
        return "n/a"
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return s[:19] if len(s) >= 19 else s

def _peers(chain, peers):
    if not peers:
        return
    print("\n--- Counterparties ---")
    for p in list(peers)[:20]:
        lbl = get_label(chain, p)
        print(f"  {p}" + (f" [{lbl}]" if lbl else ""))

def _risk_btc(n, recv, sent):
    s = 0
    if n > 1000: s += 30
    elif n > 500: s += 20
    elif n > 100: s += 10
    if recv > 100: s += 20
    elif recv > 10: s += 10
    if sent > 100: s += 20
    elif sent > 10: s += 10
    if n > 0:
        avg = (recv + sent) / n
        if avg > 1: s += 10
        elif avg < 0.001: s += 5
    return min(100, s)

def _btc(addr):
    _hdr("BITCOIN (BTC) ADDRESS ANALYSIS")
    lbl = get_label("btc", addr)
    if lbl:
        print(f"Label         : {lbl}")
    print(f"Address       : {addr}")

    data, src = None, None
    r = safe_get(f"https://blockstream.info/api/address/{addr}")
    if r and r.status_code == 200:
        try:
            d = r.json()
            cs = d.get("chain_stats", {})
            ms = d.get("mempool_stats", {})
            data = {
                "final_balance": _i(cs.get("funded_txo_sum")) - _i(cs.get("spent_txo_sum")),
                "total_received": _i(cs.get("funded_txo_sum")),
                "total_sent": _i(cs.get("spent_txo_sum")),
                "n_tx": _i(cs.get("tx_count")),
                "mempool_tx": _i(ms.get("tx_count")),
            }
            src = "Blockstream Esplora"
        except Exception:
            pass

    if data is None:
        r = safe_get(f"https://mempool.space/api/address/{addr}")
        if r and r.status_code == 200:
            try:
                d = r.json()
                cs = d.get("chain_stats", {})
                data = {
                    "final_balance": _i(cs.get("funded_txo_sum")) - _i(cs.get("spent_txo_sum")),
                    "total_received": _i(cs.get("funded_txo_sum")),
                    "total_sent": _i(cs.get("spent_txo_sum")),
                    "n_tx": _i(cs.get("tx_count")),
                }
                src = "mempool.space"
            except Exception:
                pass

    if data is None:
        r = safe_get(f"https://blockchain.info/rawaddr/{addr}", params={"limit": 50})
        if r and r.status_code == 200:
            try:
                data = r.json()
                src = "Blockchain.com"
            except Exception:
                pass

    if data is None:
        print("[!] All BTC sources failed.")
        return

    bal = _i(data.get("final_balance")) / 1e8
    recv = _i(data.get("total_received")) / 1e8
    sent = _i(data.get("total_sent")) / 1e8
    n = _i(data.get("n_tx"))
    mem = _i(data.get("mempool_tx"))

    print(f"Source        : {src}")
    print(f"Balance       : {bal:.8f} BTC")
    print(f"Total received: {recv:.8f} BTC")
    print(f"Total sent    : {sent:.8f} BTC")
    print(f"Transactions  : {n}")
    if mem:
        print(f"Unconfirmed   : {mem}")
    if n > 0:
        print(f"Avg Tx Value  : {(recv + sent) / n:.8f} BTC")
        print(f"Risk Score    : {_risk_btc(n, recv, sent)}/100 (heuristic)")

    utxo_r = safe_get(f"https://blockstream.info/api/address/{addr}/utxo")
    if utxo_r and utxo_r.status_code == 200:
        try:
            utxos = utxo_r.json()
            print(f"\n--- UTXO Forensics ---")
            print(f"Unspent Outputs: {len(utxos)}")
            total_utxo = sum(_i(u.get("value")) for u in utxos) / 1e8
            print(f"UTXO Total    : {total_utxo:.8f} BTC")
            for u in utxos[:5]:
                print(f"  {u.get('txid', '')[:20]}... vout={u.get('vout')} | {_i(u.get('value'))/1e8:.8f} BTC")
        except Exception:
            pass

    txs, txs_src = [], None
    r = safe_get(f"https://blockstream.info/api/address/{addr}/txs")
    if r and r.status_code == 200:
        try:
            txs = r.json()
            txs_src = "Blockstream"
        except Exception:
            pass

    if not txs:
        r = safe_get(f"https://blockchain.info/rawaddr/{addr}", params={"limit": 20})
        if r and r.status_code == 200:
            try:
                txs = r.json().get("txs", [])
                txs_src = "Blockchain.com"
            except Exception:
                pass

    if not txs:
        return

    print(f"\n--- Latest Transactions ({txs_src}) ---")
    peers = set()
    fee_total = 0
    in_c = 0
    out_c = 0
    for tx in txs[:10]:
        if txs_src == "Blockstream":
            txid = tx.get("txid", "")
            st = tx.get("status", {})
            ts = _ts(st.get("block_time"))
            fee = _i(tx.get("fee"))
            received = sum(_i(v.get("value")) for v in tx.get("vout", []) if v.get("scriptpubkey_address") == addr)
            spent = sum(_i((vi.get("prevout") or {}).get("value")) for vi in tx.get("vin", []) if (vi.get("prevout") or {}).get("scriptpubkey_address") == addr)
            direction = "IN" if received > spent else "OUT"
            amt = (received - spent) / 1e8
            print(f"  {ts} | {direction:3} | {abs(amt):.8f} BTC | fee {fee/1e8:.8f} | {txid[:16]}...")
            for v in tx.get("vout", []):
                pa = v.get("scriptpubkey_address")
                if pa and pa != addr:
                    peers.add(pa)
            for vi in tx.get("vin", []):
                pa = (vi.get("prevout") or {}).get("scriptpubkey_address")
                if pa and pa != addr:
                    peers.add(pa)
            if direction == "IN":
                in_c += 1
            else:
                out_c += 1
            fee_total += fee
        else:
            txid = tx.get("hash", "")
            ts = _ts(tx.get("time"))
            fee = _i(tx.get("fee"))
            res = _i(tx.get("result"))
            direction = "IN" if res > 0 else "OUT"
            print(f"  {ts} | {direction:3} | {abs(res)/1e8:.8f} BTC | fee {fee/1e8:.8f} | {txid[:16]}...")
            for inp in tx.get("inputs", []):
                pa = (inp.get("prev_out") or {}).get("addr")
                if pa and pa != addr:
                    peers.add(pa)
            for out in tx.get("out", []):
                pa = out.get("addr")
                if pa and pa != addr:
                    peers.add(pa)
            if direction == "IN":
                in_c += 1
            else:
                out_c += 1
            fee_total += fee

    print(f"\n--- Flow Summary ---")
    print(f"Incoming      : {in_c}")
    print(f"Outgoing      : {out_c}")
    print(f"Avg Fee       : {fee_total / max(1, len(txs[:10])) / 1e8:.8f} BTC")

    _peers("btc", peers)
    _btc_trace(addr, txs, txs_src)

def _btc_trace(addr, txs, txs_src):
    print("\n--- Fund Flow Tracing (Peel Chain) ---")
    visited = {addr}
    current = addr
    for hop in range(3):
        nxt, mx = None, -1
        for tx in txs:
            if txs_src == "Blockstream":
                received = sum(_i(v.get("value")) for v in tx.get("vout", []) if v.get("scriptpubkey_address") == current)
                spent = sum(_i((vi.get("prevout") or {}).get("value")) for vi in tx.get("vin", []) if (vi.get("prevout") or {}).get("scriptpubkey_address") == current)
                if received >= spent:
                    continue
                for v in tx.get("vout", []):
                    oa = v.get("scriptpubkey_address")
                    val = _i(v.get("value"))
                    if oa and oa not in visited and oa != current and val > mx:
                        mx, nxt = val, oa
            else:
                if _i(tx.get("result")) >= 0:
                    continue
                for out in tx.get("out", []):
                    oa = out.get("addr")
                    val = _i(out.get("value"))
                    if oa and oa not in visited and oa != current and val > mx:
                        mx, nxt = val, oa
        if not nxt:
            break
        lbl = get_label("btc", nxt)
        print(f"  Hop {hop+1}: {nxt} ({mx/1e8:.8f} BTC)" + (f" [{lbl}]" if lbl else ""))
        visited.add(nxt)
        current = nxt
        r = safe_get(f"https://blockstream.info/api/address/{current}/txs")
        if r and r.status_code == 200:
            try:
                txs = r.json()
                txs_src = "Blockstream"
                continue
            except Exception:
                pass
        r = safe_get(f"https://blockchain.info/rawaddr/{current}", params={"limit": 10})
        if r and r.status_code == 200:
            try:
                txs = r.json().get("txs", [])
                txs_src = "Blockchain.com"
            except Exception:
                break
        else:
            break

def _blockchair(addr, chain, name):
    _hdr(f"{name} ADDRESS ANALYSIS")
    lbl = get_label(chain, addr)
    if lbl:
        print(f"Label         : {lbl}")
    print(f"Address       : {addr}")

    r = safe_get(f"https://api.blockchair.com/{chain}/dashboards/address/{addr}",
                 params={"limit": 20})
    if r is None or r.status_code != 200:
        print("[!] Blockchair request failed.")
        return
    try:
        d = r.json().get("data", {})
        entry = d.get(addr, {})
        info = entry.get("address", {})
        txs = entry.get("transactions", [])
    except Exception:
        print("[!] Unable to parse response.")
        return

    bal = _i(info.get("balance")) / 1e8
    recv = _i(info.get("received")) / 1e8
    sent = _i(info.get("spent")) / 1e8
    cnt = _i(info.get("transaction_count"))
    utxo_cnt = _i(info.get("unspent_output_count"))

    print(f"Source        : Blockchair")
    print(f"Balance       : {bal:.8f} {name}")
    print(f"Total received: {recv:.8f} {name}")
    print(f"Total spent   : {sent:.8f} {name}")
    print(f"Transactions  : {cnt}")
    if utxo_cnt:
        print(f"UTXO Count    : {utxo_cnt}")
    if cnt > 0:
        print(f"Avg Tx Value  : {(recv + sent) / cnt:.8f} {name}")

    if txs:
        print(f"\n--- Recent Transactions ({len(txs)}) ---")
        for t in txs[:10]:
            print(f"  {t[:24]}...")

    if chain == "dogecoin":
        r2 = safe_get(f"https://dogechain.info/api/v1/address/balance/{addr}")
        if r2 and r2.status_code == 200:
            try:
                d2 = r2.json()
                if d2.get("success") == 1:
                    print(f"\nCross-check   : {d2.get('balance')} DOGE (dogechain.info)")
            except Exception:
                pass

def _ltc(a):
    _blockchair(a, "litecoin", "LITECOIN (LTC)")

def _doge(a):
    _blockchair(a, "dogecoin", "DOGECOIN (DOGE)")

def _trc20(addr):
    _hdr("TRON (TRC-20) ADDRESS ANALYSIS")
    lbl = get_label("trc20", addr)
    if lbl:
        print(f"Label         : {lbl}")
    print(f"Address       : {addr}")

    acc, src = None, None
    r = safe_get(f"https://api.trongrid.io/v1/accounts/{addr}", params={"only_confirmed": "true"})
    if r and r.status_code == 200:
        try:
            d = r.json().get("data", [])
            if d:
                acc = d[0]
                src = "TronGrid"
        except Exception:
            pass

    if acc is None:
        r = safe_get("https://apilist.tronscan.org/api/account",
                     params={"address": addr, "includeToken": "true"})
        if r and r.status_code == 200:
            try:
                d = r.json()
                if isinstance(d, dict) and "balance" in d:
                    acc = d
                    src = "apilist.tronscan.org"
            except Exception:
                pass

    if acc is None:
        r = safe_get("https://apilist.tronscanapi.com/api/account",
                     params={"address": addr}, headers=tron_headers())
        if r and r.status_code == 200:
            try:
                d = r.json()
                if isinstance(d, dict) and "balance" in d:
                    acc = d
                    src = "TronScan (key)"
            except Exception:
                pass

    if acc is None:
        r = safe_get(f"https://tronscanner.org/address/{addr}", html=True)
        if r and r.status_code == 200:
            try:
                soup = BeautifulSoup(r.text, "lxml")
                text = soup.get_text(" ", strip=True)
                m = re.search(r'([\d,\.]+)\s*TRX', text)
                if m:
                    acc = {"balance": _f(m.group(1).replace(",", "")) * 1e6}
                    src = "tronscanner.org (HTML)"
            except Exception:
                pass

    if acc is None:
        print("[!] All TRON sources failed.")
        print("[*] Set TRONSCAN_API_KEY=your_key for higher reliability.")
        return

    print(f"Source        : {src}")
    print(f"TRX Balance   : {_i(acc.get('balance'))/1e6:.6f} TRX")

    fv2 = acc.get("frozenV2")
    frozen_extra = 0
    if isinstance(fv2, list):
        for f in fv2:
            if isinstance(f, dict):
                frozen_extra += _i(f.get("amount"))
    frozen_total = _i(acc.get("frozen")) + frozen_extra
    if frozen_total:
        print(f"Frozen TRX    : {frozen_total/1e6:.6f} TRX")
    bw = acc.get("bandwidth")
    en = acc.get("energy")
    if bw or en:
        print(f"Bandwidth     : {_i(bw)}")
        print(f"Energy        : {_i(en)}")
    if acc.get("activated"):
        print(f"Activated     : True")
    else:
        print(f"Activated     : False")

    tokens = acc.get("trc20token_balances") or acc.get("tokenBalances") or []
    if tokens:
        print(f"\n--- TRC-20 Token Balances ({len(tokens)}) ---")
        for t in tokens[:15]:
            sym = t.get("tokenAbbr") or t.get("tokenName") or "TOKEN"
            dec = _i(t.get("tokenDecimal"), 6)
            amt = _i(t.get("balance")) / (10 ** dec)
            print(f"  {amt:.4f} {sym}")

    _trc20_transfers(addr)
    _tron_txs(addr)

def _trc20_transfers(addr):
    r = safe_get(f"https://api.trongrid.io/v1/accounts/{addr}/transactions/trc20",
                 params={"only_confirmed": "true", "limit": 20})
    if r is None or r.status_code != 200:
        return
    try:
        txs = r.json().get("data", [])
    except Exception:
        return
    if not txs:
        return
    print(f"\n--- TRC-20 Transfers ({len(txs)}) ---")
    peers = set()
    for tx in txs[:10]:
        ts = _ts(_i(tx.get("block_timestamp")) / 1000)
        tok = tx.get("token_info", {})
        sym = tok.get("symbol", "TOKEN")
        dec = _i(tok.get("decimals"), 6)
        val = _i(tx.get("value")) / (10 ** dec)
        frm = tx.get("from", "")
        to = tx.get("to", "")
        direction = "IN" if to == addr else "OUT"
        print(f"  {ts} | {direction:3} | {val:.4f} {sym} | {frm[:8]}... -> {to[:8]}...")
        if frm and frm != addr:
            peers.add(frm)
        if to and to != addr:
            peers.add(to)
    _peers("trc20", peers)

def _tron_txs(addr):
    r = safe_get(f"https://api.trongrid.io/v1/accounts/{addr}/transactions",
                 params={"only_confirmed": "true", "limit": 20, "order_by": "block_timestamp,desc"})
    if r is None or r.status_code != 200:
        return
    try:
        txs = r.json().get("data", [])
    except Exception:
        return
    if not txs:
        return
    print(f"\n--- Native Transactions ({len(txs)}) ---")
    type_count = {}
    peers = set()
    for tx in txs[:15]:
        raw = tx.get("raw_data", {})
        contracts = raw.get("contract", [])
        if not contracts:
            continue
        c = contracts[0]
        ctype = c.get("type", "?")
        type_count[ctype] = type_count.get(ctype, 0) + 1
        p = c.get("parameter", {}).get("value", {})
        owner = p.get("owner_address", "")
        to = p.get("to_address", "")
        amount = _i(p.get("amount")) / 1e6
        ts = _ts(_i(raw.get("timestamp")) / 1000)
        print(f"  {ts} | {ctype:15} | {amount:.6f} TRX | {owner[:8]}... -> {to[:8]}...")
        if owner and owner != addr:
            peers.add(owner)
        if to and to != addr:
            peers.add(to)
    if type_count:
        print(f"\n--- Contract Type Breakdown ---")
        for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
            print(f"  {t:20} : {c}")
    _peers("trc20", peers)

def _sol(addr):
    _hdr("SOLANA (SOL) ADDRESS ANALYSIS")
    lbl = get_label("sol", addr)
    if lbl:
        print(f"Label         : {lbl}")
    print(f"Address       : {addr}")

    rpc = "https://api.mainnet-beta.solana.com"

    r = safe_post(rpc, json_body={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [addr]})
    if r is None:
        print("[!] Solana RPC failed.")
        return
    try:
        bal = _i(r.json().get("result", {}).get("value")) / 1e9
    except Exception:
        print("[!] Unable to parse balance.")
        return
    print(f"Source        : Solana JSON-RPC")
    print(f"Balance       : {bal:.9f} SOL")

    info_r = safe_post(rpc, json_body={"jsonrpc": "2.0", "id": 1, "method": "getAccountInfo",
                                        "params": [addr, {"encoding": "base64"}]})
    if info_r:
        try:
            d = info_r.json().get("result", {}).get("value")
            if d:
                print(f"Owner Program : {d.get('owner', 'n/a')}")
                print(f"Executable    : {d.get('executable', False)}")
                print(f"Lamports      : {d.get('lamports', 0)}")
        except Exception:
            pass

    tok_r = safe_post(rpc, json_body={
        "jsonrpc": "2.0", "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [addr, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                   {"encoding": "jsonParsed"}],
    })
    if tok_r:
        try:
            data = tok_r.json().get("result", {}).get("value", [])
            if data:
                print(f"\n--- SPL Token Balances ({len(data)}) ---")
                for a in data[:15]:
                    info = a.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
                    mint = info.get("mint", "")
                    amt = info.get("tokenAmount", {}).get("uiAmountString", "0")
                    dec = info.get("tokenAmount", {}).get("decimals", 0)
                    print(f"  {mint[:20]}... | {amt} (dec {dec})")
        except Exception:
            pass

    sig_r = safe_post(rpc, json_body={
        "jsonrpc": "2.0", "id": 1,
        "method": "getSignaturesForAddress",
        "params": [addr, {"limit": 20}],
    })
    if sig_r:
        try:
            sigs = sig_r.json().get("result", [])
            if sigs:
                print(f"\n--- Recent Signatures ({len(sigs)}) ---")
                err_count = 0
                for s in sigs[:10]:
                    ts = _ts(s.get("blockTime"))
                    status = "OK" if not s.get("err") else "ERR"
                    if s.get("err"):
                        err_count += 1
                    memo = s.get("memo") or ""
                    line = f"  {ts} | {status} | {s.get('signature', '')[:20]}..."
                    if memo:
                        line += f" | memo: {memo[:20]}"
                    print(line)
                if err_count:
                    print(f"\nFailed txs    : {err_count} of {len(sigs)}")
        except Exception:
            pass

def _evm(addr, chain, name, bs_base, scan_api, key_env):
    _hdr(f"{name} ADDRESS ANALYSIS")
    lbl = get_label(chain, addr)
    if lbl:
        print(f"Label         : {lbl}")
    print(f"Address       : {addr}")

    src = None
    bal = 0.0
    tx_count = 0
    is_contract = False
    creator = None

    r = safe_get(f"{bs_base}/api/v2/addresses/{addr}")
    if r and r.status_code == 200:
        try:
            d = r.json()
            bal = _i(d.get("coin_balance")) / 1e18
            tx_count = _i(d.get("transactions_count"))
            is_contract = d.get("is_contract", False)
            creator = d.get("creator_address_hash")
            src = "Blockscout"
        except Exception:
            pass

    if src is None:
        key = get_api_key(key_env) or ""
        p = {"module": "account", "action": "balance", "address": addr, "tag": "latest"}
        if key:
            p["apikey"] = key
        r2 = safe_get(scan_api, params=p)
        if r2 and r2.status_code == 200:
            try:
                bal = _i(r2.json().get("result")) / 1e18
                src = "Etherscan/BscScan"
            except Exception:
                pass

    if src is None:
        print("[!] All EVM sources failed.")
        return

    print(f"Source        : {src}")
    print(f"Balance       : {bal:.6f} {'BNB' if chain == 'bnb' else 'ETH'}")
    print(f"Transactions  : {tx_count}")
    print(f"Is Contract   : {is_contract}")
    if creator:
        print(f"Creator       : {creator}")

    txs = []
    r = safe_get(f"{bs_base}/api/v2/addresses/{addr}/transactions")
    if r and r.status_code == 200:
        try:
            items = r.json().get("items", [])
            for it in items[:10]:
                ts = it.get("timestamp", "")
                val = _i(it.get("value")) / 1e18
                frm = (it.get("from") or {}).get("hash", "")
                to = (it.get("to") or {}).get("hash", "")
                txs.append({"ts": ts, "val": val, "from": frm, "to": to})
        except Exception:
            pass

    if txs:
        print(f"\n--- Latest Transactions ({len(txs)}) ---")
        peers = set()
        in_c = 0
        out_c = 0
        for tx in txs[:10]:
            ts = _iso(tx["ts"])
            direction = "IN" if tx["to"].lower() == addr.lower() else "OUT"
            if direction == "IN":
                in_c += 1
            else:
                out_c += 1
            print(f"  {ts} | {direction:3} | {tx['val']:.6f} | {tx['from'][:10]}... -> {tx['to'][:10]}...")
            if tx["from"] and tx["from"].lower() != addr.lower():
                peers.add(tx["from"])
            if tx["to"] and tx["to"].lower() != addr.lower():
                peers.add(tx["to"])
        print(f"\n--- Flow Summary ---")
        print(f"Incoming      : {in_c}")
        print(f"Outgoing      : {out_c}")
        _peers(chain, peers)

    tok_r = safe_get(f"{bs_base}/api/v2/addresses/{addr}/token-transfers")
    if tok_r and tok_r.status_code == 200:
        try:
            items = tok_r.json().get("items", [])
            if items:
                print(f"\n--- Token Transfers ({len(items)}) ---")
                for it in items[:10]:
                    tok = it.get("token", {})
                    sym = tok.get("symbol", "TOKEN")
                    dec = _i(tok.get("decimals"), 18)
                    val = _i(it.get("total", {}).get("value")) / (10 ** dec)
                    frm = (it.get("from") or {}).get("hash", "")
                    to = (it.get("to") or {}).get("hash", "")
                    print(f"  {sym}: {val:.4f} | {frm[:8]}... -> {to[:8]}...")
        except Exception:
            pass

    nft_r = safe_get(f"{bs_base}/api/v2/addresses/{addr}/nft")
    if nft_r and nft_r.status_code == 200:
        try:
            items = nft_r.json().get("items", [])
            if items:
                print(f"\n--- NFT Holdings ({len(items)}) ---")
                for it in items[:5]:
                    tok = it.get("token", {})
                    print(f"  {tok.get('name', 'NFT')[:30]} | #{tok.get('id', '?')}")
        except Exception:
            pass

def _eth(a):
    _evm(a, "eth", "ETHEREUM (ETH)", "https://eth.blockscout.com",
         "https://api.etherscan.io/api", "ETHERSCAN_API_KEY")

def _bnb(a):
    _evm(a, "bnb", "BNB SMART CHAIN (BSC)", "https://bsc.blockscout.com",
         "https://api.bscscan.com/api", "BSCSCAN_API_KEY")

def _ton(addr, name="TON"):
    _hdr(f"{name} ADDRESS ANALYSIS")
    lbl = get_label(name.lower(), addr)
    if lbl:
        print(f"Label         : {lbl}")
    print(f"Address       : {addr}")

    got = False
    r = safe_get("https://toncenter.com/api/v3/accountStates", params={"address": addr})
    if r and r.status_code == 200:
        try:
            st = r.json().get("accounts", [])
            if st:
                s = st[0]
                print(f"Source        : TON Center")
                print(f"Balance       : {_i(s.get('balance'))/1e9:.4f} {name}")
                print(f"Status        : {s.get('status', 'unknown')}")
                if s.get("last_transaction_lt"):
                    print(f"Last LT       : {s.get('last_transaction_lt')}")
                got = True
        except Exception:
            pass

    if not got:
        r = safe_get(f"https://tonapi.io/v2/accounts/{addr}")
        if r and r.status_code == 200:
            try:
                d = r.json()
                print(f"Source        : tonapi.io")
                print(f"Balance       : {_i(d.get('balance'))/1e9:.4f} {name}")
                print(f"Status        : {d.get('status', 'unknown')}")
                got = True
            except Exception:
                pass

    if not got:
        r = safe_get(f"https://tonscan.org/address/{addr}", html=True)
        if r and r.status_code == 200:
            try:
                soup = BeautifulSoup(r.text, "lxml")
                m = re.search(r'([\d,\.]+)\s*TON', soup.get_text(" ", strip=True))
                if m:
                    print(f"Source        : tonscan.org")
                    print(f"Balance       : {m.group(1)} {name}")
                    got = True
            except Exception:
                pass

    if not got:
        print("[!] All TON sources failed.")
        return

    jet_r = safe_get("https://toncenter.com/api/v3/jetton/wallets",
                     params={"owner_address": addr, "limit": 10, "exclude_zero_balance": "true"})
    if jet_r and jet_r.status_code == 200:
        try:
            js = jet_r.json().get("jetton_wallets", [])
            if js:
                print(f"\n--- Jetton Balances ({len(js)}) ---")
                for j in js[:10]:
                    print(f"  {j.get('jetton', '')[:20]}... | {j.get('balance', '0')}")
        except Exception:
            pass

    tx_r = safe_get("https://toncenter.com/api/v3/transactions",
                    params={"address": addr, "limit": 15})
    if tx_r and tx_r.status_code == 200:
        try:
            txs = tx_r.json().get("transactions", [])
            if txs:
                print(f"\n--- Latest Transactions ({len(txs)}) ---")
                peers = set()
                in_c = 0
                out_c = 0
                for tx in txs[:10]:
                    ts = _ts(tx.get("now"))
                    m = tx.get("in_msg") or {}
                    val = _i(m.get("value")) / 1e9
                    s = m.get("source") or "external"
                    d = m.get("destination") or "external"
                    direction = "IN" if d == addr else "OUT"
                    if direction == "IN":
                        in_c += 1
                    else:
                        out_c += 1
                    print(f"  {ts} | {direction:3} | {val:.4f} {name} | {s[:10]}... -> {d[:10]}...")
                    if s not in ("external", addr):
                        peers.add(s)
                    if d not in ("external", addr):
                        peers.add(d)
                    for om in (tx.get("out_msgs") or []):
                        os_ = om.get("source")
                        od = om.get("destination")
                        if os_ and os_ != addr:
                            peers.add(os_)
                        if od and od != addr:
                            peers.add(od)
                print(f"\n--- Flow Summary ---")
                print(f"Incoming      : {in_c}")
                print(f"Outgoing      : {out_c}")
                _peers(name.lower(), peers)
        except Exception:
            pass

def analyze_address(addr, chain):
    if chain == "evm":
        _eth(addr)
        print()
        _bnb(addr)
    elif chain == "btc":
        _btc(addr)
    elif chain == "trc20":
        _trc20(addr)
    elif chain == "ton":
        _ton(addr, "TON")
    elif chain == "gram":
        _ton(addr, "GRAM")
    elif chain == "sol":
        _sol(addr)
    elif chain == "ltc":
        _ltc(addr)
    elif chain == "doge":
        _doge(addr)