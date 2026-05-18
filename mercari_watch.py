import time

def main():
    print("メルカリ監視ツール 起動しました")
    print("停止するには Ctrl+C を押してください\n")

    try:
        while True:
            print("メルカリを監視中...")
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n監視を停止しました。")

if __name__ == "__main__":
    main()
