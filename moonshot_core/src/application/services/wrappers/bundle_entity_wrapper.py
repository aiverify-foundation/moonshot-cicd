from domain.entities.test_bundle_entity import TestBundleEntity

class TestBundleEntityWrapper:
    """
    Wrapper class for TestBundleEntity that provides additional functionality for repository operations.
    
    This wrapper extends the TestBundleEntity with repository-specific logic, particularly
    maintaining a list of test IDs for easier lookup and management in repository operations.
    It delegates most operations to the wrapped entity while providing additional metadata.
    """
    
    def __init__(self, bundle_entity: TestBundleEntity = None, name: str = "", tests: list = None, description: str = "", category: str = "", id: str = ""):
        if bundle_entity:
            self.bundle_entity = bundle_entity
        else:
            self.bundle_entity = TestBundleEntity(
                name=name,
                tests=tests or [],
                description=description,
                category=category,
                id=id
            )
        # Store test names for repository logic
        self.test_ids: list[str] = [test.name for test in (tests or [])]

    def get_bundle_entity(self) -> TestBundleEntity:
        return self.bundle_entity
    
    # Delegate properties to the wrapped entity
    @property
    def name(self) -> str:
        return self.bundle_entity.name
    
    @property
    def description(self) -> str:
        return self.bundle_entity.description
    
    @property
    def tests(self):
        return self.bundle_entity.tests
    
    @property
    def category(self) -> str:
        return self.bundle_entity.category
    
    @property
    def id(self) -> str:
        return self.bundle_entity.id
    
    @name.setter
    def name(self, value: str):
        self.bundle_entity.name = value

    @description.setter  
    def description(self, value: str):
        self.bundle_entity.description = value

    @tests.setter
    def tests(self, value):
        self.bundle_entity.tests = value

    @category.setter
    def category(self, value: str):
        self.bundle_entity.category = value

    @id.setter
    def id(self, value: str):
        self.bundle_entity.id = value

    def get_prompt_count(self) -> int:
        return self.bundle_entity.get_prompt_count()