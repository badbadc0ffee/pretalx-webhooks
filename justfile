set shell := ["bash", "-euo", "pipefail", "-c"]
set quiet
set fallback
set positional-arguments

venv_bin := ".venv/bin"

# Run ruff format
[group('linting')]
format *args=".":
    {{ venv_bin }}/ruff format "$@"

# Run ruff check
[group('linting')]
check *args=".":
    {{ venv_bin }}/ruff check "$@"

# Format Django templates with djangofmt.
[group('linting')]
djangofmt *args="":
    -{{ venv_bin }}/djangofmt {{ args }} .

[group('linting')]
djangofmt-check:
    just djangofmt
    git diff --exit-code -- '*.html' || (echo "HTML templates are not formatted. Run 'just djangofmt' to fix." && exit 1)

# Check that VCS files and the sdist match (CI runs this)
[group('linting')]
check-manifest:
    {{ venv_bin }}/check-manifest

# Run all formatters and linters
[group('linting')]
fmt: (check "--fix") format djangofmt && fmt-done

[private]
fmt-done:
    echo '{{ GREEN }}Formatting complete{{ NORMAL }}'

# Run all code quality checks
[group('linting')]
fmt-check: (format "--check") check djangofmt-check && check-done

[private]
check-done:
    echo '{{ GREEN }}All checks passed{{ NORMAL }}'

# Run tests (installs pretalx if not already present)
[group('tests')]
test *args: ensure-pretalx
    {{ venv_bin }}/pytest "$@"

# Install development dependencies
[group('development')]
install-pretalx:
    python3 -m venv .venv
    {{ venv_bin }}/python -m pip install -e ".[dev]"

# Install a local editable copy of pretalx (for development)
[group('development')]
install-pretalx-local path:
    {{ venv_bin }}/python -m pip install -e "{{ path }}[dev]"

# Ensure pretalx is importable, installing it from git if needed
[private]
ensure-pretalx:
    {{ venv_bin }}/python -c "import pretalx" 2>/dev/null || just install-pretalx

# Generate locale files
[group('development')]
[script('bash')]
localegen: ensure-pretalx
    module=$(find . -maxdepth 1 -type d -name 'pretalx_*' -not -name '*.egg-info' | head -1)
    {{ venv_bin }}/django-admin makemessages --add-location file -i build -i dist -i "*egg*" $(find "$module/locale/" -mindepth 1 -maxdepth 1 -type d -printf "-l %f " 2>/dev/null)

# Compile locale files
[group('development')]
localecompile: ensure-pretalx
    {{ venv_bin }}/django-admin compilemessages
