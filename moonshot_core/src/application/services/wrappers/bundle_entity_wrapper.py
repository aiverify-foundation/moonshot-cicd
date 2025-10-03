from domain.entities.bundle_entity import BundleEntity

class BundleEntityWrapper:
    def __init__(self, bundle_entity: BundleEntity = None, name: str = "", tests: list = None, description: str = ""):
        if bundle_entity:
            self.bundle_entity = bundle_entity
        else:
            self.bundle_entity = BundleEntity(
                name=name,
                tests=tests or [],
                description=description
            )
        # Store test names for repository logic
        self.test_names: list[str] = [test.name for test in (tests or [])]

    def get_bundle_entity(self) -> BundleEntity:
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
    
    @name.setter
    def name(self, value: str):
        self.bundle_entity.name = value

    @description.setter  
    def description(self, value: str):
        self.bundle_entity.description = value

    @tests.setter
    def tests(self, value):
        self.bundle_entity.tests = value