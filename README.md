# ragtag-get
### これは何
ragtagのアーカイブを取得する補助ツールです。  
videos.ndjsonを元に、指定したチャンネルの削除済み動画のURLを抽出できます。

### どう使う
python実行環境を用意してragtag-get.pyをソイヤしてください。


### reducer.py
videos.ndjsonをチャンネルIDで出切りだして保存します。   
扱うチャンネルが決まっている場合、ndjsonの読み込み時間を大幅に短縮できます。