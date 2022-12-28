import datetime
import glob
from typing import TypedDict

import pandas as pd


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
