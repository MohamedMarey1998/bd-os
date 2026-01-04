from pydantic import BaseModel

class Settings(BaseModel):
    secret_key: str = "CHANGE_ME__GENERATE_A_RANDOM_SECRET"
    db_url: str = "sqlite:///./bd_os.db"

settings = Settings()
