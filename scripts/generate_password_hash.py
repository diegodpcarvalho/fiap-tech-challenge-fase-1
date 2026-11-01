from getpass import getpass

from garage.infrastructure.security import hash_password


def main() -> None:
    password = getpass("Senha administrativa (minimo de 10 caracteres): ")
    confirmation = getpass("Repita a senha: ")
    if password != confirmation:
        raise SystemExit("As senhas nao coincidem.")
    print(hash_password(password))


if __name__ == "__main__":
    main()
