from __future__ import annotations

from collections.abc import Mapping
from dataclasses import MISSING, asdict, dataclass, field, fields, is_dataclass, make_dataclass
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Final,
    Self,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

from litestar.params import Parameter

from backend.app.common.tools import convert_to


if TYPE_CHECKING:
    import _typeshed


def get_keys_from_type(tp: Any) -> frozenset[str]:
    if is_dataclass(tp):
        return frozenset(f.name for f in fields(tp))

    return frozenset(tp.__annotations__.keys())


def _filter_none(values: list[tuple[str, Any]]) -> dict[str, Any]:
    return {k: v for k, v in values if v is not None}


class ToOwned[T: Mapping[str, Any] | _typeshed.DataclassInstance]:
    """
    Base mixin for auto-dataclass query wrappers.
    If a subclass is not a dataclass, `__init_subclass__`
    wraps it with `@dataclass(frozen=True, ...)`.
    `.to_owned()` converts the query instance back to the `owned` type (Mapping or dataclass).
    """

    owned: type[T]

    def __init__(self, *args: Any, **kw: Any) -> None: ...

    def __init_subclass__(cls, **kw: Any) -> None:
        if not is_dataclass(cls):
            dataclass(**kw)(cls)

    def to_owned(self) -> T:
        if not TYPE_CHECKING:
            if not issubclass(self.owned, Mapping):
                data = asdict(self)
            else:
                data = asdict(self, dict_factory=_filter_none)
        else:
            data: Mapping[str, Any] = {}

        return convert_to(self.owned, data, strict=False)

    @classmethod
    def from_(cls, owned: type[T]) -> type[Self]:
        return type(cls.__name__, (cls,), {"owned": owned})


def _unwrap_annotated(tp: Any) -> tuple[Any, list[Any]]:
    if get_origin(tp) is Annotated:
        base, *meta = get_args(tp)
        return base, list(meta)
    return tp, []


def _is_optional(tp: Any) -> bool:
    origin = get_origin(tp)
    if origin in (Union, UnionType):
        return type(None) in get_args(tp)
    return False


_DEFAULT = object()
MIN_METADATA_ITEMS: Final[int] = 1
MAX_METADATA_ITEMS: Final[int] = 2


def _parse_metadata[T: Mapping[str, Any] | _typeshed.DataclassInstance](
    metadata: list[Any],
    *,
    field_name: str,
    owner: type[T],
) -> tuple[str | None, Any | object]:
    if not metadata:
        return None, _DEFAULT

    if len(metadata) == MIN_METADATA_ITEMS:
        m = metadata[0]
        if isinstance(m, str):
            return m, _DEFAULT
        else:
            return None, m

    if len(metadata) == MAX_METADATA_ITEMS:
        desc, default = metadata
        if not isinstance(desc, str):
            raise TypeError(
                f"{owner.__name__}.{field_name}: Annotated expects "
                "first meta to be str (description) "
                f"when two metadata are provided, got {type(desc).__name__}",
            )
        return desc, default

    raise TypeError(
        f"{owner.__name__}.{field_name}: Annotated supports at most two metadata items "
        f"(description[, default]); got {len(metadata)}",
    )


def _override_default_meta[T: Mapping[str, Any] | _typeshed.DataclassInstance](
    default_meta: Any,
    param_kwargs: dict[str, Any],
    dc_fields: dict[str, Any],
    key: str,
) -> Any:
    if default_meta is not _DEFAULT:
        param_kwargs["default"] = default_meta
    elif key in dc_fields:
        f = dc_fields[key]
        if f.default != MISSING:
            default_meta = f.default
            param_kwargs["default"] = default_meta
        elif f.default_factory != MISSING:
            raise NotImplementedError(f"default_factory for {key} not supported yet")

    return default_meta


def make_filter_query[T: Mapping[str, Any] | _typeshed.DataclassInstance](
    cls: type[T],
    *required_keys: str,
    **param_overrides: dict[str, Any],
) -> type[ToOwned[T]]:
    """
    Build a dataclass-based "query" wrapper for `cls` (a `TypedDict` or a dataclass),
    suitable for request/URL query parameters. The generated class:

    - is a `@dataclass(slots=True)` that **inherits** from `ToOwned[cls]`;
    - exposes the same fields as `cls`, but each field is annotated with
        `typing.Annotated[..., Parameter(...)]` so Litestar
        can render docs and parse query params;
    - decides whether a field is **required** using one of:
        1) `required_keys` passed to this function,
        2) `cls.__required_keys__` when `cls` is a `TypedDict`,
        3) otherwise: a field is required if its base type is **not** Optional.

    ### How `Annotated` metadata is interpreted

    For a field annotated as `Annotated[BaseType, *meta]` in `cls`:
      - If `meta` has **one** item:
          * if it's a `str` -> treated as the **description**;
          * otherwise -> treated as the **default value**.
      - If `meta` has **two** items:
          * `meta[0]` **must** be `str` (description),
          * `meta[1]` is the **default value**.
        - More than two metadata items are not allowed.

    ### Defaults and Optionality

    - If the field is **not required** and `BaseType` is not Optional, the effective
        type becomes `BaseType | None`.
    - Default value is:
        * for required fields: absent, unless provided via metadata (then used);
        * for optional fields: `None`, unless a default is provided via metadata.

    ### `Parameter(...)` kwargs per field

    Extra per-field `Parameter(...)` settings can be provided via `**param_overrides`:
        - key = field name, value = `dict` of kwargs for `Parameter`.
        - Example: `make_filter_query(UserTD, login={"title": "username"})`.

    The following keys are always set by the factory and can be overridden by you:
        - `description` (auto-derived if not provided),
        - `required` (`True`/`False`).

    ### Conversion back to the owned type

    The resulting class includes `.to_owned() -> T`:
        - If `T` is a `Mapping`, `None` values are **removed** from the resulting dict.
        - If `T` is a dataclass, `asdict(...)` is used (no filtering unless `Mapping`).

    ### Examples

    #### 1) `TypedDict` with optional/required and defaults via `Annotated`
    class UserFilter(TypedDict, total=False):
        # optional, default by metadata (single non-str item)
        is_active: Annotated[bool, True]
        # optional, description only
        login: Annotated[str, "User login"]
        # optional, string default + description (two metadata items)
        email: Annotated[str, "E-mail (optional)", ""]

    # mark `login` as required via the factory argument
    UserFilterQuery = make_filter_query(UserFilter, "login")

    #### 2) `TypedDict` using its own `__required_keys__`
    class ProductFilter(TypedDict):
        sku: str               # required because total=True by default
        name: Annotated[str, "Name filter"]

    ProductFilterQuery = make_filter_query(ProductFilter)

    #### 3) Dataclass as owned type
    @dataclass
    class OrderFilter:
        status: Annotated[str | None, "Order status"] = None
        customer_id: int

    # Optional per-field Parameter overrides (e.g., title)
    OrderFilterQuery = make_filter_query(
        OrderFilter,
        customer_id={"title": "cid"},
    )

    # In a handler:
    # @get('/', dependencies={'q': Provide(make_filter_query(OrderFilter), sync_to_thread=False)})
    # async def endpoint(q: ToOwned[OrderFilter]):
    #     owned = q.to_owned()

    Returns:
        A dynamically created dataclass type named `{cls.__name__}Query` that
        inherits from `ToOwned[cls]`.
    """
    hints = get_type_hints(cls, include_extras=True)

    required: set[str] = set(getattr(cls, "__required_keys__", ()))
    if required_keys:
        required.update(required_keys)

    use_required = hasattr(cls, "__required_keys__") or bool(required_keys)

    dc_fields = {f.name: f for f in fields(cls)} if is_dataclass(cls) else {}
    fields_spec: list[tuple[Any, ...]] = []

    for key, tp in hints.items():
        base_tp, metadata = _unwrap_annotated(tp)
        desc_meta, default_meta = _parse_metadata(metadata, field_name=key, owner=cls)

        is_required = (key in required) if use_required else (not _is_optional(base_tp))

        desc = (
            desc_meta
            if isinstance(desc_meta, str) and desc_meta
            else ("Required `filter`" if is_required else "Optional `filter`")
        )

        eff_tp = base_tp
        if not is_required and not _is_optional(base_tp):
            eff_tp = base_tp | None

        additional = param_overrides.get(key, {})
        if not isinstance(additional, dict):
            raise TypeError("value in `params_overrides` dict should be dict as well")

        param_kwargs = {
            "description": additional.pop("description", desc),
            "required": additional.pop("required", is_required),
        }

        default_meta = _override_default_meta(default_meta, param_kwargs, dc_fields, key)

        ann_type = Annotated[
            eff_tp,  # type: ignore[valid-type]
            Parameter(**{**param_kwargs, **additional}),
        ]

        if is_required:
            if default_meta is not _DEFAULT:
                fields_spec.append((key, ann_type, field(default=default_meta)))
            else:
                fields_spec.append((key, ann_type))
        else:
            default_val = None if default_meta is _DEFAULT else default_meta
            fields_spec.append((key, ann_type, field(default=default_val)))

    out = make_dataclass(
        f"{cls.__name__}Query",
        fields_spec,
        bases=(ToOwned.from_(cls),),
        slots=True,
    )

    return cast(type[ToOwned[T]], out)
