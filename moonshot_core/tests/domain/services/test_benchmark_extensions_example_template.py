"""Static checks for the committed benchmark-extensions.example template."""

import json
from pathlib import Path

import yaml

_EXAMPLE_ROOT = (
    Path(__file__).resolve().parents[3] / "benchmark-extensions.example"
)


def test_example_template_paths_exist():
    assert (_EXAMPLE_ROOT / "README.md").is_file()
    assert (_EXAMPLE_ROOT / "moonshot_config.yaml").is_file()
    assert (_EXAMPLE_ROOT / "test_configs/shared.yaml").is_file()
    assert (_EXAMPLE_ROOT / "datasets/extension_example_dataset.json").is_file()
    assert (
        _EXAMPLE_ROOT / "adapters/metric/extension_example_metric_adapter.py"
    ).is_file()


def test_example_shared_yaml_references_example_ids():
    with open(_EXAMPLE_ROOT / "test_configs/shared.yaml", encoding="utf-8") as f:
        shared = yaml.safe_load(f)
    bundle = shared["extension-example-bundle"]
    assert bundle["name"] == "Extension Example"
    test = bundle["tests"][0]
    assert test["dataset"] == "extension_example_dataset"
    assert test["metric"]["name"] == "extension_example_metric_adapter"


def test_example_moonshot_config_declares_example_metric():
    with open(_EXAMPLE_ROOT / "moonshot_config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    names = [m["name"] for m in config["metrics"]]
    assert names == ["extension_example_metric_adapter"]


def test_example_dataset_json_shape():
    path = _EXAMPLE_ROOT / "datasets/extension_example_dataset.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["examples"]) == 2
    for ex in data["examples"]:
        assert "input" in ex and "target" in ex
