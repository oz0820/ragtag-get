import sys
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
import ndjson
import requests


def video_rename():
    print("ダウンロードしたファイルを保存しているパスを指定して、SQフォーマットにリネームします。")
    str_path = input("targetPath> ")
    p = Path(get_clean_path(str_path))
    for a in p.glob("*"):
        vid = a.stem.split(".")[0]  # .chat.json等に苦しめられた
        item = search_vid(vid)

        if item is None:
            print(f"データベースに{a.name}が存在しませんでした。")
            continue

        data_type = ""
        if len(a.stem.split(".")) == 2:
            data_type = "." + a.stem.split(".")[1]
            if data_type == ".chat":
                data_type = ".live_chat"  # QSフォーマットに遵守

        name_after = f"{item['upload_date'].replace('-', '')}-[{replace_invalid_chars(item['title'])}]-[{item['video_id']}]{data_type}{a.suffix}"
        a.rename(a.with_name(name_after))


def get_resource_urls():
    print("チャンネルIDを指定して、削除された動画のリソースを抽出します。")
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

    print(f"{len(videos)}件の動画が見つかりました。削除済みの動画を選別します。")
    print()

    deleted = []  # サムネイルが存在しない動画だけ選別
    for index, item in enumerate(videos):
        index += 1
        files = item.get('files')
        resources = [f.get('name') for f in files]
        drive_base = item.get('drive_base')
        video_id = item.get('video_id')

        # サムネイルの存在確認
        digit = str(len(str(len(videos))))
        if check_file_exists(f"https://i.ytimg.com/vi/{video_id}/0.jpg"):
            print(f"\r{index:{digit}}\texist.\t\t{video_id}\t{item.get('title')}", end="")
            continue
        else:
            print(f"\r{index:{digit}}\tdeleted.\t{video_id}\t{item.get('title')}")
            deleted.append(item)

    print(f"\r{len(deleted)}件の削除済み動画が見つかりました。\n")
    if len(deleted) == 0:
        return

    error_item = []  # 取得データに欠損など、エラーがあったときにデータが追加される
    output_list = []  # 書き出しデータのtxtを突っ込む

    for item in deleted:
        files = item.get('files')
        resources = [f.get('name') for f in files]
        drive_base = item.get('drive_base')
        video_id = item.get('video_id')

        print(end="\r")
        data_type = {
            "image": None,
            "video": None,
            "info": None,
            "chat": None
        }

        for st in resources:
            if st.endswith('.webp'):
                data_type['image'] = st
            elif st.endswith('.jpg'):
                if data_type['image'] is None:
                    data_type['image'] = st

            elif st.endswith('.mkv'):
                data_type['video'] = st
            elif st.endswith('.mp4'):
                if data_type['video'] is None:
                    data_type['video'] = st

            elif st.endswith('.info.json'):
                data_type['info'] = st

            elif st.endswith('.chat.json'):
                data_type['chat'] = st

        if any(value is None for key, value in data_type.items() if key != 'chat'):
            error_item.append(item)
            continue

        request_list = [val for val in data_type.values()]

        for resource in request_list:
            if resource is None:
                continue
            output_list.append(f"https://content.archive.ragtag.moe/gd:{drive_base}/{video_id}/{resource}")

    print(f"ダウンロードURLが{len(output_list)}件あります。出力方法を選んでください。")
    while True:
        print("1: コンソールに出力する")
        print("2: ファイルに保存する")
        s = input(">> ")
        if s == "1":
            print("-----------------------------")
            for u in output_list:
                print(u)
            print("-----------------------------")
            break
        elif s == "2":
            str_export_path = input("exportPath> ")
            str_export_path = get_clean_path(str_export_path)
            export_path = Path(str_export_path).resolve()
            if export_path.exists():
                print(f"{export_path.name} は存在します。別の名前を指定してください。")
                continue
            with export_path.open('w', encoding='utf8') as f:
                for u in output_list:
                    f.write(u + "\n")
            print(f"{export_path} に書き出しました。")
            break

    if len(error_item) != 0:
        print(f"ダンプデータ参照の過程でエラーが生じた動画が{len(error_item)}件あります。")
        print("表示する場合はEnterを押してください。表示しない場合は\"NO\"と入力してください。")
        sel = input(">> ")
        if sel == "NO":
            return
        else:
            print("エラーが発生した動画のVideoIDを表示します。")
            print("-----------------------------")
            for item in error_item:
                print(f"{item.get('video_id')}\t{item.get('title')}")
            print("-----------------------------")


# URL先のコンテンツを取得できればヨシ！
def check_file_exists(url):
    try:
        response = urllib.request.urlopen(url)
        return True
    except urllib.error.HTTPError:
        return False


def search_vid(vid):
    for item in nd_data:
        if item.get('video_id') == vid:
            return item
    return None


def get_clean_path(raw_path):
    if raw_path.startswith('\'') and raw_path.endswith('\'') or raw_path.startswith('"') and raw_path.endswith('"'):
        return raw_path[1:-1]
    else:
        return raw_path


# ファイルシステム上都合の悪い文字を置き換えます
def replace_invalid_chars(filename):
    invalid_chars = r'<>:"/\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


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


if __name__ == "__main__":
    print("このツールは、ragtagアーカイブ取得を補助するツールです。")
    print("まず、抽出モードでダウンロードするファイルのURLリストを生成します。")
    print("次に、何らかの方法でそのファイル群を一つのフォルダにダウンロードします。")
    print("最後に、変換モードでファイル名をQSフォーマットに準拠させます。")

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

    while True:
        print("\n\n動作モードを選択してください。")
        print("1: 抽出モード, 2: 変換モード, 3: 終了")
        raw = input(">> ")
        if raw == "1":
            get_resource_urls()
        elif raw == "2":
            video_rename()
        elif raw == "3":
            sys.exit()
