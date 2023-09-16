from pydantic import BaseModel


class Constants(BaseModel):
    """
    Looopでんきの料金計算で使う定数。
    [電気料金種別定義書](https://looop-denki.com/assets/files/contract/smarttimeone_dentou.pdf)
    を参照。
    """

    lossRate: float = 0.069  # エリア損失率
    taxRate: float = 0.1  # 消費税率
    transmissionFee: float = 9.78  # 託送料金[円/kWh]
    serviceFee: float = 5.5  # サービス料[円/kWh]
    surchargeFee: float = 1.40  # 再エネ賦課金[円/kWh]
    discountFee: float = 3.5  # 割引額(割引時に正)[円/kWh]


def calcPrice(areaPrice: float, constants: Constants = Constants()) -> float:
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
