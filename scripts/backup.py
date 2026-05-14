from pathlib import Path
from shutil import make_archive


def main() -> None:
    data_dir = Path(".data")
    backup_dir = Path(".backups")
    backup_dir.mkdir(exist_ok=True)
    archive = make_archive(str(backup_dir / "context-engine-data"), "zip", data_dir)
    print(f"Backup written: {archive}")


if __name__ == "__main__":
    main()

