

## .env ファイル

controller 直下に `.env` ファイルを以下のように作成。

```
DATA_DIR=C:/Users/xxxx/Documents/ems-server-data  # 各種データの保存先
```

## データフォルダのディレクトリ構造

DATA_DIR で指定したディレクトリに、以下のようなディレクトリ構造を作ってファイルを入れる

- chargePlan/  : 充放電計画が保存されるフォルダ
  - default.csv
- demandPlan/  : 需要計画が保存されるフォルダ
  - default.csv
- spot_2023.csv  : JEPX 価格はルートに保存される

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
