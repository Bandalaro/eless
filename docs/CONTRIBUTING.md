# Contributing to ELESS

Thank you for your interest in contributing to ELESS! This document provides guidelines and information for contributors.

## 🚀 Quick Start

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/eless-team/eless.git
   cd eless
   ```

2. **Set up development environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .[dev]     # Install in development mode with dev dependencies
   ```

3. **Install optional dependencies for testing**
   ```bash
   pip install -e .[full]    # Install all optional features
   ```

4. **Run the test suite**
   ```bash
   pytest tests/
   ```

5. **Run code formatting and linting**
   ```bash
   black src/ tests/
   flake8 src/ tests/
   mypy src/
   ```

## 🧪 Testing Your Changes

### Basic Functionality Test
```bash
# Test the configuration wizard
python -m src.cli config wizard

# Test auto-detection
python -m src.cli config auto-detect

# Test with a sample document
echo "This is a test document." > test.txt
python -m src.cli process test.txt --databases chroma

# Test monitoring
python -m src.cli monitor --duration 10
```

### Test Different System Configurations
```bash
# Test minimal configuration
python -m src.cli config init minimal -o minimal_config.yaml
python -m src.cli --config minimal_config.yaml process test.txt

# Test cache management
python -m src.cli cache --stats
python -m src.cli cache --cleanup
```

## 📝 Code Style and Standards

### Python Code Style
- **Formatting**: Use [Black](https://black.readthedocs.io/) with line length 88
- **Import sorting**: Use [isort](https://pycqa.github.io/isort/)
- **Linting**: Follow [flake8](https://flake8.pycqa.org/) recommendations
- **Type hints**: Use type hints for all public functions and methods

### Code Organization
- **Modules**: Keep modules focused on a single responsibility
- **Interfaces**: Define abstract base classes for extensible components
- **Configuration**: Use configuration-driven behavior over hardcoded logic
- **Error handling**: Provide informative error messages with suggested solutions

### Example Code Style
```python
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class ExampleComponent:
    """
    Example component following ELESS coding standards.
    
    Args:
        config: Configuration dictionary
        optional_param: Optional parameter with default
    """
    
    def __init__(self, config: Dict[str, Any], optional_param: Optional[str] = None):
        self.config = config
        self.optional_param = optional_param
        logger.info("ExampleComponent initialized")
    
    def process_data(self, data: List[str]) -> List[Dict[str, Any]]:
        """Process input data and return structured results."""
        try:
            results = []
            for item in data:
                result = self._process_item(item)
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Failed to process data: {e}", exc_info=True)
            raise
    
    def _process_item(self, item: str) -> Dict[str, Any]:
        """Private method for processing individual items."""
        return {"text": item, "length": len(item)}
```

## 🔧 Development Areas

### High-Impact Contributions

1. **Plugin Architecture**
   - Implement abstract interfaces for parsers, chunkers, embedders
   - Create plugin loading and registration system
   - Add support for user-defined plugins

2. **Additional Embedding Providers**
   - OpenAI embeddings integration
   - Cohere embeddings support
   - Azure OpenAI compatibility
   - Local model support (Ollama, etc.)

3. **Advanced Chunking Strategies**
   - Semantic chunking based on sentence embeddings
   - Token-based chunking for transformer models
   - Custom delimiter support
   - Hierarchical chunking strategies

4. **Enhanced Database Support**
   - Additional vector database connectors
   - Connection pooling and retry logic
   - Transaction support where applicable
   - Database-specific optimizations

5. **Performance Improvements**
   - Streaming processing for large files
   - Parallel processing support
   - GPU utilization optimization
   - Memory usage optimization

### Medium-Impact Contributions

1. **User Experience Enhancements**
   - Progress bars and better feedback
   - Interactive configuration validation
   - Better error messages and suggestions
   - Configuration templates and examples

2. **Monitoring and Observability**
   - Metrics collection and export
   - Integration with monitoring systems
   - Performance profiling tools
   - Health check endpoints

3. **Documentation**
   - API documentation
   - Tutorial content
   - Architecture diagrams
   - Best practices guides

### Getting Started Areas

1. **Bug fixes and small improvements**
2. **Test coverage improvements**
3. **Documentation updates**
4. **Example configurations and scripts**
5. **Performance benchmarking**

## 🐛 Bug Reports

### Before Submitting a Bug Report
1. Check if the bug has already been reported in [Issues](https://github.com/eless-team/eless/issues)
2. Try to reproduce the issue with the latest version
3. Test with minimal configuration to isolate the problem

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Run command '...'
2. With configuration '...'
3. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g. Ubuntu 22.04]
- Python version: [e.g. 3.10.2]
- ELESS version: [e.g. 1.0.0]
- Installation method: [e.g. pip, source]

**Configuration**
```yaml
# Your configuration file (remove sensitive data)
```

**Logs**
```
# Relevant log output
```

**Additional context**
Any other context about the problem.
```

## ✨ Feature Requests

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Alternative solutions or features you've considered.

**Use case**
Describe your use case and why this feature would be valuable.

**Implementation ideas**
If you have ideas on how this could be implemented, please share.
```

## 📦 Pull Request Process

### Before Submitting
1. **Create an issue** to discuss major changes before implementing
2. **Fork the repository** and create a feature branch
3. **Write tests** for new functionality
4. **Update documentation** as needed
5. **Ensure all tests pass** and code follows style guidelines

### Pull Request Template
```markdown
**Description**
Brief description of changes.

**Type of change**
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update

**Testing**
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

**Checklist**
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process
1. **Automated checks** must pass (linting, tests, etc.)
2. **Code review** by maintainers
3. **Testing** on different platforms if relevant
4. **Documentation review** for user-facing changes
5. **Approval and merge** by maintainers

## 🌟 Recognition

Contributors will be recognized in:
- **CHANGELOG.md** for significant contributions
- **README.md** contributors section
- **Release notes** for major features
- **GitHub contributors** page

## 📞 Getting Help

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Code Reviews**: For feedback on pull requests

## 📜 Code of Conduct

Please note that this project is released with a [Code of Conduct](CODE_OF_CONDUCT.md). By participating in this project you agree to abide by its terms.

## 🏗️ Architecture Overview

### Core Components
```
src/
├── cli.py                  # Command-line interface
├── core/                   # Core functionality
│   ├── config_loader.py    # Configuration management
│   ├── config_wizard.py    # Interactive setup
│   ├── state_manager.py    # Processing state tracking
│   ├── archiver.py         # Cache management
│   ├── cache_manager.py    # Smart cache with LRU
│   └── resource_monitor.py # System resource monitoring
├── processing/             # Document processing
│   ├── file_scanner.py     # File discovery and hashing
│   ├── dispatcher.py       # Processing coordination
│   └── parsers/            # Document parsers
├── embedding/              # Embedding functionality
│   ├── model_loader.py     # Model management
│   └── embedder.py         # Embedding coordination
└── database/               # Database connectors
    ├── db_loader.py        # Database coordination
    ├── db_connector_base.py # Abstract base class
    └── *_connector.py      # Specific database implementations
```

### Extension Points
- **Parsers**: Add new file format support
- **Embedders**: Add new embedding providers
- **Databases**: Add new vector database support
- **Chunkers**: Add new text splitting strategies
- **Cache backends**: Add new caching implementations

Thank you for contributing to ELESS! 🎉