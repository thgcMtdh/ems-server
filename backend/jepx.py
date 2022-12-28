import datetime
import glob
from typing import TypedDict

import pandas as pd
import requests


class SpotPrice(TypedDict):
    システム: list[float]
    北海道: list[float]
    東北: list[float]
    東京: list[float]
    中部: list[float]
    北陸: list[float]
    関西: list[float]
    中国: list[float]
    四国: list[float]
    九州: list[float]


def fetchSpot(dataDir: str, fiscalYear: int = 0) -> None:
    """
    JEPXのサイトからスポット市場の約定結果をダウンロードし、保存する

    Parameters
    ----------
    dataDir: str
        ダウンロードした約定結果の保存先ディレクトリ。絶対パス推奨
    fiscalYear: int
        ダウンロードしたい年度。年ではなく年度なので注意
    """
    today = datetime.date.today()

    # ダウンロードする年が指定されていなければ今年度分をダウンロード
    if fiscalYear == 0:

        # 1月～3月は年度が変わっていないので、yearのひとつ前を使う
        if today.month <= 3:
            fiscalYear = today.year - 1
        else:
            fiscalYear = today.year

    # 指定された保存先ディレクトリにファイルを作成。既に存在する場合は上書き
    file = open(dataDir + "/spot_" + str(fiscalYear) + ".csv", "wb")

    # JEPXのダウンロードリンクを生成
    jepx_spot_url = "http://www.jepx.org/market/excel/spot_" + str(fiscalYear) + ".csv"

    # 取得
    response = requests.get(jepx_spot_url)

    # 取得成功時
    if response.status_code == 200:

        # ファイルを書き込み
        for chunk in response.iter_content(100000):
            file.write(chunk)

        # 閉じる
        file.close()

    else:
        print(jepx_spot_url + " にアクセスできませんでした")

    # 3月31日の場合は、次年度の4月1日の約定結果が出ている可能性があるので、
    # 次年度分もダウンロードする
    if today.month == 3 and today.day == 31:
        fetchSpot(dataDir, fiscalYear + 1)


def createSpotDataframe(dataDir: str) -> pd.DataFrame:
    """
    JEPXスポット市場約定結果のCSVファイルから、pandasデータフレームを生成する

    Parameters
    ----------
    dataDir: str
        約定結果の保存先ディレクトリ。絶対パス推奨
    Returns
    -------
    df: pd.DataFrame
        保存されている全てのJEPXスポット市場価格を格納したデータフレーム
    """
    dfs: list[pd.DataFrame] = []

    # 指定されたディレクトリに存在する全てのCSVファイルを読み取り、データフレームとして格納する
    for filename in glob.glob(dataDir + "/spot_*.csv"):
        dfs.append(pd.read_csv(filename, encoding="shift_jis"))

    # 読み取った全てのデータフレームを連結して返す
    if dfs:
        return pd.concat(dfs)
    else:
        print("データがありません")
        raise FileNotFoundError


def getSpotPrice(df: pd.DataFrame, date: datetime.date) -> SpotPrice:
    """
    指定された日付のスポット市場約定価格を返す

    Parameters
    ---------
    date: datetime.date
        取得したい日付
    Returns
    -------
    spotPrice: jepx.SpotPrice
        各エリアのスポット市場価格
    """
    dfOfTheDate = df[df["年月日"] == date.strftime("%Y/%m/%d")]
    spotPrice = SpotPrice(
        システム=dfOfTheDate["システムプライス(円/kWh)"].to_list(),
        北海道=dfOfTheDate["エリアプライス北海道(円/kWh)"].to_list(),
        東北=dfOfTheDate["エリアプライス東北(円/kWh)"].to_list(),
        東京=dfOfTheDate["エリアプライス東京(円/kWh)"].to_list(),
        中部=dfOfTheDate["エリアプライス中部(円/kWh)"].to_list(),
        北陸=dfOfTheDate["エリアプライス北陸(円/kWh)"].to_list(),
        関西=dfOfTheDate["エリアプライス関西(円/kWh)"].to_list(),
        中国=dfOfTheDate["エリアプライス中国(円/kWh)"].to_list(),
        四国=dfOfTheDate["エリアプライス四国(円/kWh)"].to_list(),
        九州=dfOfTheDate["エリアプライス九州(円/kWh)"].to_list(),
    )
    return spotPrice
