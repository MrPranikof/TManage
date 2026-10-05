from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt

ph = PasswordHasher()
SECRET = "mPqbOaBz2geFVV3IubS2i67aG0vNd0Fr98s9qessnHWkvffW-MlzuRwW-9t1KdWBNpI9X367UtV5fU1q0S2x_A"
users = {}

def create_user(login: str, first_name: str, last_name: str, password: str, user_role = "user", banned = False):
    if users.get(login) is None:
        users[login] = {"first_name": first_name, "last_name": last_name, "password_hash": ph.hash(password), "user_role": user_role, "banned": banned}
        return "success"
    else:
        print("Такой пользователь уже существует.")
        return None

def login_user(login: str, password: str):
    if users.get(login):
        try:
            user = users[login]
            ph.verify(user["password_hash"], password)
            if user["banned"]:
                print("Доступ запрещен!")
            else:
                print("Вы успешно вошли.")
                return login
        except VerifyMismatchError:
            print("Логин или пароль неверный.")
            return None
    else:
        print("Логин или пароль неверный.")

def create_access_token(login: str):
    payload = {"sub": login, "exp": datetime.now(timezone.utc) + timedelta(minutes=15)}
    return jwt.encode(payload, SECRET, algorithm="HS256")

def decode_access_token(token):
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

if __name__ == "__main__":
    create_user("mrpranik", "Vahan", "Hovannisyan", "pas123")
    print(users)
    login_user(login="mrpranik", password="pas123")
    print(decode_access_token(create_access_token(login="mrpranik")))
