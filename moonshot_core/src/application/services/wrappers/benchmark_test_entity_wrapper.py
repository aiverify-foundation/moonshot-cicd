from domain.entities.benchmark_test_entity import BenchmarkTestEntity

class BenchmarkTestEntityWrapper:
    """
    Wrapper class for BenchmarkTestEntity that provides additional functionality for repository operations.
    
    This wrapper extends the BenchmarkTestEntity with repository-specific logic, particularly
    maintaining a dataset_id field for easier lookup and management in repository operations.
    It delegates most operations to the wrapped entity while providing additional metadata.
    """
    
    def __init__(self, benchmark_test_entity: BenchmarkTestEntity = None):
        if benchmark_test_entity:
            self.benchmark_test_entity = benchmark_test_entity
        else:
            # Create a default entity with required fields
            self.benchmark_test_entity = BenchmarkTestEntity(
                id="",
                name="",
                metric={}
            )
        self.dataset_id: str = ""

    def get_benchmark_test_entity(self) -> BenchmarkTestEntity:
        return self.benchmark_test_entity
    
    # Delegate properties to the wrapped entity
    @property
    def name(self) -> str:
        return self.benchmark_test_entity.name
    
    @property
    def dataset(self):
        return self.benchmark_test_entity.dataset
    
    @property
    def metric(self) -> dict:
        return self.benchmark_test_entity.metric
    
    @property
    def description(self) -> str:
        return self.benchmark_test_entity.description
    
    @property
    def id(self) -> str:
        return self.benchmark_test_entity.id
    
    @name.setter
    def name(self, value: str):
        self.benchmark_test_entity.name = value

    @dataset.setter  
    def dataset(self, value):
        self.benchmark_test_entity.dataset = value

    @metric.setter
    def metric(self, value: dict):
        self.benchmark_test_entity.metric = value

    @description.setter
    def description(self, value: str):
        self.benchmark_test_entity.description = value

    @id.setter
    def id(self, value: str):
        self.benchmark_test_entity.id = value

    def get_prompt_count(self) -> int:
        return self.benchmark_test_entity.get_prompt_count()
