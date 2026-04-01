#!/usr/bin/env python3
"""
競艇 期待値計算プログラム
Boat Racing Expected Value Calculator

使い方:
    python kyoutei_ev.py

賭式対応:
    - 単勝 (Win)
    - 複勝 (Place: Top 2)
    - 拡連複 (Quinella Place: Top 3 any 2)
    - 連複 (Quinella: Top 2 any order)
    - 連単 (Exacta: Top 2 exact order)
    - 3連複 (Trifecta Box: Top 3 any order)
    - 3連単 (Trifecta: Top 3 exact order)
"""

from itertools import permutations, combinations
from typing import Optional
import sys


# ─────────────────────────────────────────
# Harville モデルによる確率計算
# ─────────────────────────────────────────

def harville_p1(probs: dict[int, float], i: int) -> float:
    """艇iが1着になる確率"""
    return probs[i]


def harville_p12(probs: dict[int, float], i: int, j: int) -> float:
    """艇iが1着、艇jが2着になる確率 (Harville式)"""
    pi = probs[i]
    pj = probs[j]
    if pi >= 1.0:
        return 0.0
    return pi * (pj / (1.0 - pi))


def harville_p123(probs: dict[int, float], i: int, j: int, k: int) -> float:
    """艇iが1着、艇jが2着、艇kが3着になる確率 (Harville式)"""
    pi = probs[i]
    pj = probs[j]
    pk = probs[k]
    denom_2 = 1.0 - pi
    denom_3 = 1.0 - pi - pj
    if denom_2 <= 0 or denom_3 <= 0:
        return 0.0
    return pi * (pj / denom_2) * (pk / denom_3)


# ─────────────────────────────────────────
# 賭式ごとの確率計算
# ─────────────────────────────────────────

def prob_tansho(probs: dict[int, float], i: int) -> float:
    """単勝: 艇iが1着"""
    return harville_p1(probs, i)


def prob_fukusho(probs: dict[int, float], i: int) -> float:
    """複勝: 艇iが2着以内"""
    boats = list(probs.keys())
    total = 0.0
    for j in boats:
        if j != i:
            total += harville_p12(probs, j, i)
    return probs[i] + total


def prob_kakurenpuku(probs: dict[int, float], i: int, j: int) -> float:
    """拡連複: 艇i, jが3着以内(順不同)"""
    boats = list(probs.keys())
    total = 0.0
    for k in boats:
        if k == i or k == j:
            continue
        for perm in permutations([i, j, k]):
            total += harville_p123(probs, *perm)
    # i,j が1,2着のケースも加算
    total += harville_p12(probs, i, j) + harville_p12(probs, j, i)
    return total


def prob_renpuku(probs: dict[int, float], i: int, j: int) -> float:
    """連複: 艇i, jが1,2着(順不同)"""
    return harville_p12(probs, i, j) + harville_p12(probs, j, i)


def prob_rentan(probs: dict[int, float], i: int, j: int) -> float:
    """連単: 艇iが1着, 艇jが2着"""
    return harville_p12(probs, i, j)


def prob_sanrenpuku(probs: dict[int, float], i: int, j: int, k: int) -> float:
    """3連複: 艇i, j, kが1〜3着(順不同)"""
    total = 0.0
    for perm in permutations([i, j, k]):
        total += harville_p123(probs, *perm)
    return total


def prob_sanrentan(probs: dict[int, float], i: int, j: int, k: int) -> float:
    """3連単: 艇iが1着, 艇jが2着, 艇kが3着"""
    return harville_p123(probs, i, j, k)


# ─────────────────────────────────────────
# 期待値計算
# ─────────────────────────────────────────

def expected_value(prob: float, odds: float) -> float:
    """
    期待値 = 確率 × オッズ - 1
    オッズ: 1.0倍 = 元本のみ返ってくる (損益ゼロ)
    """
    return prob * odds - 1.0


# ─────────────────────────────────────────
# 入力ユーティリティ
# ─────────────────────────────────────────

def input_float(prompt: str, min_val: float = 0.0, max_val: float = float("inf"),
                default: Optional[float] = None) -> float:
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            val = float(raw)
            if min_val <= val <= max_val:
                return val
            print(f"  ※ {min_val}〜{max_val} の範囲で入力してください")
        except ValueError:
            print("  ※ 数値を入力してください")


def input_odds(bet_label: str) -> Optional[float]:
    raw = input(f"  {bet_label} のオッズ (スキップは Enter): ").strip()
    if raw == "":
        return None
    try:
        val = float(raw)
        if val > 0:
            return val
    except ValueError:
        pass
    print("  ※ 無効な値のためスキップします")
    return None


# ─────────────────────────────────────────
# 表示ユーティリティ
# ─────────────────────────────────────────

BOAT_COLORS = {1: "白", 2: "黒", 3: "赤", 4: "青", 5: "黄", 6: "緑"}


def boat_label(n: int) -> str:
    color = BOAT_COLORS.get(n, "")
    return f"{n}号艇({color})"


def fmt_pct(v: float) -> str:
    return f"{v * 100:.2f}%"


def fmt_ev(ev: float) -> str:
    sign = "+" if ev >= 0 else ""
    label = " ★期待値プラス" if ev > 0 else ""
    return f"{sign}{ev * 100:.1f}%{label}"


def print_section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def print_ev_row(label: str, prob: float, odds: float, ev: float) -> None:
    marker = " ◆" if ev > 0 else "  "
    print(f"{marker} {label:<28} 確率:{fmt_pct(prob):>8}  オッズ:{odds:>6.1f}  EV:{fmt_ev(ev)}")


# ─────────────────────────────────────────
# メインフロー
# ─────────────────────────────────────────

def input_win_probabilities() -> dict[int, float]:
    """各艇の勝率を入力 (合計100%に正規化)"""
    print_section("各艇の勝率入力")
    print("  ※ 合計が100%でなくても自動で正規化します")
    print("  ※ オッズから逆算する場合は 100÷オッズ で概算できます\n")

    raw: dict[int, float] = {}
    for boat in range(1, 7):
        pct = input_float(f"  {boat_label(boat)} 勝率(%) > ", min_val=0.0, max_val=100.0)
        raw[boat] = pct

    total = sum(raw.values())
    if total <= 0:
        print("  ※ 勝率の合計が0です。均等(16.7%)に設定します")
        return {b: 1 / 6 for b in range(1, 7)}

    probs = {b: v / total for b, v in raw.items()}
    print("\n  [正規化後の勝率]")
    for b, p in probs.items():
        print(f"    {boat_label(b)}: {fmt_pct(p)}")
    return probs


def calc_and_show_tansho(probs: dict[int, float]) -> list[dict]:
    print_section("単勝 (1着)")
    results = []
    for b in range(1, 7):
        odds = input_odds(f"{boat_label(b)}")
        if odds is None:
            continue
        prob = prob_tansho(probs, b)
        ev = expected_value(prob, odds)
        print_ev_row(f"{boat_label(b)}", prob, odds, ev)
        results.append({"bet": "単勝", "label": str(b), "prob": prob, "odds": odds, "ev": ev})
    return results


def calc_and_show_fukusho(probs: dict[int, float]) -> list[dict]:
    print_section("複勝 (2着以内)")
    results = []
    for b in range(1, 7):
        odds = input_odds(f"{boat_label(b)}")
        if odds is None:
            continue
        prob = prob_fukusho(probs, b)
        ev = expected_value(prob, odds)
        print_ev_row(f"{boat_label(b)}", prob, odds, ev)
        results.append({"bet": "複勝", "label": str(b), "prob": prob, "odds": odds, "ev": ev})
    return results


def calc_and_show_kakurenpuku(probs: dict[int, float]) -> list[dict]:
    print_section("拡連複 (3着以内の任意2艇)")
    results = []
    for i, j in combinations(range(1, 7), 2):
        label = f"{i}-{j}"
        odds = input_odds(label)
        if odds is None:
            continue
        prob = prob_kakurenpuku(probs, i, j)
        ev = expected_value(prob, odds)
        print_ev_row(label, prob, odds, ev)
        results.append({"bet": "拡連複", "label": label, "prob": prob, "odds": odds, "ev": ev})
    return results


def calc_and_show_renpuku(probs: dict[int, float]) -> list[dict]:
    print_section("連複 (1・2着 順不同)")
    results = []
    for i, j in combinations(range(1, 7), 2):
        label = f"{i}={j}"
        odds = input_odds(label)
        if odds is None:
            continue
        prob = prob_renpuku(probs, i, j)
        ev = expected_value(prob, odds)
        print_ev_row(label, prob, odds, ev)
        results.append({"bet": "連複", "label": label, "prob": prob, "odds": odds, "ev": ev})
    return results


def calc_and_show_rentan(probs: dict[int, float]) -> list[dict]:
    print_section("連単 (1・2着 順あり)")
    results = []
    for i, j in permutations(range(1, 7), 2):
        label = f"{i}→{j}"
        odds = input_odds(label)
        if odds is None:
            continue
        prob = prob_rentan(probs, i, j)
        ev = expected_value(prob, odds)
        print_ev_row(label, prob, odds, ev)
        results.append({"bet": "連単", "label": label, "prob": prob, "odds": odds, "ev": ev})
    return results


def calc_and_show_sanrenpuku(probs: dict[int, float]) -> list[dict]:
    print_section("3連複 (1〜3着 順不同)")
    results = []
    for i, j, k in combinations(range(1, 7), 3):
        label = f"{i}={j}={k}"
        odds = input_odds(label)
        if odds is None:
            continue
        prob = prob_sanrenpuku(probs, i, j, k)
        ev = expected_value(prob, odds)
        print_ev_row(label, prob, odds, ev)
        results.append({"bet": "3連複", "label": label, "prob": prob, "odds": odds, "ev": ev})
    return results


def calc_and_show_sanrentan(probs: dict[int, float]) -> list[dict]:
    print_section("3連単 (1〜3着 順あり)")
    results = []
    for i, j, k in permutations(range(1, 7), 3):
        label = f"{i}→{j}→{k}"
        odds = input_odds(label)
        if odds is None:
            continue
        prob = prob_sanrentan(probs, i, j, k)
        ev = expected_value(prob, odds)
        print_ev_row(label, prob, odds, ev)
        results.append({"bet": "3連単", "label": label, "prob": prob, "odds": odds, "ev": ev})
    return results


BET_HANDLERS = {
    "1": ("単勝",   calc_and_show_tansho),
    "2": ("複勝",   calc_and_show_fukusho),
    "3": ("拡連複", calc_and_show_kakurenpuku),
    "4": ("連複",   calc_and_show_renpuku),
    "5": ("連単",   calc_and_show_rentan),
    "6": ("3連複",  calc_and_show_sanrenpuku),
    "7": ("3連単",  calc_and_show_sanrentan),
}


def select_bet_types() -> list[str]:
    print_section("計算する賭式を選択")
    for key, (name, _) in BET_HANDLERS.items():
        print(f"  {key}: {name}")
    print("  a: 全賭式")
    print()
    raw = input("  番号をスペース区切りで入力 (例: 1 7 / a=全て) > ").strip().lower()
    if raw == "a" or raw == "":
        return list(BET_HANDLERS.keys())
    selected = []
    for token in raw.split():
        if token in BET_HANDLERS:
            selected.append(token)
        else:
            print(f"  ※ '{token}' は無効です。無視します")
    return selected or list(BET_HANDLERS.keys())


def show_summary(all_results: list[dict]) -> None:
    if not all_results:
        return
    print_section("期待値ランキング (EV降順)")
    sorted_results = sorted(all_results, key=lambda x: x["ev"], reverse=True)
    positive = [r for r in sorted_results if r["ev"] > 0]
    negative = [r for r in sorted_results if r["ev"] <= 0]

    if positive:
        print(f"\n  ★ 期待値プラスの賭式 ({len(positive)}件)")
        for r in positive:
            print(f"   ◆ [{r['bet']:4s}] {r['label']:<28} "
                  f"EV: {fmt_ev(r['ev'])}  (確率:{fmt_pct(r['prob'])}  オッズ:{r['odds']:.1f})")
    else:
        print("\n  期待値プラスの賭式はありませんでした")

    if negative:
        print(f"\n  上位10件 (期待値マイナス)")
        for r in negative[:10]:
            print(f"     [{r['bet']:4s}] {r['label']:<28} "
                  f"EV: {fmt_ev(r['ev'])}  (確率:{fmt_pct(r['prob'])}  オッズ:{r['odds']:.1f})")

    print(f"\n  ※ EVは 0% 以上が理論上プラス収支")
    print(f"  ※ 競艇の払戻率は約75%のため、全体平均は -25% 付近になります")


def main() -> None:
    print("=" * 50)
    print("   競艇 期待値計算プログラム")
    print("   Boat Racing EV Calculator")
    print("=" * 50)

    # 勝率入力
    probs = input_win_probabilities()

    # 賭式選択
    selected_keys = select_bet_types()

    # 各賭式を計算
    all_results: list[dict] = []
    for key in selected_keys:
        _, handler = BET_HANDLERS[key]
        results = handler(probs)
        all_results.extend(results)

    # サマリー表示
    show_summary(all_results)

    print(f"\n{'=' * 50}")
    print("  計算完了")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  中断しました")
        sys.exit(0)
