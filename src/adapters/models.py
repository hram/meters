from dataclasses import dataclass, field


@dataclass
class Scale:
    """One tariff zone of a meter (day / night / middle or a single value)."""
    id: str           # pesc: str(meter_scale_id), gaz: "day" | "night" | "middle"
    name: str
    value: float | None
    unit: str | None


@dataclass
class Meter:
    service: str      # "pesc" | "gaz"
    account_id: str   # pesc: account_id int, gaz: lspu_id int
    meter_id: str     # pesc: registration, gaz: uuid
    name: str
    scales: list[Scale] = field(default_factory=list)

    # Extra fields kept for building submit-values payloads
    extra: dict = field(default_factory=dict)


@dataclass
class ServiceData:
    service: str      # "pesc" | "gaz"
    label: str        # human-readable: "Вода и электричество" | "Газ"
    account_id: str
    balance_text: str | None
    meters: list[Meter] = field(default_factory=list)
    error: str | None = None
