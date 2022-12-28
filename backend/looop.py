import math
from typing import TypedDict

import jepx


class AreaPrice(TypedDict):
    北海道: list[float]
    東北: list[float]
    東京: list[float]
    中部: list[float]
    北陸: list[float]
    関西: list[float]
    中国: list[float]
    四国: list[float]
    九州: list[float]
    沖縄: list[float]


def calcPrice(spotPrice: jepx.SpotPrice) -> AreaPrice:
    """
    Looopでんきの「スマートタイムONE(電灯)電気料金種別定義書」をもとに、電力量料金を計算する。
    """
    # 3.45は再エネ賦課金(2022年度)
    def func(
        areaPrice: float, LOSS_RATE: float, TAX_RATE: float, USAGE_FEE: float, RE_SURCHARGE: float, DISCOUNT: float
    ) -> float:
        dengenRyoukin = math.floor((areaPrice / (1 - LOSS_RATE) * (1 + TAX_RATE)) * 100) / 100  # 第3位を切り捨て
        dengenRyoukin = dengenRyoukin + USAGE_FEE + RE_SURCHARGE - DISCOUNT
        dengenRyoukin = math.floor(dengenRyoukin * 100) / 100
        return dengenRyoukin

    looopPrice = AreaPrice(
        北海道=list(map(lambda x: func(x, 0.076, 0.1, 15.41, 3.45, 0), spotPrice["北海道"])),
        東北=list(map(lambda x: func(x, 0.082, 0.1, 16.04, 3.45, 0), spotPrice["東北"])),
        東京=list(map(lambda x: func(x, 0.069, 0.1, 15.11, 3.45, 0), spotPrice["東京"])),
        中部=list(map(lambda x: func(x, 0.067, 0.1, 15.60, 3.45, 0), spotPrice["中部"])),
        北陸=list(map(lambda x: func(x, 0.079, 0.1, 14.05, 3.45, 0), spotPrice["北陸"])),
        関西=list(map(lambda x: func(x, 0.078, 0.1, 14.15, 3.45, 0), spotPrice["関西"])),
        中国=list(map(lambda x: func(x, 0.080, 0.1, 14.68, 3.45, 0), spotPrice["中国"])),
        四国=list(map(lambda x: func(x, 0.083, 0.1, 15.08, 3.45, 0), spotPrice["四国"])),
        九州=list(map(lambda x: func(x, 0.082, 0.1, 14.82, 3.45, 0), spotPrice["四国"])),
        沖縄=list(map(lambda x: func(x, 0.061, 0.1, 16.66, 3.45, 0), spotPrice["システム"])),
    )
    return looopPrice
