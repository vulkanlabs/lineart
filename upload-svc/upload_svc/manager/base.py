from abc import ABC, abstractmethod

import pandas as pd


class FileManager(ABC):
    @abstractmethod
    def publish(self, project_id: str, data: pd.DataFrame) -> str:
        pass

    @abstractmethod
    def delete(self, project_id: str, file_path: str) -> None:
        pass

    @abstractmethod
    def get(self, project_id: str, file_path: str) -> pd.DataFrame:
        pass
