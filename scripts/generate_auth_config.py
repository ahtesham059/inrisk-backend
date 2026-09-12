import getpass
import secrets

from app.auth import hash_password


def main() -> None:
    username = input("Demo username [reviewer]: ").strip() or "reviewer"
    password = getpass.getpass("Demo password: ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")
    print(f"AUTH_USERNAME={username}")
    print(f"AUTH_PASSWORD_HASH={hash_password(password, secrets.token_bytes(16))}")
    print(f"AUTH_TOKEN_SECRET={secrets.token_urlsafe(48)}")
    print("AUTH_TOKEN_TTL_MINUTES=120")
    print("MAX_STORED_FILES=100")


if __name__ == "__main__":
    main()
