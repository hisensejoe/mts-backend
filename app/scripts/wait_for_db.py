import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)

    for attempt in range(1, 16):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            print("Database connection established.")
            return
        except OperationalError:
            print(f"Database not ready yet. Attempt {attempt}/15.")
            time.sleep(2)

    raise SystemExit("Database was not ready in time.")


if __name__ == "__main__":
    main()
