import datetime

import requests


def fetchSpot(dataDir: str, fiscalYear: int = 0) -> None:
    """
    JEPXのサイトからスポット市場の約定結果をダウンロードし、保存する

    Parameters
    ----------
    dataDir: str
        ダウンロードした約定結果の保存先ディレクトリ。絶対パス推奨
    fiscalYear: int
        ダウンロードしたい年度。年ではなく年度なので注意。省略したら当日
    """
    today = datetime.date.today()

    # ダウンロードする年が指定されていなければ今年度分をダウンロード
    if fiscalYear == 0:
        # 1月～3月は年度が変わっていないので、yearのひとつ前を使う
        if today.month <= 3:
            fiscalYear = today.year - 1
        else:
            fiscalYear = today.year

    # JEPXのダウンロードリンクを生成
    jepx_header = {"referer": "https://www.jepx.jp/electricpower/market-data/spot/"}
    jepx_spot_url = (
        "https://www.jepx.jp/js/csv_read.php"
        + "?dir=spot_summary&file=spot_summary_"
        + str(fiscalYear)
        + ".csv"
    )

    # 取得
    response = requests.get(jepx_spot_url, headers=jepx_header)

    # 取得成功時
    if response.status_code == 200:
        # 指定された保存先ディレクトリにファイルを作成。既に存在する場合は上書き。
        # JEPXサイトからダウンロードするファイルはshift_jisらしい。
        filePath = dataDir + "/spot_" + str(fiscalYear) + ".csv"
        with open(filePath, mode="w", encoding="shift-jis", newline="\n") as file:
            # 取得したデータの書き込み
            file.write(response.text)

    else:
        print(jepx_spot_url + " にアクセスできませんでした")

    # 3月31日の場合は、次年度の4月1日の約定結果が出ている可能性があるので、
    # 次年度分もダウンロードする
    if today.month == 3 and today.day == 31:
        fetchSpot(dataDir, fiscalYear + 1)
