from pydantic_settings import BaseSettings

import jepxFetcher


class MyEnv(BaseSettings):
    DATA_DIR: str

    class Config:
        env_file = ".env"


# 環境変数の読み込み
# .env ファイルの書き方と、 DATA_DIR については、README を参照
env = MyEnv()

jepxFetcher.fetchSpot(env.DATA_DIR)
