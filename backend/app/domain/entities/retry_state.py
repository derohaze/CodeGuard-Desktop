from dataclasses import dataclass, field


@dataclass(slots=True)
class RetryStateEntity:
    excluded_strategy_ids: list[str] = field(default_factory=list)
    attempted_strategy_ids: list[str] = field(default_factory=list)
    previous_rationales: list[str] = field(default_factory=list)
