from typing.io import BinaryIO
from pathlib import Path


class BinaryAsset:
    def for_writing(self) -> BinaryIO:
        raise NotImplementedError()

    def for_reading(self) -> BinaryIO:
        raise NotImplementedError()


class BaseStore:
    """
    The interface to saving data from a running QM job
    """

    def __init__(self) -> None:
        super().__init__()

    def job_named_result(self, job_id: str, name: str) -> BinaryAsset:
        raise NotImplementedError()

    def all_job_results(self, job_id: str) -> BinaryAsset:
        raise NotImplementedError()


class FileBinaryAsset(BinaryAsset):
    def __init__(self, path: Path) -> None:
        super().__init__()
        self._path = path

    def for_writing(self) -> BinaryIO:
        return self._path.open("wb")

    def for_reading(self) -> BinaryIO:
        return self._path.open("rb")


class SimpleFileStore(BaseStore):
    def __init__(self, root: str = '.') -> None:
        super().__init__()
        self._root = Path(root).absolute()

    def _job_path(self, job_id: str):
        path = Path(f"{self._root}/{job_id}")
        path.mkdir(parents=True, exist_ok=True)
        return path

    def job_named_result(self, job_id: str, name: str) -> BinaryAsset:
        return FileBinaryAsset(self._job_path(job_id).joinpath(f"result_{name}.npy"))

    def all_job_results(self, job_id: str) -> BinaryAsset:
        return FileBinaryAsset(self._job_path(job_id).joinpath(f"results.npz"))
