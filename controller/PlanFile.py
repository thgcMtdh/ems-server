import datetime
import os

import pandas as pd


class PlanFile:
    dir: str = ""
    DEFAULT_FILE_NAME = "default.csv"

    def __init__(self, dir: str) -> None:
        """
        30分値を記録したCSVファイルが日別に保存されているディレクトリに対して、日時を指定した読み書きを行うモジュール。

        [想定するディレクトリのイメージ]
        ```
        dir/
          20230801.csv
          20230802.csv
          ...
          default.csv
        ```

        Parameters
        ----------
        dir: str
            CSVが保存されているディレクトリ。
        """
        self.dir = dir

    def read(self, theDate: datetime.datetime) -> pd.DataFrame:
        """
        指定した日付のファイルを読み込む。存在しない場合は default.csv を返す。
        default.csv も存在しない場合は FileNotFoundError を返す。

        Parameters
        ----------
        `theDate`: datetime.datetime
            読み込みたい日付
        """

        path = self.dir + theDate.strftime("%Y%m%d") + ".csv"
        defaultPath = self.dir + self.DEFAULT_FILE_NAME

        if os.path.isfile(path):
            return pd.read_csv(path)  # 指定された日の需要ファイルが存在すれば読み込み

        if os.path.isfile(defaultPath):
            return pd.read_csv(defaultPath)  # 存在しなければdefaultを返す

        raise FileNotFoundError

    def extract(
        self, beginDate: datetime.datetime, beginIndex: int, length: int
    ) -> dict:
        """
        指定した日 `theDate` の指定したコマ `beginIndex` から始まるデータを `length` コマぶん取得する。
        データが存在しない日については default.csv の値を返す。
        2日分(今日と明日)しか対応していない。期間が明後日に被ってしまった場合の動作は未定義。

        Returns
        -------
        `dict`: {column -> [values]}
            列名を key, 数値列の list を value にもつ辞書。
            たとえば `{"dcDemand": [10, 15, 10], "acDemand": [40, 40, 40]}` のようなイメージ。
        """

        if beginIndex + length <= 48:  # 当日分に収まれば
            dfToday = self.read(beginDate)
            return dfToday[beginIndex : beginIndex + length].to_dict(orient="list")

        elif beginIndex + length <= 96:  # 当日と翌日
            nextDate = beginDate + datetime.timedelta(days=1)
            dfToday = self.read(beginDate)
            dfTommorow = self.read(nextDate)
            dfConcat = pd.concat([dfToday, dfTommorow])
            return dfConcat[beginIndex : beginIndex + length].to_dict(orient="list")

        else:
            raise ValueError

    def overwrite(
        self, beginDate: datetime.datetime, beginIndex: int, length: int, data: dict
    ) -> None:
        """
        指定した日 `theDate` の指定したコマ `beginIndex` から `length` コマぶんデータを上書きする。
        ファイルが存在しない場合は新規生成され、データが与えられていない時刻コマは default.csv の値で埋められる。
        再帰を使っているので何日でも書けると思うが未検証。今日と明日は動作確認済み。

        例）
        beginDate = 2023/8/1, beginIndex = 2, length = 3 とし、
        `{"dcDemand": [10, 10, 10], "acDemand": [90, 90, 90]}`
        というデータを保存するよう指定すると：

        20230801.csv が存在していれば、
            '01:00', '01:30', '02:00' の dcDemand と acDemand が、それぞれ10と90で上書きされる
        20230801.csv が存在しない場合、
            default.csv をコピーして 20230801.csv が新規作成され、当該3コマだけが指定値で上書きされる
        """

        path = self.dir + beginDate.strftime("%Y%m%d") + ".csv"
        defaultPath = self.dir + self.DEFAULT_FILE_NAME

        if beginIndex + length <= 48:  # 当日分に収まれば
            # 上書き元のデータを読み込む
            if os.path.isfile(path):
                df = pd.read_csv(path)
            else:
                df = pd.read_csv(defaultPath)

            # 与えられたデータで上書きして保存する
            for rowIndex in range(beginIndex, beginIndex + length):
                for key in data.keys():
                    df.loc[rowIndex, key] = data[key][rowIndex - beginIndex]
            df.to_csv(path, header=True, index=False)

        else:  # 当日分に収まらない場合
            # まず当日分を書く
            self.overwrite(beginDate, beginIndex, 48 - beginIndex, data)

            # 書けていない翌日以降分のデータを抽出
            remainingData = data
            for key in remainingData.keys():
                remainingData[key] = data[key][48 - beginIndex :]
            remainingLength = length - (48 - beginIndex)

            # 翌日以降分を書く
            newDate = beginDate + datetime.timedelta(days=1)
            self.overwrite(newDate, 0, remainingLength, remainingData)
