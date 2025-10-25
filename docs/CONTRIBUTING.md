# Contributing to ELESS

We welcome contributions to ELESS! This guide outlines how to get involved.

## How to Contribute

### 1. Fork the Repository

Fork the project on GitHub and clone your fork:

```bash
git clone https://github.com/YOUR_USERNAME/eless.git
cd eless
```

### 2. Set Up Development Environment

Install in development mode with all dependencies:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[full,dev]"
```

### 3. Make Your Changes

Create a feature branch:

```bash
git checkout -b feature/your-feature-name
```

Follow coding standards:
- Use Black for formatting: `black src/`
- Lint with Flake8: `flake8 src/`
- Type check with MyPy: `mypy src/`
- Write tests for new features

### 4. Test Thoroughly

Run the test suite:

```bash
pytest tests/ -v
```

Ensure all tests pass and add new tests if needed.

### 5. Commit Your Changes

Use clear commit messages:

```bash
git add .
git commit -m "feat: add support for new parser"
```

Follow the commit message format: `<type>: <description>`

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

### 6. Push and Create Pull Request

Push to your fork:

```bash
git push origin feature/your-feature-name
```

Create a pull request on GitHub with:
- Clear description of changes
- Link to related issues
- Test results
- Updated documentation if applicable

## Contribution Guidelines

### Code Style

- Follow PEP 8 with Black formatting (88 characters line length)
- Use Google-style docstrings
- Group imports: stdlib, third-party, local
- Use structured logging

### Testing

- Write unit tests for new components
- Include integration tests for interactions
- Add end-to-end tests for workflows
- Use pytest fixtures for setup

### Documentation

- Update docs for new features
- Include examples in EXAMPLES_AND_USAGE.md
- Update API_REFERENCE.md for new APIs

### Pull Request Template

Use this template for PRs:

```
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Self-reviewed code
```

## Reporting Issues

- Use the [GitHub Issue Tracker](https://github.com/Bandalaro/eless/issues)
- Include output of `eless doctor`
- Provide steps to reproduce
- Attach error logs

## Community

- Be respectful and inclusive
- Ask questions in issues or discussions
- Share your use cases

## License

By contributing, you agree that your contributions will be licensed under the same MIT License as the original project.

**Contributing Version**: 1.0  
**Last Updated**: 2025-10-25