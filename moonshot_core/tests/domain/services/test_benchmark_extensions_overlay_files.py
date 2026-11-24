"""Static checks for the committed benchmark-extensions.example overlay files."""

import json
from pathlib import Path

import yaml

_OVERLAY_ROOT = Path(__file__).resolve().parents[3] / "benchmark-extensions.example"


def test_overlay_paths_exist():
    assert (_OVERLAY_ROOT / "README.md").is_file()
    assert (_OVERLAY_ROOT / "moonshot_config.yaml").is_file()
    assert (_OVERLAY_ROOT / "test_configs/shared.yaml").is_file()
    assert (_OVERLAY_ROOT / "datasets/custom_extension_sample.json").is_file()
    assert (
        _OVERLAY_ROOT / "adapters/metric/extension_example_metric_adapter.py"
    ).is_file()
    assert (
        _OVERLAY_ROOT / "adapters/connector/benchmark_extension_openai_adapter.py"
    ).is_file()


def test_overlay_shared_yaml_references_sample_ids():
    with open(_OVERLAY_ROOT / "test_configs/shared.yaml", encoding="utf-8") as f:
        shared = yaml.safe_load(f)
    bundle = shared["custom-extension-sample"]
    assert bundle["name"] == "Custom Extension Sample"
    test = bundle["tests"][0]
    assert test["dataset"] == "custom_extension_sample"
    assert test["metric"]["name"] == "accuracy_adapter"


def test_overlay_moonshot_config_parses():
    with open(_OVERLAY_ROOT / "moonshot_config.yaml", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    assert isinstance(config, dict)
    connectors = config["connectors_configurations"]
    assert connectors[0]["id"] == "benchmark-extension-openai"
    assert connectors[0]["connector_adapter"] == "benchmark_extension_openai_adapter"


def test_overlay_dataset_json_shape():
    path = _OVERLAY_ROOT / "datasets/custom_extension_sample.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["examples"]) == 1
    for ex in data["examples"]:
        assert "input" in ex and "target" in ex
