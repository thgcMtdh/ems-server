# ems-server
自宅EMSシステムのサーバー側のコード

## backend
Flask backend。以下を行う。
- 監視用ウェブサイトGUIのホスティング
- ウェブサイト用APIの提供
- エッジデバイスとの通信APIの提供（今後実装予定）

### .envファイル
- `DATA_DIR`: EMSシステムの動作に必要な一切のデータの保存先。絶対パスで記述

### crontabによる定期実行スクリプト
cron_というprefixのついた以下のスクリプトについては、定期実行する必要がある
- `cron_jepxFetch.py`: JEPXからのスポット価格取得を行う。毎日10:30に実行すること
- 今後、以下のようなタスクを追加予定
  - エッジデバイスとの定期的な通信
  - 最適化計算

## frontend
フロントで表示するウェブページ。Flaskのフォルダ構成（templatesとstatic）を採用している。主な内容は、
- 市場価格の表示
- システム監視画面（今後実装予定）
