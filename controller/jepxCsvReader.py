from __future__ import annotations

import datetime
import glob

import pandas as pd


def createDataframe(dataDir: str) -> pd.DataFrame:
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


def getSpotPriceList(df: pd.DataFrame, date: datetime.date, area: str) -> list[float]:
    """
    指定された日付のスポット市場約定価格を返す

    Parameters
    ---------
    df: pd.DataFrame
        createDataFrameで作成したスポット価格のpandasデータフレーム
    date: datetime.date
        取得したい日付
    area: str
        "システム", "北海道" などのエリアを指定
    Returns
    -------
    spotPrice: list[float]
        スポット価格の配列。存在しない場合は要素数ゼロのlistを返す
    """

    dfOfTheDate = df[df["受渡日"] == date.strftime("%Y/%m/%d")]

    if area == "システム":
        return dfOfTheDate["システムプライス(円/kWh)"].to_list()
    else:
        return dfOfTheDate["エリアプライス" + area + "(円/kWh)"].to_list()
