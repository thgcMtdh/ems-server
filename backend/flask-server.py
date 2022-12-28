import datetime
import json
from dataclasses import dataclass
from typing import Literal

import pandas as pd
from flask import Flask, abort, render_template
from pydantic import BaseSettings

import jepx
import looop


# 環境変数の読み込み。存在しない場合はValidationErrorを出して終了する
class Env(BaseSettings):
    DATA_DIR: str
    class Config:
        env_file = '.env'

env = Env()


# このウェブアプリでグローバルに使う変数をMyDataクラスに格納しておく
@dataclass
class MyData:
    dfSpotPrice: pd.DataFrame

    def __init__(self):
        self.dfSpotPrice = jepx.createSpotDataframe(env.DATA_DIR)
        self.timesteps = [
            "0:00",
            "0:30",
            "1:00",
            "1:30",
            "2:00",
            "2:30",
            "3:00",
            "3:30",
            "4:00",
            "4:30",
            "5:00",
            "5:30",
            "6:00",
            "6:30",
            "7:00",
            "7:30",
            "8:00",
            "8:30",
            "9:00",
            "9:30",
            "10:00",
            "10:30",
            "11:00",
            "11:30",
            "12:00",
            "12:30",
            "13:00",
            "13:30",
            "14:00",
            "14:30",
            "15:00",
            "15:30",
            "16:00",
            "16:30",
            "17:00",
            "17:30",
            "18:00",
            "18:30",
            "19:00",
            "19:30",
            "20:00",
            "20:30",
            "21:00",
            "21:30",
            "22:00",
            "22:30",
            "23:00",
            "23:30",
        ]
        self.colors = {
            "システム": "#5AC0F8",
            "北海道": "#2A6FF8",
            "東北": "#745AF8",
            "東京": "#5AF86B",
            "中部": "#F8F55A",
            "北陸": "#F8B62A",
            "関西": "#F86E5A",
            "中国": "#FDB4C5",
            "四国": "#F54ABC",
            "九州": "#FF0037",
            "沖縄": "#5AC0F8",
        }

    def update(self):
        """
        定期的にデータを更新する
        """
        pass


myData = MyData()


# ウェブサーバの起動
app = Flask(__name__, static_folder="../frontend/static", template_folder="../frontend/template")
app.config["JSON_AS_ASCII"] = False  # 日本語のjsonを扱えるように


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/price/jepx/<yearStr>/<monthStr>/<dayStr>")
def getPriceJepx(yearStr: str, monthStr: str, dayStr: str):
    year = int(yearStr)
    month = int(monthStr)
    day = int(dayStr)
    spotPrice = jepx.getSpotPrice(myData.dfSpotPrice, datetime.date(year, month, day))
    areas: list[
        Literal[
            "システム",
            "北海道",
            "東北",
            "東京",
            "中部",
            "北陸",
            "関西",
            "中国",
            "四国",
            "九州",
        ]
    ] = ["システム", "北海道", "東北", "東京", "中部", "北陸", "関西", "中国", "四国", "九州"]
    if len(spotPrice["システム"]) > 0:  # 要素が入っていたら
        return json.dumps(
            {
                "labels": myData.timesteps,
                "datasets": [
                    {
                        "label": area,
                        "data": spotPrice[area],
                        "borderColor": myData.colors[area],
                        "fill": "none",
                        "tension": 0,
                    }
                    for area in areas
                ],
            }
        )
    else:
        return json.dumps({})  # 何も要素がないときは空オブジェクトを返す


@app.route("/api/price/looop/<yearStr>/<monthStr>/<dayStr>")
def getPriceLooop(yearStr: str, monthStr: str, dayStr: str):
    year = int(yearStr)
    month = int(monthStr)
    day = int(dayStr)
    spotPrice = jepx.getSpotPrice(myData.dfSpotPrice, datetime.date(year, month, day))
    looopPrice = looop.calcPrice(spotPrice)
    areas: list[
        Literal[
            "北海道",
            "東北",
            "東京",
            "中部",
            "北陸",
            "関西",
            "中国",
            "四国",
            "九州",
            "沖縄",
        ]
    ] = ["北海道", "東北", "東京", "中部", "北陸", "関西", "中国", "四国", "九州", "沖縄"]
    if len(looopPrice["北海道"]) > 0:  # 要素が入っていたら
        return json.dumps(
            {
                "labels": myData.timesteps,
                "datasets": [
                    {
                        "label": area,
                        "data": looopPrice[area],
                        "borderColor": myData.colors[area],
                        "fill": "none",
                        "tension": 0,
                    }
                    for area in areas
                ],
            }
        )
    else:
        return json.dumps({})  # 何も要素がないときは空オブジェクトを返す


@app.route("/api/price/jepx/areas")
def getPriceJepxAreas():
    return json.dumps(
        [
            "システム",
            "北海道",
            "東北",
            "東京",
            "中部",
            "北陸",
            "関西",
            "中国",
            "四国",
            "九州",
        ]
    )


@app.route("/api/price/looop/areas")
def getPriceLooopAreas():
    return json.dumps(
        [
            "北海道",
            "東北",
            "東京",
            "中部",
            "北陸",
            "関西",
            "中国",
            "四国",
            "九州",
            "沖縄",
        ]
    )


@app.route("/price/<company>")
def priceLooop(company):
    if company == "looop":
        return render_template("priceGraph.html", title="Looopでんき エリアプライス", companyKey="looop")
    elif company == "jepx":
        return render_template("priceGraph.html", title="JEPXスポット市場約定価格", companyKey="jepx")
    else:
        return abort(404)
