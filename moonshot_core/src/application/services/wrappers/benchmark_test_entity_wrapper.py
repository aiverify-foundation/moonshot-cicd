from domain.entities.benchmark_test_entity import BenchmarkTestEntity

class BenchmarkTestEntityWrapper:
    def __init__(self, benchmark_test_entity: BenchmarkTestEntity = None):
        self.benchmark_test_entity = benchmark_test_entity or BenchmarkTestEntity()
        self.dataset_name: str = ""

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
