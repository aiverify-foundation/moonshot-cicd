"""Tests for the structured adapter-not-found error detail."""

from application.dto.adapter_not_found_dto import (
    AdapterNotFoundDetailDTO,
    adapter_not_found_detail,
    find_adapter_not_found,
)
from domain.services.benchmark_extensions import AdapterNotFoundError
from domain.services.enums.module_types import ModuleTypes


def _missing_adapter() -> AdapterNotFoundError:
    return AdapterNotFoundError(
        "metric adapter 'gone' not found: no file at /srv/app/src/adapters/metric/gone.py.",
        module_type=ModuleTypes.METRIC,
        adapter_name="gone",
    )


def test_detail_for_adapter_not_found_error_has_no_path():
    detail = adapter_not_found_detail(_missing_adapter())

    assert detail == {
        "code": "adapter_not_found",
        "message": "The metric adapter 'gone' is not available on the server.",
        "adapter_type": "metric",
        "adapter_name": "gone",
    }
    assert "/srv" not in str(detail)


def test_detail_follows_the_cause_chain():
    wrapper = ValueError("export failed")
    wrapper.__cause__ = _missing_adapter()

    assert adapter_not_found_detail(wrapper)["adapter_name"] == "gone"
    assert find_adapter_not_found(wrapper) is wrapper.__cause__


def test_detail_is_none_for_other_errors():
    assert adapter_not_found_detail(ValueError("nothing to do with adapters")) is None


def test_detail_uses_placeholders_when_adapter_fields_are_missing():
    detail = adapter_not_found_detail(AdapterNotFoundError("gone"))

    assert detail["adapter_type"] == "unknown"
    assert detail["adapter_name"] == "unknown"


def test_connector_adapter_type_is_reported():
    error = AdapterNotFoundError(
        "x", module_type=ModuleTypes.CONNECTOR, adapter_name="my_connector"
    )

    assert adapter_not_found_detail(error)["adapter_type"] == "connector"


def test_dto_code_is_fixed():
    dto = AdapterNotFoundDetailDTO(message="m", adapter_type="metric", adapter_name="n")

    assert dto.code == "adapter_not_found"


def test_cyclic_cause_chain_terminates():
    first = ValueError("a")
    second = ValueError("b")
    first.__cause__ = second
    second.__cause__ = first

    assert find_adapter_not_found(first) is None
