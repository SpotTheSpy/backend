class Parameters:
    MIN_PLAYER_AMOUNT: int = 3
    MAX_PLAYER_AMOUNT: int = 8
    GUARANTEED_UNIQUE_WORDS_COUNT = 30

    TELEGRAM_BOT_START_URL: str = "https://t.me/SpotTheSpyBot?start={payload}"
    DEFAULT_REDIS_KEY: str = "spotthespy"
