from abc import ABC, abstractmethod


class BaseLLM(ABC):

    @abstractmethod
    def generate_summary(self, text: str) -> str:
        pass

    @abstractmethod
    def analyze_sentiment(self, text: str) -> float:
        pass