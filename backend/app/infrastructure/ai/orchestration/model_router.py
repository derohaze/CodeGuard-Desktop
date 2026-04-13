class ModelRouter:
    def __init__(
        self,
        *,
        small_model: str,
        large_model: str,
        overflow_model: str | None = None,
        scout_model: str | None = None,
    ) -> None:
        self.small_model = small_model
        self.large_model = large_model
        self.overflow_model = overflow_model
        self.scout_model = scout_model

    def route(self, task_name: str) -> str:
        return self.route_candidates(task_name)[0]

    def route_candidates(self, task_name: str) -> list[str]:
        normalized = task_name.strip().lower()
        depth_tasks = {"explain", "fix_validate", "patch_validate", "final_patch", "verdict", "finding_validate"}
        if normalized in depth_tasks:
            models = [self.large_model]
            if self.overflow_model:
                models.append(self.overflow_model)
            if self.scout_model:
                models.append(self.scout_model)
            return models

        models = [self.small_model]
        if self.overflow_model:
            models.append(self.overflow_model)
        if self.scout_model:
            models.append(self.scout_model)
        return models
