class SnapshotNotFound(FileNotFoundError):
    def __init__(self, dataset: str, table: str) -> None:
        self.dataset = dataset
        self.table = table
        super().__init__(f"Snapshot data is unavailable for dataset {dataset}, table {table}")


class SchemaMismatch(ValueError):
    def __init__(self, dataset: str, table: str, detail: str) -> None:
        self.dataset = dataset
        self.table = table
        super().__init__(f"Snapshot schema mismatch for dataset {dataset}, table {table}: {detail}")


class IntegrityError(ValueError):
    def __init__(self, dataset: str, table: str, detail: str) -> None:
        self.dataset = dataset
        self.table = table
        super().__init__(
            f"Snapshot integrity failure for dataset {dataset}, table {table}: {detail}"
        )


class SourceUnavailable(RuntimeError):
    def __init__(self, dataset: str, table: str) -> None:
        self.dataset = dataset
        self.table = table
        super().__init__(f"Source unavailable for dataset {dataset}, table {table}")
