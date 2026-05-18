def calculate_profit(cost_price, sell_price, shipping_cost):
    """
    利益を計算する関数
    cost_price   : 仕入れ値（円）
    sell_price   : 売値（円）
    shipping_cost: 送料（円）
    """
    mercari_fee = sell_price * 0.10      # メルカリ手数料10%
    transfer_fee = 200                   # 振込手数料（200円）

    total_cost = cost_price + shipping_cost + mercari_fee + transfer_fee
    profit = sell_price - total_cost
    profit_rate = (profit / sell_price) * 100 if sell_price > 0 else 0

    return {
        "売値":         sell_price,
        "仕入れ値":     cost_price,
        "送料":         shipping_cost,
        "メルカリ手数料": round(mercari_fee),
        "振込手数料":   transfer_fee,
        "利益":         round(profit),
        "利益率":       round(profit_rate, 1),
    }


def judge(profit, profit_rate):
    """利益判定"""
    if profit >= 1000 and profit_rate >= 20:
        return "◎ 優良物件！買い！"
    elif profit >= 500 and profit_rate >= 10:
        return "○ 悪くない。検討あり"
    elif profit >= 0:
        return "△ 利益薄い。慎重に"
    else:
        return "✕ 赤字。やめとこう"


SHIPPING_PRESETS = {
    "1": ("らくらくメルカリ便（60サイズ）", 750),
    "2": ("らくらくメルカリ便（80サイズ）", 850),
    "3": ("らくらくメルカリ便（100サイズ）", 1050),
    "4": ("ゆうパケット（〜3cm）",           230),
    "5": ("ネコポス（〜2.5cm）",             210),
    "6": ("手入力する",                       None),
}


def select_shipping():
    """送料をプリセットから選ぶ"""
    print("\n【送料を選んでください】")
    for key, (name, price) in SHIPPING_PRESETS.items():
        price_str = f"{price}円" if price else "手入力"
        print(f"  {key}: {name}  ({price_str})")

    while True:
        choice = input("\n番号を入力: ").strip()
        if choice in SHIPPING_PRESETS:
            name, price = SHIPPING_PRESETS[choice]
            if price is None:
                price = int(input("送料を入力（円）: "))
            return name, price
        print("1〜6の番号を入力してください")


def main():
    print("=" * 40)
    print("   せどり利益計算ツール")
    print("=" * 40)

    while True:
        try:
            cost_price = int(input("\n仕入れ値を入力（円）: "))
            sell_price = int(input("売値を入力（円）  : "))
            shipping_name, shipping_cost = select_shipping()

            result = calculate_profit(cost_price, sell_price, shipping_cost)
            verdict = judge(result["利益"], result["利益率"])

            print("\n" + "=" * 40)
            print("【計算結果】")
            print(f"  売値          : {result['売値']:,}円")
            print(f"  仕入れ値      : {result['仕入れ値']:,}円")
            print(f"  送料({shipping_name}): {result['送料']:,}円")
            print(f"  メルカリ手数料: {result['メルカリ手数料']:,}円")
            print(f"  振込手数料    : {result['振込手数料']:,}円")
            print("-" * 40)
            print(f"  利益          : {result['利益']:,}円")
            print(f"  利益率        : {result['利益率']}%")
            print(f"\n  判定 → {verdict}")
            print("=" * 40)

        except ValueError:
            print("数字を入力してください")
            continue

        again = input("\n続けて計算しますか？ (y/n): ").strip().lower()
        if again != "y":
            print("\n終了します。")
            break


if __name__ == "__main__":
    main()
