"""High-level helper that wires a LogPipeline to a LogRouter."""

from typing import Optional
from logslice.pipeline import LogPipeline
from logslice.router import LogRouter


class LogDispatcher:
    """Combines a pipeline with a router for a single-call workflow.

    Example usage::

        dispatcher = LogDispatcher("app.log")
        dispatcher.router.add_rule("errors", RegexFilter("error", field="level"))
        result = dispatcher.run()
        print(result.bucket("errors"))
    """

    def __init__(
        self,
        path: str,
        router: Optional[LogRouter] = None,
        pipeline: Optional[LogPipeline] = None,
    ) -> None:
        self._path = path
        self.router = router or LogRouter()
        self.pipeline = pipeline or LogPipeline(path)

    def run(self) -> LogRouter:
        """Stream the pipeline and route every entry; return the router."""
        for entry in self.pipeline.stream():
            self.router.route(entry)
        return self.router

    def bucket_counts(self) -> dict:
        """Return a mapping of bucket name -> entry count after run()."""
        return {name: len(entries) for name, entries in self.router.buckets.items()}
