import datetime

from pydantic_settings import BaseSettings

import jepxCsvReader
import looop
import optimization
from PlanFile import PlanFile


class MyEnv(BaseSettings):
    DATA_DIR: str

    class Config:
        env_file = ".env"


# 環境変数の読み込み
# .env ファイルの書き方と、 DATA_DIR については、README を参照
env = MyEnv()


# 今日(+データがあれば明日)のjepx価格を取得
now = datetime.datetime.today()
tommorow = now + datetime.timedelta(days=1)
jepxDf = jepxCsvReader.createDataframe(env.DATA_DIR)
todayPriceList = jepxCsvReader.getSpotPriceList(jepxDf, now, "東京")
tommorowPriceList = jepxCsvReader.getSpotPriceList(jepxDf, tommorow, "東京")
jepxPriceList = todayPriceList + tommorowPriceList

# 現在時刻のコマを求め、価格リストを現在コマ～最終コマ までに絞る
# たとえば2:00なら beginIndex=4
beginIndex = int(48 * (60 * now.hour + now.minute) / 1440)
jepxPriceList = jepxPriceList[beginIndex:]
length = len(jepxPriceList)

# Looopの価格に換算
looopPriceList = [looop.calcPrice(p) for p in jepxPriceList]

# 需要を取得
demandPlanFile = PlanFile(env.DATA_DIR + "/demandPlan/")
demandDataDict = demandPlanFile.extract(now, beginIndex, length)
dcDemandList = demandDataDict["dcDemand"]
acDemandList = demandDataDict["acDemand"]

# 初期SOCを取得。さしあたり直前の計算結果から取ってくる
chargePlanFile = PlanFile(env.DATA_DIR + "/chargePlan/")
initSoc = chargePlanFile.extract(now, beginIndex, 1)["soc"][0] / 1000

# 最適化計算
acdcCommand, invCommand, socPermill = optimization.do(
    initSoc, looopPriceList, dcDemandList, acDemandList
)
data = {"acdc": acdcCommand, "inv": invCommand, "soc": socPermill}

# 保存
chargePlanFile.overwrite(now, beginIndex, length, data)
