from pydantic import BaseModel


class Constants(BaseModel):
    """
    Looopでんきの料金計算で使う定数。
    [電気料金種別定義書](https://looop-denki.com/assets/files/contract/smarttimeone_dentou.pdf)
    を参照。
    """

    lossRate: float  # エリア損失率
    taxRate: float  # 消費税率
    transmissionFee: float  # 託送料金[円/kWh]
    serviceFee: float  # サービス料[円/kWh]
    surchargeFee: float  # 再エネ賦課金[円/kWh]
    discountFee: float = 0.0  # 割引額(割引時に正)[円/kWh]


def calcPrice(areaPrice: float, constants: Constants) -> float:
    """
    JEPXエリアプライスをもとに、LooopでんきスマートタイムONE(電灯)における
    電力量料金を計算する。
    """
    dengenRyoukin = areaPrice / (1 - constants.lossRate) * (1 + constants.taxRate)
    dengenRyoukin = int(dengenRyoukin * 100) / 100  # 第3位を切り捨て
    juryoRyoukin = constants.transmissionFee + constants.serviceFee
    juryoRyoukin = int(juryoRyoukin * 100) / 100  # 第3位を切り捨て
    sum = dengenRyoukin + juryoRyoukin + constants.surchargeFee - constants.discountFee
    return round(sum, 2)  # sumの計算でfloat誤差が出るので再度round


# if __name__ == "__main__":
#     constants = Constants(
#         lossRate=0.069,
#         taxRate=0.1,
#         transmissionFee=9.78,
#         serviceFee=5.5,
#         surchargeFee=1.40,  # 2023年度再エネ賦課金
#         discountFee=7.0,  # 激変緩和事業
#     )
#     print(calcPrice(14.55, constants))
