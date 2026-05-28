from app.seed import ensure_seed_admin


def main() -> None:
    user = ensure_seed_admin(sync_password=True)
    print(f"Seed admin ready: {user.email}")


if __name__ == "__main__":
    main()

