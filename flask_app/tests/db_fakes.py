class StepDrivenFakeCursor:
    def __init__(self, steps=None):
        self.steps = steps or []
        self.step_index = 0
        self.last_step = None
        self.queries = []
        self.params_list = []
        self.rowcount = 0

    def execute(self, query, params=None):
        normalized = " ".join(query.split())
        self.queries.append(normalized)
        self.params_list.append(params)
        if self.step_index >= len(self.steps):
            raise AssertionError(f"Unexpected execute: {normalized} with params {params}")
        step = self.steps[self.step_index]
        if "expect" in step and step["expect"] not in normalized:
            raise AssertionError(f"Query mismatch. Expected to include: {step['expect']}. Got: {normalized}")
        if "params" in step:
            assert params == step["params"], f"Params mismatch. Expected {step['params']}, got {params}"
        self.rowcount = step.get("rowcount", 0)
        self.last_step = step
        self.step_index += 1

    def fetchone(self):
        if not self.last_step or self.last_step.get("fetch") != "one":
            raise AssertionError("fetchone called without matching 'one' step")
        return self.last_step.get("result")

    def fetchall(self):
        if not self.last_step or self.last_step.get("fetch") != "all":
            raise AssertionError("fetchall called without matching 'all' step")
        return self.last_step.get("result") or []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, steps=None):
        self.cursor_obj = StepDrivenFakeCursor(steps or [])
        self.commit_called = False
        self.commit_count = 0

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.commit_called = True
        self.commit_count += 1
