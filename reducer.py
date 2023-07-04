import sys
from pathlib import Path

import ndjson
import requests
from bs4 import BeautifulSoup


def main():
    print('videos.ndjsonを、チャンネルIDから抽出分割して書き出し、ファイルサイズを削減します。')

    print("")
    print("まず、videos.ndjsonのパスを指定してください。")
    print("読み込み時に、弊環境では" + "\033[31m" + "メモリを8GB消費" + "\033[0m" + "しました。ご注意ください。")
    str_ndp = input("> ")
    if str_ndp == "":
        str_ndp = "videos.ndjson"
    ndp = Path(get_clean_path(str_ndp))
    if ndp.exists() is False:
        print("ndjsonが見つかりません。参照先を確認してください。")
        sys.exit()

    print("データベースを読み込み中です……", end="")
    try:
        with ndp.open('r', encoding='utf8') as file:
            nd_data = ndjson.load(file)
    except:
        print("\r\033[31m" + "データベースの読み込みに失敗しました。ファイルの正常性を確認してください。" + "\033[0m")
        sys.exit()
    print("\rデータベース読み込み完了")

    print("チャンネルIDを指定してください。")
    print("Youtube handleでも検索可能です。先頭に@を付けてください。")
    channel_id = input("channel_id> ")

    if channel_id.startswith("@"):
        print(f"Youtube handleが入力されたようです。チャンネルIDを検索します。")
        print()
        channel_id = get_channel_id(channel_id)
        if not channel_id is None:
            print("チャンネルIDを取得しました。")
            print(f"{channel_id}を検索します。")
            print()
        else:
            print(f"チャンネルIDを取得できませんでした。")
            return

    first = True  # チャンネル名を1回だけ表示するためのフラグ

    videos = []  # チャンネルIDで絞り込む
    for item in nd_data:
        if item.get('channel_id') == channel_id:
            channel_name = item.get('channel_name')
            if first:
                print("channel_name:", channel_name)
                first = False
            videos.append(item)

    if len(videos) == 0:
        print("指定されたチャンネルがデータベース内にありませんでした。")
        return

    print(f"{len(videos)}件の動画が見つかりました。")

    export_path = Path(channel_id + ".ndjson")
    if export_path.exists():
        if ask_yes_no(export_path.name + " が存在しています。上書きしますか？"):
            pass
        else:
            return

    ndjson.dump(videos, export_path.open("w", encoding='utf8'), ensure_ascii=False)

    print(export_path.name + " に書き出しました。")


def get_clean_path(raw_path):
    if raw_path.startswith('\'') and raw_path.endswith('\'') or raw_path.startswith('"') and raw_path.endswith('"'):
        return raw_path[1:-1]
    else:
        return raw_path


def get_channel_id(handle: str):
    try:
        res = requests.get(f"https://www.youtube.com/{handle}")
        if res.status_code != 200:
            return None
        soup = BeautifulSoup(res.content, 'html.parser')
        canonical_url = soup.find(rel="canonical").get('href')
        res = requests.get(canonical_url)
        if res.status_code != 200:
            return None
    except:
        return None
    return canonical_url.split('/')[-1]


def ask_yes_no(question):
    while True:
        response = input(question + " (yes/no): ").lower()
        if response in ["yes", "y"]:
            return True
        elif response in ["no", "n"]:
            return False
        else:
            print("Invalid response. Please enter yes or no.")


if __name__ == "__main__":
    main()
