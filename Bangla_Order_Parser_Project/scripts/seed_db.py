from app.database import SessionLocal, init_db
from app.services.inventory import seed_inventory


if __name__ == "__main__":
    init_db()
    with SessionLocal() as db:
        created = seed_inventory(db)
    print(f"Seeded {created} product(s).")
