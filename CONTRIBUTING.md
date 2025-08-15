# Contributing to the Arabic Dictionary Backend

Thank you for considering contributing to this project!  We welcome
bug reports, feature requests and pull requests.  To ensure a smooth
development experience please follow these guidelines.

## Development Setup

1. Fork the repository and clone your fork.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy `config/settings.example.toml` to `config/settings.toml` and
   customise as needed.  Use SQLite during development.

4. Run the test suite:

   ```bash
   pytest
   ```

5. Make your changes on a feature branch.  Write tests for new
   functionality and update the documentation when appropriate.

## Coding Guidelines

* Use Python 3.11+ and follow PEP 8 style guidelines.
* Write docstrings for public functions and classes.
* Keep functions pure where possible; separate business logic from
  I/O.
* When adding new ETL modules, document the source license and
  include a provenance record for each field.
* Update the changelog (`CHANGELOG.md`) with a summary of your
  changes.

## Pull Request Checklist

* [ ] Tests have been added or updated to cover your changes.
* [ ] All tests pass locally (`pytest`).
* [ ] The code builds without errors (`python -m compileall .`).
* [ ] Documentation and examples have been updated.
* [ ] Changelog has been updated.

We appreciate your contributions and look forward to working with you!
