from abc import ABC, abstractmethod


class PasswordHasherPort(ABC):
    @abstractmethod
    def hash(self, plain: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verify(self, plain: str, hashed: str) -> bool:
        raise NotImplementedError
