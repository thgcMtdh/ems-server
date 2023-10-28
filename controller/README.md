## セットアップ

### ループタスクの自動起動

loopTask.py の中で、充放電指令とログの取得を行っている。
loopTask.py がシステム起動時に自動実行されるように systemd を編集する。

やり方例：https://www.pc-koubou.jp/magazine/52061

### .env ファイル

controller 直下に以下のような `.env` ファイルを作成する。

```
DATA_DIR=C:/Users/xxxx/Documents/ems-server-data  # 各種データの保存先
```

### データ保存先のディレクトリ構造の作成

`DATA_DIR` で指定したディレクトリに、以下のようなディレクトリ構造を作って、default.csv を格納する

- chargePlan/  : 充放電計画が保存されるフォルダ
  - default.csv
- demandPlan/  : 需要計画が保存されるフォルダ
  - default.csv
- measureLog/ : 計測値が保存されるフォルダ

chargePlan の default.csv

```csv
"time","acdc","inv","soc"
"00:00",1,0,1000
"00:30",1,0,1000
....
"23:30",1,0,1000
``````

demandPlan の default.csv

```csv
"time","dcDemand","acDemand"
"00:00",10,40
"00:30",10,40
....
"23:30",10,40
``````
