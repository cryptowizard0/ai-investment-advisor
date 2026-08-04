#!/usr/bin/env python3
"""Elder NH-NL breadth state machine (Sell & Sell Short ch.10, "Groping for a Bottom").

Computes 250-session new-high/new-low breadth over a stock universe, rescales
Elder's US-wide absolute thresholds into universe-size-independent ratios,
evaluates the S1-S4 major-bottom checklist plus the P0-P6 state machine, and
adds index-level reads (Impulse System, value zone, autoenvelope, false
downside breakouts). Prints a Chinese markdown summary or JSON for the agent
to fold into the final monitor report; it does not write report files itself.

Data: yfinance by default; --prices-file/--index-file run fully offline.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

# Elder's absolute thresholds on the ~7,000-issue US universe, in ratio form.
# weekly_ratio = 5-day rolling sum of (daily NH-NL / eligible count), range [-5, +5].
RATIO_CAPITULATION = -0.571  # Elder -4000: capitulation spike (S1)
RATIO_FLOOR = -0.857         # Elder -6000: never breached before Oct 2008
RATIO_BULL_CONFIRM = 0.357   # Elder +2500: bear rallies do not reach this
DIVERGENCE_SHALLOWER = 0.40  # second trough >=40% shallower (2008-09 calibration)
DEEP_WEEK = -0.35            # ~Elder -2500: minimum depth for a divergence anchor

# 30 SOX members per Invesco SOXQ holdings 2026-07-17. Refresh on rebalances;
# applying current members to history carries mild survivorship bias.
SOX_UNIVERSE = [
    "NVDA", "AVGO", "MU", "AMAT", "KLAC", "LRCX", "AMD", "TXN", "MRVL", "ADI",
    "INTC", "QCOM", "NXPI", "MPWR", "COHR", "ALAB", "TER", "MCHP", "CRDO",
    "ON", "GFS", "ENTG", "MTSI", "RMBS", "SWKS", "QRVO",
    "TSM", "ASML", "ARM", "NVMI",
]
PRESETS = {"sox": {"tickers": SOX_UNIVERSE, "index": "^SOX", "label": "SOX"}}

STATE_LABELS = {
    "P0": "熊市初段（新高枯竭且新低潮已启动）",
    "P1": "投降进行中（S1 触发，平空/列清单，不接飞刀）",
    "P2": "生还确认（尖峰后回正，等背离）",
    "P3": "大底背离成立（战略转多，允许试仓）",
    "P4": "战术确认（日线双螺旋二次金叉，买入窗口）",
    "P5": "牛市确认（宽度站上确认线）",
    "P6": "牛市回调/休整（确认线回落但结构未坏）",
    "PX": "P6/P0 判定期（新高枯竭但零新低，等两侧触发器裁决）",
    "NEUTRAL": "中性（无近期极端事件）",
}


def abs_thresholds(n_universe: int) -> dict:
    """Ratio thresholds converted back to absolute weekly member-counts for display."""
    return {
        "capitulation": RATIO_CAPITULATION * n_universe,
        "floor": RATIO_FLOOR * n_universe,
        "bull_confirm": RATIO_BULL_CONFIRM * n_universe,
    }


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def macd_hist(close: pd.Series) -> pd.Series:
    macd = ema(close, 12) - ema(close, 26)
    return macd - ema(macd, 9)


def impulse(close: pd.Series) -> pd.Series:
    """Elder Impulse System per bar: green (buy ok) / red (buy ban) / blue (no ban)."""
    e13, hist = ema(close, 13), macd_hist(close)
    up = (e13.diff() > 0) & (hist.diff() > 0)
    down = (e13.diff() < 0) & (hist.diff() < 0)
    return pd.Series("blue", index=close.index).mask(up, "green").mask(down, "red")


def compute_breadth(px: pd.DataFrame, lookback: int = 252) -> pd.DataFrame:
    """Daily NH/NL counts, NH-NL, weekly 5-day sum, and normalized weekly ratio."""
    prev_max = px.rolling(lookback).max().shift(1)
    prev_min = px.rolling(lookback).min().shift(1)
    eligible = prev_max.notna() & px.notna()
    nh = ((px > prev_max) & eligible).sum(axis=1)
    nl = ((px < prev_min) & eligible).sum(axis=1)
    n_elig = eligible.sum(axis=1)
    daily = nh - nl
    denom = n_elig.astype(float).replace(0.0, float("nan"))
    return pd.DataFrame({
        "nh": nh,
        "nl": nl,
        "daily_nhnl": daily,
        "weekly_nhnl": daily.rolling(5).sum(),
        "weekly_ratio": (daily / denom).rolling(5).sum(),
        "n_eligible": n_elig,
    })


def below_level_episodes(series: pd.Series, level: float = 0.0) -> list[dict]:
    """Contiguous stretches with value < level; trough value/date per stretch."""
    out: list[dict] = []
    cur: dict | None = None
    for dt, value in series.dropna().items():
        if value < level:
            if cur is None:
                cur = {"start": dt, "trough": value, "trough_date": dt, "end": None}
            elif value < cur["trough"]:
                cur["trough"], cur["trough_date"] = value, dt
        elif cur is not None:
            cur["end"] = dt
            out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return out


def divergence_check(weekly_ratio: pd.Series, weekly_price: pd.Series,
                     shallower: float = DIVERGENCE_SHALLOWER,
                     min_first_trough: float = DEEP_WEEK) -> dict | None:
    """Most recent valid bullish divergence: price lower low, NH-NL trough much
    shallower, and a zero recross between the two troughs (episode separation)."""
    episodes = below_level_episodes(weekly_ratio, 0.0)
    for episode in episodes:
        end = episode["end"] or weekly_price.index[-1]
        segment = weekly_price.loc[episode["start"]:end]
        episode["price_low"] = float(segment.min()) if len(segment) else float("nan")
    found = None
    for first, second in zip(episodes, episodes[1:]):
        deep_enough = first["trough"] <= min_first_trough
        price_lower = second["price_low"] < first["price_low"]
        much_shallower = abs(second["trough"]) <= (1 - shallower) * abs(first["trough"])
        if deep_enough and price_lower and much_shallower:
            found = {"first": first, "second": second}
    return found


def double_helix_crossings(daily_nhnl: pd.Series, daily_nl: pd.Series,
                           lookback: int = 120) -> list[pd.Timestamp]:
    """Dates where daily NH-NL crosses above the daily New Lows line (ch.10:
    act on the SECOND crossing, the "double helix")."""
    spread = (daily_nhnl - daily_nl).dropna().tail(lookback)
    above = spread > 0
    crossed = above & ~above.shift(fill_value=False)
    return list(spread.index[crossed])


def false_breakouts(close: pd.Series, ref_window: int = 90, gap: int = 5,
                    confirm: int = 5, span: int = 180) -> list[dict]:
    """Closes below the prior significant low that are reclaimed within a few
    sessions -- Elder's favorite bottom pattern at the index level."""
    events = []
    start = max(ref_window + gap, len(close) - span)
    for i in range(start, len(close)):
        ref = close.iloc[i - ref_window:i - gap].min()
        if close.iloc[i] < ref:
            recovery = close.iloc[i + 1:i + 1 + confirm]
            reclaimed = recovery[recovery > ref]
            if len(reclaimed):
                events.append({
                    "break_date": close.index[i], "close": float(close.iloc[i]),
                    "ref_low": float(ref), "depth": float(close.iloc[i] / ref - 1),
                    "reclaim_date": reclaimed.index[0],
                })
    return events


def classify(breadth: pd.DataFrame, index_close: pd.Series | None) -> dict:
    """Deterministic P0-P6/PX read. S3/S4 structure still needs a human check."""
    weekly = breadth["weekly_ratio"].resample("W-FRI").last().dropna()
    weekly_nh = breadth["nh"].resample("W-FRI").sum().reindex(weekly.index)
    weekly_nl = breadth["nl"].resample("W-FRI").sum().reindex(weekly.index)
    reasons: list[str] = []

    if len(weekly) < 8:
        return {"state": "NEUTRAL", "label": STATE_LABELS["NEUTRAL"],
                "reasons": ["周线样本不足 8 周，无法判定"]}

    latest = float(weekly.iloc[-1])
    caps = weekly[weekly <= RATIO_CAPITULATION]

    if latest <= RATIO_CAPITULATION:
        reasons.append(f"本周比率 {latest:.3f} ≤ 投降线 {RATIO_CAPITULATION}")
        return {"state": "P1", "label": STATE_LABELS["P1"], "reasons": reasons}

    confirm_recent = weekly.iloc[-4:][weekly.iloc[-4:] >= RATIO_BULL_CONFIRM]
    if len(confirm_recent):
        reasons.append(f"近 4 周内比率 ≥ 确认线 {RATIO_BULL_CONFIRM}"
                       f"（{confirm_recent.index[-1].date()}）")
        return {"state": "P5", "label": STATE_LABELS["P5"], "reasons": reasons}

    if len(caps) and caps.index[-1] >= weekly.index[max(0, len(weekly) - 26)]:
        cap_date = caps.index[-1]
        after = weekly.loc[cap_date:]
        if after.max() < 0:
            reasons.append(f"{cap_date.date()} 投降后尚未回正")
            return {"state": "P1", "label": STATE_LABELS["P1"], "reasons": reasons}
        reasons.append(f"{cap_date.date()} 投降，其后已回正（S2）")
        divergence = None
        if index_close is not None:
            weekly_price = index_close.resample("W-FRI").last().dropna()
            divergence = divergence_check(weekly, weekly_price)
        if divergence and divergence["second"]["trough_date"] >= cap_date:
            reasons.append("投降后出现有效底背离（S3）")
            crossings = double_helix_crossings(breadth["daily_nhnl"], breadth["nl"])
            second_cross = [d for d in crossings
                            if d >= divergence["second"]["trough_date"]]
            if len(second_cross) >= 2:
                reasons.append(f"日线双螺旋二次金叉 {second_cross[1].date()}")
                return {"state": "P4", "label": STATE_LABELS["P4"], "reasons": reasons}
            return {"state": "P3", "label": STATE_LABELS["P3"], "reasons": reasons}
        return {"state": "P2", "label": STATE_LABELS["P2"], "reasons": reasons}

    nh_dried = (weekly_nh.iloc[-3:] == 0).all()
    if nh_dried:
        reasons.append("连续 ≥3 周零新高（新高枯竭）")
        if (weekly_nl.iloc[-3:] > 0).any():
            reasons.append("近 3 周已出现新低（溃逃开始）")
            return {"state": "P0", "label": STATE_LABELS["P0"], "reasons": reasons}
        reasons.append("但新低仍为零（垫子厚，未到恐慌）")
        return {"state": "PX", "label": STATE_LABELS["PX"], "reasons": reasons}

    confirm_26w = weekly.iloc[-26:][weekly.iloc[-26:] >= RATIO_BULL_CONFIRM]
    if len(confirm_26w):
        reasons.append(f"近 26 周内有牛市确认（最近 {confirm_26w.index[-1].date()}），"
                       "当前宽度回落但未枯竭")
        return {"state": "P6", "label": STATE_LABELS["P6"], "reasons": reasons}

    reasons.append("无近期投降、确认或枯竭事件")
    return {"state": "NEUTRAL", "label": STATE_LABELS["NEUTRAL"], "reasons": reasons}


def load_universe(args: argparse.Namespace) -> tuple[list[str], str | None, str]:
    if args.preset:
        preset = PRESETS[args.preset]
        return preset["tickers"], preset["index"], args.label or preset["label"]
    if not args.tickers_file:
        raise SystemExit("error: provide --preset or --tickers-file")
    lines = Path(args.tickers_file).read_text(encoding="utf-8").splitlines()
    tickers = [ln.split("#")[0].strip() for ln in lines]
    tickers = [t for t in tickers if t]
    if not tickers:
        raise SystemExit(f"error: no tickers found in {args.tickers_file}")
    return tickers, args.index_symbol, args.label or "CUSTOM"


def load_prices(args: argparse.Namespace, tickers: list[str],
                index_symbol: str | None) -> tuple[pd.DataFrame, pd.Series | None]:
    if args.prices_file:
        px = pd.read_csv(args.prices_file, index_col=0, parse_dates=True)
        index_close = None
        if args.index_file:
            idx = pd.read_csv(args.index_file, index_col=0, parse_dates=True)
            index_close = idx.iloc[:, 0].astype(float)
        return px.astype(float), index_close
    import yfinance as yf  # network path only

    px = yf.download(tickers, start=args.start, auto_adjust=True,
                     progress=False)["Close"]
    index_close = None
    if index_symbol:
        raw = yf.download(index_symbol, start=args.start, auto_adjust=True,
                          progress=False)["Close"]
        index_close = raw.iloc[:, 0] if isinstance(raw, pd.DataFrame) else raw
        index_close = index_close.dropna()
    return px, index_close


def render_markdown(result: dict) -> str:
    lines = [
        f"# NH-NL 宽度状态机：{result['label']}（截至 {result['asof']}）",
        "",
        f"- 样本：{result['n_universe']} 只（当日可判 {result['n_eligible']} 只），"
        f"口径：{result['lookback']} 日新高/新低，周线 = 日值 5 日求和",
        f"- 阈值（比率 | 折算家次）：投降 {RATIO_CAPITULATION} | "
        f"{result['thresholds']['capitulation']:.0f}；历史极限 {RATIO_FLOOR} | "
        f"{result['thresholds']['floor']:.0f}；牛市确认 +{RATIO_BULL_CONFIRM} | "
        f"+{result['thresholds']['bull_confirm']:.0f}",
        "",
        f"## 状态判定：{result['state']} — {result['state_label']}",
        "",
    ]
    lines += [f"- {reason}" for reason in result["reasons"]]
    lines += ["", "## 近 8 周宽度", "", "| 周 | 周NH | 周NL | 比率 | 指数收盘 |",
              "|---|---|---|---|---|"]
    for row in result["recent_weeks"]:
        lines.append(f"| {row['week']} | {row['nh']} | {row['nl']} | "
                     f"{row['ratio']:.3f} | {row['index_close']} |")
    lines += ["", "## 历史事件（窗口内）", ""]
    lines.append("- 投降周（S1）：" + (
        "、".join(f"{e['week']}（{e['ratio']:.3f}）" for e in result["capitulations"])
        if result["capitulations"] else "无"))
    lines.append("- 牛市确认区间：" + (
        "、".join(f"{e['start']}~{e['end']}（峰值 {e['peak']:.3f}）"
                  for e in result["bull_confirms"]) if result["bull_confirms"] else "无"))
    divergence = result.get("divergence")
    lines.append("- 有效底背离（S3）：" + (
        f"{divergence['first_trough_date']}（{divergence['first_trough']:.3f}）→ "
        f"{divergence['second_trough_date']}（{divergence['second_trough']:.3f}），"
        "期间已回正" if divergence else "无（结构需人工复核）"))
    lines.append("- 日线双螺旋金叉（近 120 交易日）：" + (
        "、".join(result["double_helix"]) if result["double_helix"] else "无"))
    if result.get("index"):
        idx = result["index"]
        lines += [
            "", "## 指数层读数", "",
            f"- 收盘 {idx['close']:.2f}，距 52 周高 {idx['off_high']:+.1%}，"
            f"距 52 周低 {idx['off_low']:+.1%}",
            f"- 周线 Impulse（近 6 根，末根或为进行中一周）：{idx['weekly_impulse']}",
            f"- 日线 Impulse（近 8 根）：{idx['daily_impulse']}",
            f"- 日线价值区 13/26EMA：{idx['ema13']:.0f}/{idx['ema26']:.0f}；"
            f"包络 ±{idx['envelope_pct']:.1%} → [{idx['env_low']:.0f}, {idx['env_high']:.0f}]",
            "- 假突破扫描（近 180 交易日）：" + (
                "、".join(f"{e['break_date']} 破 {e['ref_low']:.0f}"
                          f"（{e['depth']:+.1%}）→ {e['reclaim_date']} 收复"
                          for e in idx["false_breakouts"])
                if idx["false_breakouts"] else "无"),
        ]
    lines += ["", "## 人工复核项", "",
              "- S3 背离结构与 S4 末跌缩量需对照周线图人工确认；",
              "- 样本 <100 时单周噪音大，一家权重高，勿把单周读数当信号；",
              "- 现成分回溯有幸存者偏差；阈值为按样本数等比换算的操作化取值。"]
    return "\n".join(lines)


def run(argv: list[str] | None = None) -> str:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--preset", choices=sorted(PRESETS))
    parser.add_argument("--tickers-file", help="text file, one ticker per line, # comments")
    parser.add_argument("--index-symbol", help="benchmark symbol for index-level reads")
    parser.add_argument("--label", help="label used in headings/report names")
    parser.add_argument("--start", default="2021-01-01")
    parser.add_argument("--as-of", help="truncate data after this date (YYYY-MM-DD)")
    parser.add_argument("--lookback", type=int, default=252)
    parser.add_argument("--prices-file", help="offline wide CSV of closes (Date + tickers)")
    parser.add_argument("--index-file", help="offline CSV: date,close for the index")
    parser.add_argument("--cache-dir", help="write the daily breadth series CSV here")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args(argv)

    tickers, index_symbol, label = load_universe(args)
    px, index_close = load_prices(args, tickers, index_symbol)
    if args.as_of:
        px = px.loc[:args.as_of]
        if index_close is not None:
            index_close = index_close.loc[:args.as_of]

    breadth = compute_breadth(px, args.lookback)
    valid = breadth.dropna(subset=["weekly_ratio"])
    if valid.empty:
        raise SystemExit("error: not enough history for the lookback window")
    if args.cache_dir:
        cache = Path(args.cache_dir)
        cache.mkdir(parents=True, exist_ok=True)
        out = breadth.copy()
        if index_close is not None:
            out = out.join(index_close.rename("index_close"))
        out.to_csv(cache / f"nhnl_daily_{label}.csv")

    weekly = valid["weekly_ratio"].resample("W-FRI").last().dropna()
    weekly_nh = valid["nh"].resample("W-FRI").sum().reindex(weekly.index)
    weekly_nl = valid["nl"].resample("W-FRI").sum().reindex(weekly.index)
    weekly_px = (index_close.resample("W-FRI").last().reindex(weekly.index)
                 if index_close is not None else None)

    state = classify(valid, index_close)
    n_universe = px.shape[1]

    confirms = weekly >= RATIO_BULL_CONFIRM
    confirm_runs = []
    if confirms.any():
        groups = (confirms != confirms.shift()).cumsum()
        for _, chunk in weekly[confirms].groupby(groups[confirms]):
            confirm_runs.append({"start": str(chunk.index[0].date()),
                                 "end": str(chunk.index[-1].date()),
                                 "peak": float(chunk.max())})

    divergence = None
    if weekly_px is not None:
        raw_div = divergence_check(weekly, weekly_px.dropna())
        if raw_div:
            divergence = {
                "first_trough": float(raw_div["first"]["trough"]),
                "first_trough_date": str(raw_div["first"]["trough_date"].date()),
                "second_trough": float(raw_div["second"]["trough"]),
                "second_trough_date": str(raw_div["second"]["trough_date"].date()),
            }

    result = {
        "label": label,
        "asof": str(valid.index[-1].date()),
        "n_universe": n_universe,
        "n_eligible": int(valid["n_eligible"].iloc[-1]),
        "lookback": args.lookback,
        "thresholds": abs_thresholds(n_universe),
        "state": state["state"],
        "state_label": state["label"],
        "reasons": state["reasons"],
        "recent_weeks": [
            {"week": str(dt.date()), "nh": int(weekly_nh.loc[dt]),
             "nl": int(weekly_nl.loc[dt]), "ratio": float(weekly.loc[dt]),
             "index_close": (f"{weekly_px.loc[dt]:.2f}"
                             if weekly_px is not None and pd.notna(weekly_px.loc[dt])
                             else "-")}
            for dt in weekly.index[-8:]],
        "capitulations": [{"week": str(dt.date()), "ratio": float(v)}
                          for dt, v in weekly[weekly <= RATIO_CAPITULATION].items()],
        "bull_confirms": confirm_runs,
        "divergence": divergence,
        "double_helix": [str(d.date()) for d in
                         double_helix_crossings(valid["daily_nhnl"], valid["nl"])],
    }

    if index_close is not None and len(index_close):
        close = index_close.dropna()
        e13, e26 = ema(close, 13), ema(close, 26)
        deviation = (close / e26 - 1).abs().rolling(100).quantile(0.95)
        dev_last = float(deviation.iloc[-1]) if pd.notna(deviation.iloc[-1]) else 0.0
        hi52, lo52 = close.rolling(252).max(), close.rolling(252).min()
        weekly_close = close.resample("W-FRI").last().dropna()
        result["index"] = {
            "close": float(close.iloc[-1]),
            "off_high": float(close.iloc[-1] / hi52.iloc[-1] - 1),
            "off_low": float(close.iloc[-1] / lo52.iloc[-1] - 1),
            "weekly_impulse": list(impulse(weekly_close).iloc[-6:]),
            "daily_impulse": list(impulse(close).iloc[-8:]),
            "ema13": float(e13.iloc[-1]),
            "ema26": float(e26.iloc[-1]),
            "envelope_pct": dev_last,
            "env_low": float(e26.iloc[-1] * (1 - dev_last)),
            "env_high": float(e26.iloc[-1] * (1 + dev_last)),
            "false_breakouts": [{**e, "break_date": str(e["break_date"].date()),
                                 "reclaim_date": str(e["reclaim_date"].date())}
                                for e in false_breakouts(close)],
        }

    if args.format == "json":
        return json.dumps(result, ensure_ascii=False, indent=2, default=str)
    return render_markdown(result)


if __name__ == "__main__":
    print(run(sys.argv[1:]))
