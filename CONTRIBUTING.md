# Contributing to SMOL

Thank you for considering contributing to SMOL! We welcome contributions of all kinds.

## Ways to Contribute

### Report Bugs
Found a bug? Please [open an issue](https://github.com/leotrs/smol/issues) with:
- A clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version)

### Suggest Features
Have an idea? [Open an issue](https://github.com/leotrs/smol/issues) describing:
- The feature you'd like to see
- Why it would be useful
- How it might work

### Submit Code

1. **Fork the repository** and create a branch from `main`
2. **Make your changes**:
   - Follow existing code style (we use `ruff` for linting)
   - Add tests for new functionality
   - Update documentation as needed
3. **Test your changes**:
   ```bash
   just test           # Run all tests
   just test-cov       # Run tests with coverage
   ```
4. **Submit a pull request**:
   - Describe what the PR does
   - Reference any related issues
   - Ensure CI passes

### Improve Documentation
Documentation improvements are always welcome:
- Fix typos or unclear explanations
- Add examples
- Improve API documentation
- Expand the glossary

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/smol.git
cd smol

# Install dependencies
uv sync

# Set up database
createdb smol
psql smol < sql/schema.sql

# Generate some graphs for testing
just generate 1 5  # Generate graphs n=1 to n=5

# Run tests
just test
```

## Code Style

- Use `ruff` for linting: `uv run ruff check .`
- Follow existing patterns in the codebase
- Write clear, descriptive variable and function names
- Add docstrings for public functions
- Keep functions focused and concise

## Testing

- Add tests for new features in `tests/`
- Use pytest markers for database-dependent tests: `@pytest.mark.needs_db`
- Aim for good test coverage of core functionality
- Run tests before submitting: `just test`

## Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Reference issues when applicable (e.g., "Fix #123")

## Questions?

Feel free to [open an issue](https://github.com/leotrs/smol/issues) or contact Leo Torres at leo@leotrs.com

## Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to abide by its terms.
