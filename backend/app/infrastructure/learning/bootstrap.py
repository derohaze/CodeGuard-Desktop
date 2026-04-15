from app.infrastructure.learning.benchmark.benchmark import LearningBenchmarkService
from app.infrastructure.learning.storage.repository import LearningArchiveMongoRepository


async def ensure_learning_bootstrap() -> None:
    repository = LearningArchiveMongoRepository()
    benchmark_service = LearningBenchmarkService(repository)
    await benchmark_service.ensure_benchmark_skeleton()
