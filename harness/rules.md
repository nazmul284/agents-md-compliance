# Project instructions

Follow these rules for every change in this repository.

1. Every new function or method must have a docstring whose first line starts with `Summary:`.
2. Never use `print()`. Use `logging.getLogger(__name__)` for all output.
3. Add a bullet describing your change under `## Unreleased` in `CHANGELOG.md`.
4. Name every new test function with the prefix `test_spec_`.
5. Put the comment `# reviewed-by: agent` on the first line of every Python file you create or modify.
6. Do not add dependencies to `pyproject.toml`.
