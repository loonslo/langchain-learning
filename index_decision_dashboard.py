#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""五指数决策看板：只抓数据、计算信号，不执行交易。"""

import argparse
import datetime as dt
import html
import json
import re
import sys
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


CSI_BASE = "https://www.csindex.com.cn/csindex-home"
CSI_INDICES = {
    "000300": {"name": "沪深300", "kind": "cn_broad", "product": "-"},
    "000905": {"name": "中证500", "kind": "cn_broad", "product": "-"},
    "H30269": {"name": "中证红利低波动", "kind": "dividend", "product": "512890/563020"},
}
US_INDICES = {
    "^GSPC": {"name": "标普500", "kind": "us_broad", "cnbc": ".SPX", "wsj": "S&P 500 Index", "product": "标普QDII/VOO"},
    "^NDX": {"name": "纳斯达克100", "kind": "nasdaq", "cnbc": ".NDX", "wsj": "NASDAQ 100 Index", "product": "纳指QDII/QQQ"},
}
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) IndexDecisionDashboard/1.0"
TIMEOUT = 12


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json,*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return json.loads(response.read().decode("utf-8"))


def get_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8", errors="replace")


def to_float(value):
    try:
        return float(str(value).replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def pct(value, digits=1):
    return "N/A" if value is None else f"{value:.{digits}f}%"


def num(value, digits=2):
    return "N/A" if value is None else f"{value:.{digits}f}"


def drawdown(current, high):
    if current is None or high in (None, 0):
        return None
    return (current / high - 1.0) * 100.0


def drawdown_band(dd):
    if dd is None:
        return None
    for level in (-25, -20, -15, -10, -5):
        if dd <= level:
            return level
    return 0


def percentile_label(value):
    if value is None:
        return "未知"
    if value <= 0.2:
        return "低位"
    if value <= 0.5:
        return "中低"
    if value <= 0.8:
        return "中高"
    return "高位"


def fetch_csi_history(code, start_date, end_date):
    query = urllib.parse.urlencode({
        "indexCode": code,
        "startDate": start_date.strftime("%Y%m%d"),
        "endDate": end_date.strftime("%Y%m%d"),
    })
    payload = get_json(f"{CSI_BASE}/perf/index-perf?{query}")
    rows = payload.get("data") or []
    rows = [row for row in rows if to_float(row.get("close")) is not None]
    rows.sort(key=lambda row: str(row.get("tradeDate", "")))
    if not rows:
        raise RuntimeError(f"中证日线为空: {code}")
    latest = rows[-1]
    high_52w = max(to_float(row.get("high")) or to_float(row.get("close")) for row in rows[-260:])
    return {
        "current": to_float(latest.get("close")),
        "high_52w": high_52w,
        "drawdown_52w": drawdown(to_float(latest.get("close")), high_52w),
        "pe_ttm": to_float(latest.get("peg")),
        "date": str(latest.get("tradeDate", "N/A")),
        "source_price": "CSI:index-perf",
    }


def fetch_csi_performance(code):
    payload = get_json(f"{CSI_BASE}/perf/get-index-yield-item/{code}")
    data = payload.get("data") or {}
    return {
        "return_1m": to_float(data.get("oneMonth")),
        "return_3m": to_float(data.get("threeMonth")),
        "return_ytd": to_float(data.get("thisYear")),
        "return_1y": to_float(data.get("oneYear")),
        "performance_date": data.get("endDate"),
        "source_performance": "CSI:get-index-yield-item",
    }


def fetch_csi_dashboard_valuations():
    payload = get_json(f"{CSI_BASE}/data-service/indexValuation")
    data = payload.get("data") or {}
    rows = data.get("indexValuations") or []
    result = {}
    for row in rows:
        result[row.get("indexName")] = {
            "pe_static": to_float(row.get("pe")),
            "pe_ttm": to_float(row.get("peg")),
            "pb": to_float(row.get("pb")),
            "dividend_yield": to_float(row.get("dp")),
            "valuation_date": str(row.get("tradeDate") or data.get("tradeDate") or "N/A"),
            "source_valuation": "CSI:indexValuation",
        }
    return result


def fetch_danjuan_valuations():
    payload = get_json("https://danjuanfunds.com/djapi/index_eva/dj")
    wanted = {"SH000300": "000300", "SH000905": "000905", "CSIH30269": "H30269"}
    result = {}
    for row in (payload.get("data") or {}).get("items", []):
        code = wanted.get(row.get("index_code"))
        if not code:
            continue
        result[code] = {
            "pe_ttm": to_float(row.get("pe")),
            "pb": to_float(row.get("pb")),
            "dividend_yield": None if to_float(row.get("yeild")) is None else to_float(row.get("yeild")) * 100,
            "roe": None if to_float(row.get("roe")) is None else to_float(row.get("roe")) * 100,
            "pe_percentile": to_float(row.get("pe_percentile")),
            "pb_percentile": to_float(row.get("pb_percentile")),
            "valuation_date": str(row.get("date") or "N/A"),
            "source_valuation_extra": "Danjuan:index_eva",
        }
    return result


def fetch_yahoo_history(ticker):
    encoded = urllib.parse.quote(ticker)
    last_error = None
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            payload = get_json(f"https://{host}/v8/finance/chart/{encoded}?range=400d&interval=1d")
            result = payload["chart"]["result"][0]
            timestamps = result.get("timestamp") or []
            quote = result["indicators"]["quote"][0]
            rows = []
            for stamp, close, high in zip(timestamps, quote.get("close") or [], quote.get("high") or []):
                if close is not None:
                    rows.append((stamp, float(close), float(high) if high is not None else float(close)))
            if not rows:
                raise RuntimeError("Yahoo日线为空")
            current = rows[-1][1]
            high_52w = max(row[2] for row in rows[-260:])
            return {
                "current": current,
                "high_52w": high_52w,
                "drawdown_52w": drawdown(current, high_52w),
                "date": dt.datetime.fromtimestamp(rows[-1][0], dt.UTC).date().isoformat(),
                "source_price": f"Yahoo:{host}",
            }
        except Exception as exc:
            last_error = exc
    raise RuntimeError(f"Yahoo失败: {last_error}")


def fetch_cnbc_quote(symbol):
    encoded = urllib.parse.quote(symbol, safe="")
    url = (
        "https://quote.cnbc.com/quote-html-webservice/quote.htm"
        f"?symbols={encoded}&requestMethod=quick&noform=1&partnerId=2&fund=1&exthrs=1&output=json"
    )
    payload = get_json(url)
    row = payload["QuickQuoteResult"]["QuickQuote"][0]
    fundamentals = row.get("FundamentalData") or {}
    current = to_float(row.get("last"))
    high_52w = to_float(fundamentals.get("yrhiprice"))
    return {
        "current": current,
        "high_52w": high_52w,
        "drawdown_52w": drawdown(current, high_52w),
        "date": row.get("last_time") or "N/A",
        "source_price": "CNBC",
    }


def parse_wsj_valuations(page):
    page = html.unescape(page)
    result = {}
    for ticker, cfg in US_INDICES.items():
        marker = f'"name":"{cfg["wsj"]}"'
        start = page.find(marker)
        if start < 0:
            continue
        segment = page[start:start + 1200]
        def field(name):
            match = re.search(rf'"{re.escape(name)}"\s*:\s*"([0-9.]+)"', segment)
            return to_float(match.group(1)) if match else None
        date_match = re.search(r'"formattedTradeDate"\s*:\s*"([0-9/]+)"', segment)
        result[ticker] = {
            "pe_ttm": field("priceEarningsRatio"),
            "pe_forward": field("priceEarningsRatioEstimate"),
            "pe_52w_ago": field("priceEarningsRatio52WeekAgo"),
            "dividend_yield": field("yield"),
            "valuation_date": date_match.group(1) if date_match else dt.date.today().isoformat(),
            "source_valuation": "WSJ:P/E & Yields",
        }
    return result


def fetch_wsj_valuations():
    return parse_wsj_valuations(get_text("https://www.wsj.com/market-data/stocks/peyields"))


def merge_non_null(target, source, overwrite=True):
    for key, value in source.items():
        if value is not None and (overwrite or target.get(key) is None):
            target[key] = value


def dividend_signal(row):
    pe = row.get("pe_ttm")
    dy = row.get("dividend_yield")
    pe_pct = row.get("pe_percentile")
    if pe is None or dy is None:
        return "数据不足：至少需要PE和股息率"
    if dy < 4.5 or pe > 13:
        return "暂停新增：股息率<4.5%或PE>13"
    if dy > 6 or pe < 11:
        if dy < 6 and pe_pct is not None and pe_pct > 0.7:
            return "可买但不加速：PE低，股息率/历史分位未到极便宜"
        return "允许买入/加速：股息率>6%或PE<11"
    return "正常小额：股息率4.5%-6%、PE 11-13"


def broad_signal(row, kind):
    dd = row.get("drawdown_52w")
    band = drawdown_band(dd)
    pe_pct = row.get("pe_percentile")
    fwd = row.get("pe_forward")
    notes = []
    if kind == "nasdaq" and fwd is not None and fwd > 35:
        notes.append("前瞻PE>35，暂停纳指新增")
    if band in (None, 0):
        notes.append("未到-5%回撤档，维持基础节奏")
    elif band == -5:
        notes.append("进入-5%观察档，可检查定投×1.5")
    else:
        notes.append(f"进入{band}%回撤档，按宽基金字塔复核")
    if pe_pct is not None:
        if pe_pct > 0.8:
            notes.append("PE历史分位高，不因回撤自动加速")
        elif pe_pct <= 0.3:
            notes.append("PE历史分位较低，估值与回撤更匹配")
    pe_now = row.get("pe_ttm")
    pe_old = row.get("pe_52w_ago")
    if pe_now is not None and pe_old not in (None, 0) and pe_now / pe_old > 1.1:
        notes.append("PE较一年前扩张>10%")
    return "；".join(notes)


def collect_dashboard():
    today = dt.date.today()
    start = today - dt.timedelta(days=370)
    rows = {}
    gaps = []

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {}
        for code, cfg in CSI_INDICES.items():
            futures[pool.submit(fetch_csi_history, code, start, today)] = (code, "history")
            futures[pool.submit(fetch_csi_performance, code)] = (code, "performance")
        for ticker, cfg in US_INDICES.items():
            futures[pool.submit(fetch_yahoo_history, ticker)] = (ticker, "history")
        for future in as_completed(futures):
            code, part = futures[future]
            rows.setdefault(code, {})
            try:
                merge_non_null(rows[code], future.result())
            except Exception as exc:
                gaps.append(f"{code}/{part}: {exc}")

    for ticker, cfg in US_INDICES.items():
        if rows.get(ticker, {}).get("current") is None:
            try:
                merge_non_null(rows.setdefault(ticker, {}), fetch_cnbc_quote(cfg["cnbc"]))
            except Exception as exc:
                gaps.append(f"{ticker}/CNBC: {exc}")

    try:
        official = fetch_csi_dashboard_valuations()
        name_to_code = {cfg["name"]: code for code, cfg in CSI_INDICES.items()}
        for name, values in official.items():
            code = name_to_code.get(name)
            if code:
                merge_non_null(rows.setdefault(code, {}), values)
    except Exception as exc:
        gaps.append(f"CSI/valuation: {exc}")

    try:
        extras = fetch_danjuan_valuations()
        for code, values in extras.items():
            merge_non_null(rows.setdefault(code, {}), values, overwrite=False)
            for key in ("pe_percentile", "pb_percentile", "roe", "source_valuation_extra"):
                if values.get(key) is not None:
                    rows[code][key] = values[key]
            if code == "H30269":
                for key in ("pb", "dividend_yield", "valuation_date", "source_valuation_extra"):
                    if values.get(key) is not None:
                        rows[code][key] = values[key]
    except Exception as exc:
        gaps.append(f"Danjuan/valuation: {exc}")

    try:
        us_values = fetch_wsj_valuations()
        for ticker, values in us_values.items():
            merge_non_null(rows.setdefault(ticker, {}), values)
        for ticker in US_INDICES:
            if ticker not in us_values:
                gaps.append(f"{ticker}/WSJ valuation: 未找到指数PE字段")
    except Exception as exc:
        gaps.append(f"WSJ/valuation: {exc}")

    output = []
    for code, cfg in {**CSI_INDICES, **US_INDICES}.items():
        row = rows.setdefault(code, {})
        row.update({"code": code, "name": cfg["name"], "kind": cfg["kind"], "product": cfg.get("product", "-")})
        row["pe_percentile_label"] = percentile_label(row.get("pe_percentile"))
        row["signal"] = dividend_signal(row) if cfg["kind"] == "dividend" else broad_signal(row, cfg["kind"])
        output.append(row)
    return {"asof": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "indices": output, "data_gaps": gaps}


def print_dashboard(data):
    print(f"【五指数决策看板 {data['asof']}】")
    print("名称/代码/产品                 当前       52周高点    距高点    PE(TTM)  PE(FWD)  PB    股息率   PE分位")
    print("-" * 116)
    for row in data["indices"]:
        identity = f"{row['name']}({row['code']}/{row['product']})"
        print(
            f"{identity:<28} "
            f"{num(row.get('current'), 2):>10} "
            f"{num(row.get('high_52w'), 2):>10} "
            f"{pct(row.get('drawdown_52w'), 1):>8} "
            f"{num(row.get('pe_ttm'), 2):>8} "
            f"{num(row.get('pe_forward'), 2):>8} "
            f"{num(row.get('pb'), 2):>5} "
            f"{pct(row.get('dividend_yield'), 2):>8} "
            f"{row.get('pe_percentile_label', '未知'):>6}"
        )
        perf = []
        for key, label in (("return_1m", "1月"), ("return_3m", "3月"), ("return_ytd", "年内"), ("return_1y", "1年")):
            if row.get(key) is not None:
                perf.append(f"{label}{pct(row[key])}")
        if perf:
            print("  表现：" + " / ".join(perf))
        print("  判断：" + row["signal"])
        sources = [row.get("source_price"), row.get("source_performance"), row.get("source_valuation"), row.get("source_valuation_extra")]
        print("  日期/源：" + str(row.get("date", "N/A")) + " | " + " + ".join(x for x in sources if x))
    if data["data_gaps"]:
        print("\n数据缺口：")
        for gap in data["data_gaps"]:
            print("- " + gap)
    print("\n说明：PE分位来自公开估值源，仅作交叉验证；N/A表示未取到，不用旧值填充。脚本不执行交易。")


def selftest():
    wsj_sample = (
        '{"name":"NASDAQ 100 Index","priceEarningsRatio":"34.65",'
        '"priceEarningsRatioEstimate":"26.59","priceEarningsRatio52WeekAgo":"31.1",'
        '"yield":"0.58","formattedTradeDate":"6/12/26"}'
        '{"name":"S&P 500 Index","priceEarningsRatio":"25.1",'
        '"priceEarningsRatioEstimate":"21.54","priceEarningsRatio52WeekAgo":"23.72",'
        '"yield":"1.09","formattedTradeDate":"6/12/26"}'
    )
    wsj_test = parse_wsj_valuations(wsj_sample)
    checks = [
        ("回撤120到90=-25%", abs(drawdown(90, 120) + 25) < 1e-9),
        ("-16%进入-15档", drawdown_band(-16) == -15),
        ("PE分位10%=低位", percentile_label(0.1) == "低位"),
        ("红利PE8/股息5/分位72%=不加速", "不加速" in dividend_signal({"pe_ttm": 8, "dividend_yield": 5, "pe_percentile": 0.72})),
        ("红利股息4%=暂停", "暂停" in dividend_signal({"pe_ttm": 8, "dividend_yield": 4, "pe_percentile": 0.2})),
        ("纳指前瞻PE36=暂停", "暂停" in broad_signal({"drawdown_52w": -2, "pe_forward": 36}, "nasdaq")),
        ("WSJ纳指PE解析", wsj_test.get("^NDX", {}).get("pe_forward") == 26.59),
        ("WSJ标普PE解析", wsj_test.get("^GSPC", {}).get("pe_ttm") == 25.1),
    ]
    ok = True
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        ok = ok and passed
    return ok


def main():
    parser = argparse.ArgumentParser(description="获取五个核心指数的估值、52周回撤与决策提示")
    parser.add_argument("--json", action="store_true", help="输出JSON")
    parser.add_argument("--selftest", action="store_true", help="运行离线自测")
    args = parser.parse_args()
    if args.selftest:
        return 0 if selftest() else 1
    data = collect_dashboard()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_dashboard(data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
