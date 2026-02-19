from __future__ import annotations

from di_es_dashboard_api.db import engine
from di_es_dashboard_api.models import Base


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("DB schema created/verified.")


if __name__ == "__main__":
    main()

