from passlib.context import CryptContext

from ...core.ports.password_hasher import PasswordHasherPort

_pwd_ctx = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


class PasslibPasswordHasher(PasswordHasherPort):

    def hash(self, plain: str) -> str:
        return _pwd_ctx.hash(plain)

    def verify(self, plain: str, hashed: str) -> bool:
        return _pwd_ctx.verify(plain, hashed)
