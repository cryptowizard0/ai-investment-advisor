#!/usr/bin/env python3
"""
Fetch market data with routing + fallback.

Primary goals:
- Bars at 5m/1h/1d (US/HK/CN/FUT)
- L1 order book (US/HK/CN, if supported)
- Options + darkpool/OTC for US via Polygon
- Yahoo as partial fallback only

Output format: JSON with stable schema for downstream skills.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


DEFAULT_TIMEOUT = 20
BASE_INTERVAL_MINUTES = 5
SUPPORTED_INTERVALS = {"5m": 5, "1h": 60, "1d": 1440}
DEFAULT_INTERVAL = "5m"
HTTP_RETRY_DELAYS_SECONDS = (1, 2)
ERROR_LOG: List[str] = []


def _log_error(scope: str, err: Exception) -> None:
    ERROR_LOG.append(f"{scope}: {err.__class__.__name__}: {err}")


def _normalize_alltick_symbol(symbol: str, market: str) -> str:
    if "." in symbol:
        return symbol
    if market == "US":
        return f"{symbol}.US"
    if market == "HK":
        return f"{symbol}.HK"
    return symbol


def _load_dotenv() -> None:
    def parse_line(line: str) -> Optional[Tuple[str, str]]:
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        if "=" not in line:
            return None
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")  # strip quotes
        return key, value

    def find_env() -> Optional[Path]:
        # Search from cwd upwards
        cwd = Path.cwd()
        for p in [cwd, *cwd.parents]:
            candidate = p / ".env"
            if candidate.exists():
                return candidate
        # Search from script location upwards
        here = Path(__file__).resolve().parent
        for p in [here, *here.parents]:
            candidate = p / ".env"
            if candidate.exists():
                return candidate
        return None

    env_path = find_env()
    if not env_path:
        return
    try:
        with env_path.open("r", encoding="utf-8") as f:
            for line in f:
                parsed = parse_line(line)
                if not parsed:
                    continue
                key, value = parsed
                # Do not override existing env vars
                os.environ.setdefault(key, value)
    except Exception:
        return


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        # Fallback: YYYY-MM-DD
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"Invalid datetime: {value}")


def _http_get_json(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    req = Request(url, headers=headers or {})
    attempts = 1 + len(HTTP_RETRY_DELAYS_SECONDS)
    last_exc: Optional[Exception] = None

    for attempt in range(attempts):
        try:
            with urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
                data = resp.read()
            return json.loads(data.decode("utf-8"))
        except HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8")
            except Exception:
                body = ""
            last_exc = HTTPError(e.url, e.code, f"{e.reason} {body}".strip(), e.headers, e.fp)
        except URLError as e:
            last_exc = e

        if attempt < len(HTTP_RETRY_DELAYS_SECONDS):
            time.sleep(HTTP_RETRY_DELAYS_SECONDS[attempt])

    if last_exc:
        raise last_exc
    raise RuntimeError("HTTP request failed without explicit exception")


def _iso(ts: int | float) -> str:
    # ts in seconds
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _iso_from_ns(ns: int) -> str:
    return _iso(ns / 1_000_000_000)


def _iso_from_ms(ms: int) -> str:
    return _iso(ms / 1000)


def _cache_key(params: Dict[str, Any]) -> str:
    digest = hashlib.sha1(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()
    return digest


def _load_cache(cache_dir: Optional[str], key: str, ttl: int) -> Optional[Dict[str, Any]]:
    if not cache_dir:
        return None
    path = os.path.join(cache_dir, f"{key}.json")
    if not os.path.exists(path):
        return None
    if ttl > 0:
        mtime = os.path.getmtime(path)
        if time.time() - mtime > ttl:
            return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(cache_dir: Optional[str], key: str, payload: Dict[str, Any]) -> None:
    if not cache_dir:
        return
    os.makedirs(cache_dir, exist_ok=True)
    path = os.path.join(cache_dir, f"{key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _detect_gaps(bars: List[Dict[str, Any]], interval_minutes: int) -> bool:
    if len(bars) < 2:
        return False
    interval_seconds = interval_minutes * 60
    last_ts = None
    for b in bars:
        ts = datetime.fromisoformat(b["timestamp"].replace("Z", "+00:00")).timestamp()
        if last_ts is not None:
            if ts - last_ts > interval_seconds * 2:
                return True
        last_ts = ts
    return False


def _merge_bars(primary: List[Dict[str, Any]], fallback: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {b["timestamp"]: b for b in primary}
    for b in fallback:
        if b["timestamp"] not in index:
            index[b["timestamp"]] = b
    return sorted(index.values(), key=lambda x: x["timestamp"])


def _normalize_interval(interval: str) -> str:
    interval = interval.strip().lower()
    if interval == "auto":
        return "auto"
    if interval in {"60m", "1h"}:
        return "1h"
    if interval in {"1d", "day", "1day"}:
        return "1d"
    if interval in {"5m", "5min", "5minute"}:
        return "5m"
    return interval


def _auto_interval(start: Optional[datetime], end: Optional[datetime]) -> Tuple[str, float]:
    if not end:
        end = _now_utc()
    if not start:
        start = end - timedelta(days=7)
    span_days = max(1, (end - start).total_seconds() / 86400)
    if span_days <= 10:
        return "5m", span_days
    if span_days <= 60:
        return "1h", span_days
    return "1d", span_days


def _aggregate_bars(bars: List[Dict[str, Any]], interval_minutes: int) -> List[Dict[str, Any]]:
    if not bars:
        return []
    if interval_minutes <= BASE_INTERVAL_MINUTES:
        return bars

    grouped: Dict[int, Dict[str, Any]] = {}
    interval_seconds = interval_minutes * 60
    for b in bars:
        ts = datetime.fromisoformat(b["timestamp"].replace("Z", "+00:00")).timestamp()
        bucket = int(ts // interval_seconds) * interval_seconds
        key = int(bucket)
        if key not in grouped:
            grouped[key] = {
                "timestamp": _iso(key),
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "volume": b.get("volume", 0),
                "symbol": b["symbol"],
                "market": b["market"],
                "source": b.get("source", "unknown"),
                "quality_flags": list(b.get("quality_flags", [])) + ["aggregated_from_5m"],
            }
        else:
            g = grouped[key]
            g["high"] = max(g["high"], b["high"])
            g["low"] = min(g["low"], b["low"])
            g["close"] = b["close"]
            g["volume"] += b.get("volume", 0)
    return sorted(grouped.values(), key=lambda x: x["timestamp"])


# --------------------------- AllTick --------------------------- #


def fetch_alltick_bars(
    symbol: str,
    market: str,
    interval: str,
    start: Optional[datetime],
    end: Optional[datetime],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    interval = _normalize_interval(interval)
    symbol = _normalize_alltick_symbol(symbol, market)
    api_key = os.environ.get("ALLTICK_API_KEY")
    if not api_key:
        return [], ["alltick_unconfigured"]

    base_url = os.environ.get("ALLTICK_BASE_URL", "https://quote.alltick.io").strip()
    if not base_url.startswith("http"):
        return [], ["alltick_invalid_base_url"]
    if market in {"US", "HK", "CN"}:
        path = "/quote-stock-b-api/kline"
    else:
        path = "/quote-b-api/kline"

    kline_type = 2  # 5m per AllTick docs
    kline_timestamp_end = 0
    if market not in {"US", "HK", "CN"} and end:
        kline_timestamp_end = int(end.timestamp())
    query_kline_num = 300
    if start and end:
        delta = int((end - start).total_seconds() / 60)
        query_kline_num = max(1, min(500, delta // BASE_INTERVAL_MINUTES + 1))

    query = {
        "trace": f"mdr-{int(time.time())}",
        "data": {
            "code": symbol,
            "kline_type": kline_type,
            "kline_timestamp_end": kline_timestamp_end,
            "query_kline_num": query_kline_num,
            "adjust_type": 0,
        },
    }
    url = f"{base_url}{path}?{urlencode({'token': api_key, 'query': json.dumps(query)})}"
    try:
        payload = _http_get_json(url)
    except Exception as e:
        _log_error("alltick_bars", e)
        return [], ["alltick_request_failed"]

    data = payload.get("data") or {}
    kline_list = data.get("kline_list") or data.get("kline") or []
    bars: List[Dict[str, Any]] = []
    for item in kline_list:
        # Try multiple timestamp keys
        ts_val = item.get("timestamp") or item.get("ts") or item.get("time")
        if ts_val is None:
            continue
        ts_val = int(float(ts_val))
        if ts_val > 10_000_000_000:
            ts_iso = _iso_from_ms(ts_val)
        else:
            ts_iso = _iso(ts_val)
        open_val = item.get("open") or item.get("open_price")
        close_val = item.get("close") or item.get("close_price")
        high_val = item.get("high") or item.get("high_price")
        low_val = item.get("low") or item.get("low_price")
        vol_val = item.get("volume")
        bars.append(
            {
                "timestamp": ts_iso,
                "open": float(open_val or 0),
                "high": float(high_val or 0),
                "low": float(low_val or 0),
                "close": float(close_val or 0),
                "volume": int(float(vol_val or 0)),
                "symbol": symbol,
                "market": market,
                "source": "alltick",
                "quality_flags": [],
            }
        )
    flags = []
    if not bars:
        flags.append("missing_bars")
    else:
        if _detect_gaps(bars, BASE_INTERVAL_MINUTES):
            flags.append("missing_bars")
        if start and end:
            first_ts = datetime.fromisoformat(bars[0]["timestamp"].replace("Z", "+00:00"))
            last_ts = datetime.fromisoformat(bars[-1]["timestamp"].replace("Z", "+00:00"))
            if first_ts > start + timedelta(minutes=BASE_INTERVAL_MINUTES * 2):
                flags.append("missing_bars")
            if last_ts < end - timedelta(minutes=BASE_INTERVAL_MINUTES * 2):
                flags.append("missing_bars")
    bars = sorted(bars, key=lambda x: x["timestamp"])
    if interval != "5m":
        target_minutes = SUPPORTED_INTERVALS.get(interval)
        if not target_minutes:
            flags.append("interval_unsupported")
            return [], flags
        bars = _aggregate_bars(bars, target_minutes)
    return bars, flags


def fetch_alltick_l1(symbol: str, market: str) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    symbol = _normalize_alltick_symbol(symbol, market)
    api_key = os.environ.get("ALLTICK_API_KEY")
    if not api_key:
        return None, ["alltick_unconfigured", "missing_l1"]

    base_url = os.environ.get("ALLTICK_BASE_URL", "https://quote.alltick.io").strip()
    if not base_url.startswith("http"):
        return None, ["alltick_invalid_base_url", "missing_l1"]
    path = "/quote-stock-b-api/depth-tick"

    query = {
        "trace": f"mdr-{int(time.time())}",
        "data": {"symbol_list": [{"code": symbol}]},
    }
    url = f"{base_url}{path}?{urlencode({'token': api_key, 'query': json.dumps(query)})}"
    try:
        payload = _http_get_json(url)
    except Exception as e:
        _log_error("alltick_l1", e)
        return None, ["alltick_request_failed", "missing_l1"]

    data = payload.get("data") or {}
    tick_list = data.get("tick_list") or data.get("tick") or []
    if not tick_list:
        return None, ["missing_l1"]

    tick = tick_list[0]
    bids = tick.get("bid") or tick.get("bids") or []
    asks = tick.get("ask") or tick.get("asks") or []

    def _first(levels):
        if not levels:
            return (None, None)
        if isinstance(levels[0], dict):
            return (levels[0].get("price"), levels[0].get("volume") or levels[0].get("size"))
        return (levels[0][0], levels[0][1]) if len(levels[0]) >= 2 else (None, None)

    bid, bid_size = _first(bids)
    ask, ask_size = _first(asks)

    ts = tick.get("timestamp") or tick.get("ts") or int(time.time())
    ts_iso = _iso_from_ms(int(ts)) if int(ts) > 10_000_000_000 else _iso(int(ts))

    l1 = {
        "timestamp": ts_iso,
        "bid": float(bid) if bid is not None else None,
        "ask": float(ask) if ask is not None else None,
        "bid_size": int(float(bid_size)) if bid_size is not None else None,
        "ask_size": int(float(ask_size)) if ask_size is not None else None,
        "symbol": symbol,
        "market": market,
        "source": "alltick",
        "quality_flags": [],
    }
    return l1, []


# --------------------------- Yahoo --------------------------- #


def fetch_yahoo_bars(
    symbol: str,
    market: str,
    start: Optional[datetime],
    end: Optional[datetime],
    interval: str,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    if os.environ.get("YAHOO_ENABLED", "true").lower() not in {"1", "true", "yes"}:
        return [], ["yahoo_disabled"]

    interval = _normalize_interval(interval)
    yahoo_interval = "5m"
    if interval == "1h":
        yahoo_interval = "60m"
    elif interval == "1d":
        yahoo_interval = "1d"

    if not end:
        end = _now_utc()
    if not start:
        start = end - timedelta(days=7)

    params = {
        "period1": int(start.timestamp()),
        "period2": int(end.timestamp()),
        "interval": yahoo_interval,
        "includePrePost": "false",
        "events": "div,splits",
    }
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?{urlencode(params)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MarketDataRouter/1.0)",
        "Accept": "application/json",
    }
    try:
        payload = _http_get_json(url, headers=headers)
    except Exception as e:
        _log_error("yahoo_bars", e)
        return [], ["missing_bars"]

    chart = (payload.get("chart") or {}).get("result") or []
    if not chart:
        return [], ["missing_bars"]

    result = chart[0]
    ts_list = result.get("timestamp") or []
    quote = (result.get("indicators") or {}).get("quote") or []
    if not quote:
        return [], ["missing_bars"]
    quote = quote[0]

    bars: List[Dict[str, Any]] = []
    for i, ts in enumerate(ts_list):
        o = quote.get("open", [None])[i]
        h = quote.get("high", [None])[i]
        l = quote.get("low", [None])[i]
        c = quote.get("close", [None])[i]
        v = quote.get("volume", [None])[i]
        if o is None or h is None or l is None or c is None:
            continue
        bars.append(
            {
                "timestamp": _iso(ts),
                "open": float(o),
                "high": float(h),
                "low": float(l),
                "close": float(c),
                "volume": int(float(v or 0)),
                "symbol": symbol,
                "market": market,
                "source": "yahoo",
                "quality_flags": ["fallback_to_yahoo"],
            }
        )
    flags = []
    if not bars:
        flags.append("missing_bars")
    # Yahoo already returns the requested interval for 1h/1d
    if interval not in {"5m", "1h", "1d"}:
        flags.append("interval_unsupported")
        return [], flags
    return bars, flags


# --------------------------- Polygon --------------------------- #


def fetch_polygon_options(underlying: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        return [], ["polygon_unconfigured", "options_unavailable"]

    base = os.environ.get("POLYGON_BASE_URL", "https://api.polygon.io").strip()
    if not base.startswith("http"):
        return [], ["polygon_invalid_base_url", "options_unavailable"]
    url = f"{base}/v3/snapshot/options/{underlying}?{urlencode({'apiKey': api_key})}"
    try:
        payload = _http_get_json(url)
    except Exception as e:
        _log_error("polygon_options", e)
        return [], ["options_unavailable"]
    results = payload.get("results") or []

    options: List[Dict[str, Any]] = []
    for opt in results:
        details = opt.get("details", {})
        last_quote = opt.get("last_quote", {}) or {}
        last_trade = opt.get("last_trade", {}) or {}
        options.append(
            {
                "timestamp": _iso_from_ns(last_trade.get("sip_timestamp", int(time.time() * 1e9)))
                if last_trade.get("sip_timestamp")
                else _iso(int(time.time())),
                "symbol": underlying,
                "contract": details.get("ticker"),
                "strike": details.get("strike_price"),
                "expiry": details.get("expiration_date"),
                "type": details.get("contract_type"),
                "last": last_trade.get("price"),
                "bid": last_quote.get("bid"),
                "ask": last_quote.get("ask"),
                "volume": opt.get("day", {}).get("volume"),
                "open_interest": opt.get("open_interest"),
                "source": "polygon",
                "quality_flags": [],
            }
        )
    flags = []
    if not options:
        flags.append("options_unavailable")
    return options, flags


def fetch_polygon_darkpool(symbol: str, start: Optional[datetime], end: Optional[datetime]) -> Tuple[List[Dict[str, Any]], List[str]]:
    api_key = os.environ.get("POLYGON_API_KEY")
    if not api_key:
        return [], ["polygon_unconfigured", "darkpool_unavailable"]

    if not start or not end:
        return [], ["darkpool_unavailable"]

    base = os.environ.get("POLYGON_BASE_URL", "https://api.polygon.io").strip()
    if not base.startswith("http"):
        return [], ["polygon_invalid_base_url", "darkpool_unavailable"]
    params = {
        "timestamp": start.strftime("%Y-%m-%d"),
        "order": "desc",
        "limit": 1000,
        "sort": "timestamp",
        "apiKey": api_key,
    }
    url = f"{base}/v3/trades/{symbol}?{urlencode(params)}"
    try:
        payload = _http_get_json(url)
    except Exception as e:
        _log_error("polygon_darkpool", e)
        return [], ["darkpool_unavailable"]
    results = payload.get("results") or []

    darkpool: List[Dict[str, Any]] = []
    for tr in results:
        # Polygon darkpool/OTC: exchange=4 and TRF present
        if tr.get("exchange") == 4 and tr.get("trf_id") is not None:
            ts = tr.get("sip_timestamp") or tr.get("participant_timestamp")
            ts_iso = _iso_from_ns(ts) if ts else _iso(int(time.time()))
            darkpool.append(
                {
                    "timestamp": ts_iso,
                    "symbol": symbol,
                    "price": tr.get("price"),
                    "size": tr.get("size"),
                    "venue": tr.get("trf_id"),
                    "source": "polygon",
                    "quality_flags": [],
                }
            )
    flags = []
    if not darkpool:
        flags.append("darkpool_unavailable")
    return darkpool, flags


def main() -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Market data router with fallback")
    parser.add_argument("--market", required=True, choices=["US", "HK", "CN", "FUT"])
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--interval", default=DEFAULT_INTERVAL, help="5m/1h/1d/auto")
    parser.add_argument("--types", default="bars", help="bars,l1,options,darkpool")
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--out", default="-", help="Output file path or '-' for stdout")
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--cache-ttl", type=int, default=0, help="Cache TTL seconds")
    parser.add_argument("--explain", action="store_true", help="Explain auto interval selection")

    args = parser.parse_args()

    args.interval = _normalize_interval(args.interval)
    interval_mode = "manual"
    auto_info = None

    start = _parse_dt(args.start)
    end = _parse_dt(args.end)
    if args.interval == "auto":
        auto_interval, span_days = _auto_interval(start, end)
        args.interval = auto_interval
        interval_mode = "auto"
        auto_info = {"selected": auto_interval, "span_days": round(span_days, 2)}
        if args.explain:
            print(
                f"[auto] span_days={span_days:.2f} -> interval={auto_interval}",
                file=sys.stderr,
            )
    if args.interval not in SUPPORTED_INTERVALS:
        print(f"Unsupported interval: {args.interval}. Supported: {sorted(SUPPORTED_INTERVALS)}", file=sys.stderr)
        return 2
    if not end:
        end = _now_utc()

    types = [t.strip() for t in args.types.split(",") if t.strip()]

    cache_params = {
        "market": args.market,
        "symbol": args.symbol,
        "interval": args.interval,
        "types": types,
        "start": args.start,
        "end": args.end,
    }
    cache_key = _cache_key(cache_params)
    cached = _load_cache(args.cache_dir, cache_key, args.cache_ttl)
    if cached:
        if args.out == "-":
            print(json.dumps(cached, ensure_ascii=False, indent=2))
        else:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(cached, f, ensure_ascii=False, indent=2)
        return 0

    quality_flags: List[str] = []
    sources: List[str] = []

    bars: List[Dict[str, Any]] = []
    if "bars" in types:
        bars, flags = fetch_alltick_bars(args.symbol, args.market, args.interval, start, end)
        if bars:
            sources.append("alltick")
        quality_flags.extend(flags)

        if not bars or "missing_bars" in flags:
            ybars, yflags = fetch_yahoo_bars(args.symbol, args.market, start, end, args.interval)
            if ybars:
                if bars:
                    bars = _merge_bars(bars, ybars)
                    quality_flags.append("partial_data")
                else:
                    bars = ybars
                quality_flags.append("fallback_to_yahoo")
                sources.append("yahoo")
            quality_flags.extend(yflags)

    l1 = None
    if "l1" in types:
        if args.market in {"US", "HK", "CN"}:
            l1, flags = fetch_alltick_l1(args.symbol, args.market)
            if l1:
                sources.append("alltick")
            quality_flags.extend(flags)
        else:
            quality_flags.append("missing_l1")

    options: List[Dict[str, Any]] = []
    if "options" in types and args.market == "US":
        options, flags = fetch_polygon_options(args.symbol)
        if options:
            sources.append("polygon")
        quality_flags.extend(flags)

    darkpool: List[Dict[str, Any]] = []
    if "darkpool" in types and args.market == "US":
        darkpool, flags = fetch_polygon_darkpool(args.symbol, start, end)
        if darkpool:
            sources.append("polygon")
        quality_flags.extend(flags)

    payload = {
        "metadata": {
            "market": args.market,
            "symbol": args.symbol,
            "interval": args.interval,
            "start": start.isoformat().replace("+00:00", "Z") if start else None,
            "end": end.isoformat().replace("+00:00", "Z") if end else None,
            "requested_types": types,
            "generated_at": _now_utc().isoformat().replace("+00:00", "Z"),
            "interval_mode": interval_mode,
            "auto_interval": auto_info,
            "sources": sorted(set(sources)),
            "quality_flags": sorted(set(quality_flags)),
            "errors": ERROR_LOG,
        },
        "bars": bars,
        "l1": l1,
        "options": options,
        "darkpool": darkpool,
    }

    _save_cache(args.cache_dir, cache_key, payload)

    if args.out == "-":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
