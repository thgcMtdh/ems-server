import pulp


def lpSolve(
    initSoc: float,
    priceList: list[float],
    dcDemandList: list[float],
    acDemandList: list[float],
) -> tuple[list[float]]:
    """
    最適化計算を行う

    Parameters
    ----------
    initSoc: float
        初期・終期SOC (0～1)
    priceList: list[float]
        計算したいコマの電力価格[円/kWh]
    dcDemandList: list[float]
        計算したいコマのDC需要[W]
    acDemandList: list[float]
        計算したいコマのAC需要[W]

    Returns
    -------
    (acdcPowerList, invPowerList): tuple[list[float]]
        変換器の出力電力[W]のリスト, インバータの出力電力[W]のリスト, SOCのリスト
    """

    # 定数
    BATT_CAPACITY_WH = 12 * 100
    MAX_SOCRATE = 1.00
    MIN_SOCRATE = 0.50
    ACDC_PWR_W = 150
    EFF_ACDC = 0.80
    EFF_INV = 0.85

    # 全ての配列の長さが一致しているか確認
    if len(priceList) != len(dcDemandList) or len(priceList) != len(acDemandList):
        raise ValueError

    index = [i for i in range(len(priceList))]  # 0～listの長さ-1 までのインデックス

    problem = pulp.LpProblem("battery_optimization", pulp.LpMinimize)

    # 内生変数

    Pgrid_W = pulp.LpVariable.dicts("Pgrid_W", index, lowBound=0, cat="Continuous")

    Pacdc_in_W = pulp.LpVariable.dicts("Pacdc_in", index, lowBound=0, cat="Continuous")
    Pacdc_out_W = pulp.LpVariable.dicts(
        "Pacdc_out",
        index,
        lowBound=0,
        upBound=ACDC_PWR_W,
        cat="Continuous",
    )

    Pbat_W = pulp.LpVariable.dicts("Pbat", index, cat="Continuous")

    Pinv_in_W = pulp.LpVariable.dicts("Pinv_in", index, lowBound=0, cat="Continuous")
    Pinv_out_W = pulp.LpVariable.dicts("Pinv_out", index, lowBound=0, cat="Continuous")

    Pgrid_load_W = pulp.LpVariable.dicts(
        "Pgrid_load", index, lowBound=0, cat="Continuous"
    )

    SOCbat_Wh = pulp.LpVariable.dicts(
        "SOCbat",
        index,
        lowBound=0,
        upBound=BATT_CAPACITY_WH,
        cat="Continuous",
    )

    # 目的関数：電気代の合計
    problem += pulp.lpSum(0.001 * Pgrid_W[t] * 30 / 60 * priceList[t] for t in index)

    # 制約条件
    for t in index:
        # 電力の出入りに関する等式
        problem += Pgrid_W[t] == Pacdc_in_W[t] + Pgrid_load_W[t]
        problem += Pgrid_load_W[t] + Pinv_out_W[t] == acDemandList[t]
        problem += Pacdc_out_W[t] == Pbat_W[t] + Pinv_in_W[t] + dcDemandList[t]

        # 変換効率に関する不等式
        problem += Pacdc_out_W[t] <= Pacdc_in_W[t] * EFF_ACDC
        problem += Pinv_out_W[t] <= Pinv_in_W[t] * EFF_INV

        # バッテリーの上下限SOC制約
        problem += SOCbat_Wh[t] >= BATT_CAPACITY_WH * MIN_SOCRATE
        problem += SOCbat_Wh[t] <= BATT_CAPACITY_WH * MAX_SOCRATE

        # バッテリーのSOC変化に関する等式（SOCbat_0 は、date日0:00時点でのSOCを表すと定義する）
        if t != 0:  # 現在(t)のSOCは、ひとつ前のコマ(t-1)のSOCに、そのコマ(t-1)で行われた充放電を加えたものに等しい
            problem += SOCbat_Wh[t] == SOCbat_Wh[t - 1] + Pbat_W[t - 1] * 30 / 60

    # バッテリーのSOC初期条件[Wh]
    problem += SOCbat_Wh[0] == initSoc * BATT_CAPACITY_WH

    # バッテリーのSOC終端条件[Wh]
    # 23:30のSOC[Wh] + 23:30～24:00の間に充電する電力[Wh] = 24:00のSOC[kWh] が初期SOCと一致
    lastIndex = index[-1]
    problem += (
        SOCbat_Wh[lastIndex] + Pbat_W[lastIndex] * 30 / 60 == initSoc * BATT_CAPACITY_WH
    )

    # 解く
    status = problem.solve(pulp.PULP_CBC_CMD(msg=False))
    print(pulp.LpStatus[status], problem.objective.value())

    # ACDCとINVの電力とSOCを返す
    acdcPowerList = [Pacdc_out_W[t].value() for t in index]
    invPowerList = [Pinv_out_W[t].value() for t in index]
    socList = [SOCbat_Wh[t].value() / BATT_CAPACITY_WH for t in index]

    return (acdcPowerList, invPowerList, socList)


def convertToBinary(powerList: list[float]) -> list[float]:
    """
    電力の値が正なら`1`, 0なら`0`に変換する。
    例: [0, 150, 2, 0] -> [0, 1, 1, 0]
    """
    return [1 if p > 0 else 0 for p in powerList]


def modifyConsecutivePrice(price: list[float]) -> list[float]:
    """
    同一価格が複数回出現したとき、後につづくものを少し大きくして、連続を避ける
    こうすると、同一価格が続くときなるべく先に電池を充電しようとするので、充電電力のチャタリングが減る
    入出力の例: [5, 5, 5, 6, 7, 5] -> [5, 5.0001, 5.0002, 6, 7, 5.0003]
    5が100回以上出てくると100個目が5.01になって、元々の価格と大小関係が逆転してしまうが、
    2日分(96コマ)を計算する想定なので、流石に100回出てくることはないと考える
    """

    modifiedPrice = price

    for i in range(len(price)):
        increment = 0.0
        for j in range(i + 1, len(price)):
            if modifiedPrice[i] == modifiedPrice[j]:
                increment += 0.0001
                modifiedPrice[j] += increment

    return modifiedPrice


def do(
    initSoc: float,
    priceList: list[float],
    dcDemandList: list[float],
    acDemandList: list[float],
) -> tuple[list[int]]:
    modifiedPriceList = modifyConsecutivePrice(priceList)
    acdcPowerList, invPowerList, socList = lpSolve(
        initSoc, modifiedPriceList, dcDemandList, acDemandList
    )
    return (
        convertToBinary(acdcPowerList),
        convertToBinary(invPowerList),
        list(map(lambda x: round(1000 * x), socList)),  # SOC を千分率にする
    )
