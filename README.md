# ems-server
自宅EMSシステムのサーバー側のコード

## backend
Flask backend。以下を行う。
- 監視用ウェブサイトGUIのホスティング
- ウェブサイト用APIの提供
- エッジデバイスとの通信APIの提供（今後実装予定）

.envファイルに必要な情報は以下の通り
- `DATA_DIR`: EMSシステムの動作に必要な一切のデータの保存先。絶対パスで記述

## crontask（今後実装予定）
定時実行処理をまとめておく場所。例えば、以下のようなタスクを行うpythonファイルが入る
- JEPXからの約定結果取得
- エッジデバイスとの定期的な通信
- 最適化計算

## frontend
フロントで表示するウェブページ。Flaskのフォルダ構成（templatesとstatic）を採用している。主な内容は、
- 市場価格の表示
- システム監視画面（今後実装予定）
