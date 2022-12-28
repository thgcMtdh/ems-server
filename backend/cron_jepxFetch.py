import datetime
import requests
from pydantic import BaseSettings


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

if __name__ == "__main__":

    # 環境変数の読み込み。存在しない場合はValidationErrorを出して終了する
    class Env(BaseSettings):
        DATA_DIR: str
        class Config:
            env_file = '.env'

    env = Env()
    fetchSpot(env.DATA_DIR)
    