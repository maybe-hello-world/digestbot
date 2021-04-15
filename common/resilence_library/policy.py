from abc import abstractmethod, ABC
from typing import Callable, TypeVar

T = TypeVar("T")


class Policy(ABC):
    @abstractmethod
    def execute(self, function: Callable[[], T]) -> T:
        """
        Accepts lambda function and execute it with pre-defined policy parameters
        Example: p.execute(lambda: api.call(1, 2))

        :param function: lambda function to be executed
        :return: function result
        """
        raise NotImplementedError
