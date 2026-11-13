# AGENTS.md

Always read the README at the beginning of the session.

## Environment

`devenv` is used to manage the environment, and project "tasks".
`devenv shell` is already active, there's no need for `devenv shell {command}`.
List tasks: `devenv --no-tui --quiet tasks list`
Run a task: `devenv --no-tui --quiet tasks run publish:clean 2>&1 >/dev/null`

## Coding

Never use recursion.

### Code style guidelines

`black` formats, and it runs automatically. Do not run it.

### Validation

Every public interface implementation should validate the inputs using
assertions as a sort of sanity check. The assertion message must
explain the problem, and show the incorrect value.
This validation must be first in the function, as a separate paragraph.
Never validate types with code.

### Type Annotations

Since Python 2.7 is supported, no annotations.

## Testing

- `unittest` is the testing framework.
- List possible tests: `devenv --no-tui --quiet tasks list | rg test:`
- Run tests for a given Python version:
  `devenv --no-tui --quiet tasks run test:py312`
- Run tests, linters, and formatters for all supported Python versions:
  
      devenv --no-tui test 2>&1 | rg -v ' in \d| ignoring ' ; \
      echo EXITS:${PIPESTATUS[0]}
  
  (Do not truncate output)

### Efficiency

1. Baseline: all tests for all versions once at start to capture
   pre-existing state.
2. Iterate fast: single interpreter, `test:py313`; single failure → that one `unittest`
   in isolation.
3. Verify: all tests for all versions at the end to double-check.

### Tests

Organize tests into 3 paragraphs: setup, execution, assertions.
Assign the type being tested to variable `subject`.
Name tests using BDD-like style. E.g.
`test_when_{scenario}_then_it_{expected outcome}`.

## Documentation

### Docstrings

Do not add redundant information. E.g. if a function has type
annotations, do not document the same information.
Type annotations are better than documentation, when containing the
same info.
