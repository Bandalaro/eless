# ELESS Documentation

Complete documentation for the ELESS (Evolving Low-resource Embedding and Storage System).

## 📚 Documentation Index

### For Users

- **[Quick Start Guide](QUICK_START.md)** - Get started in 5 minutes
  - Installation instructions
  - Basic usage tutorial
  - Common use cases
  - Configuration guide
  - Troubleshooting tips

- **[User Guide](../README.md)** - Complete user documentation
  - Feature overview
  - Architecture description
  - Command reference
  - Configuration options
  - Examples and workflows

### For Developers

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
  - Core components
  - Processing components
  - Embedding components
  - Database components
  - CLI interface
  - Configuration schema
  - Error handling
  - Best practices

- **[Developer Guide](DEVELOPER_GUIDE.md)** - Development documentation
  - Development setup
  - Architecture overview
  - Code structure
  - Development workflow
  - Testing guide
  - Adding new features
  - Performance optimization
  - Contributing guidelines

### Project Documentation

- **[Test Summary](../TEST_AND_DEBUG_SUMMARY.md)** - Testing and debugging report
  - Test results (56/56 passing)
  - Bug fixes
  - Code improvements
  - Recommendations

- **[Changelog](../CHANGELOG.md)** - Version history and changes
- **[Contributing](../CONTRIBUTING.md)** - Contribution guidelines
- **[License](../LICENSE)** - MIT License

---

## 📖 Reading Guide

### I'm a New User

Start here:
1. [Quick Start Guide](QUICK_START.md) - 5-minute tutorial
2. [User Guide](../README.md) - Complete features
3. [API Reference](API_REFERENCE.md) - When you need specific details

### I Want to Integrate ELESS

Read these:
1. [API Reference](API_REFERENCE.md) - Understand the API
2. [Quick Start Guide](QUICK_START.md) - Basic integration
3. [Developer Guide](DEVELOPER_GUIDE.md) - Advanced integration

### I Want to Contribute

Follow this path:
1. [Developer Guide](DEVELOPER_GUIDE.md) - Setup and workflows
2. [Contributing Guidelines](../CONTRIBUTING.md) - Contribution process
3. [API Reference](API_REFERENCE.md) - Understand the codebase
4. [Test Summary](../TEST_AND_DEBUG_SUMMARY.md) - Current state

### I'm Debugging an Issue

Check these:
1. [Quick Start Guide](QUICK_START.md) - Troubleshooting section
2. [User Guide](../README.md) - Error messages and solutions
3. [Developer Guide](DEVELOPER_GUIDE.md) - Debugging techniques
4. [API Reference](API_REFERENCE.md) - Component details

---

## 🎯 Documentation by Topic

### Installation & Setup
- [Quick Start - Installation](QUICK_START.md#installation)
- [Developer Guide - Development Setup](DEVELOPER_GUIDE.md#development-setup)

### Configuration
- [Quick Start - Configuration Guide](QUICK_START.md#configuration-guide)
- [API Reference - Configuration Schema](API_REFERENCE.md#configuration-schema)
- [User Guide - Configuration Options](../README.md#configuration-options)

### Usage & Examples
- [Quick Start - Common Use Cases](QUICK_START.md#common-use-cases)
- [Quick Start - Example Workflows](QUICK_START.md#example-workflows)
- [User Guide - Usage Examples](../README.md#usage-examples)

### CLI Commands
- [Quick Start - CLI Command Reference](QUICK_START.md#cli-command-reference)
- [API Reference - CLI Interface](API_REFERENCE.md#cli-interface)
- [User Guide - Commands Reference](../README.md#commands-reference)

### API & Programming
- [API Reference - Core Components](API_REFERENCE.md#core-components)
- [API Reference - Processing Components](API_REFERENCE.md#processing-components)
- [API Reference - Embedding Components](API_REFERENCE.md#embedding-components)
- [API Reference - Database Components](API_REFERENCE.md#database-components)

### Architecture & Design
- [Developer Guide - Architecture Overview](DEVELOPER_GUIDE.md#architecture-overview)
- [User Guide - Architecture Overview](../README.md#architecture-overview)
- [API Reference - System Architecture](API_REFERENCE.md#core-components)

### Testing & Quality
- [Test Summary](../TEST_AND_DEBUG_SUMMARY.md)
- [Developer Guide - Testing](DEVELOPER_GUIDE.md#testing)
- [Developer Guide - Debugging](DEVELOPER_GUIDE.md#debugging)

### Performance
- [Quick Start - Performance Tips](QUICK_START.md#performance-tips)
- [API Reference - Performance Tuning](API_REFERENCE.md#performance-tuning)
- [Developer Guide - Performance Optimization](DEVELOPER_GUIDE.md#performance-optimization)

### Extending ELESS
- [Developer Guide - Adding New Features](DEVELOPER_GUIDE.md#adding-new-features)
- [Developer Guide - Adding a New Parser](DEVELOPER_GUIDE.md#adding-a-new-parser)
- [Developer Guide - Adding a New Database Connector](DEVELOPER_GUIDE.md#adding-a-new-database-connector)

### Troubleshooting
- [Quick Start - Troubleshooting](QUICK_START.md#troubleshooting)
- [API Reference - Troubleshooting](API_REFERENCE.md#troubleshooting)
- [User Guide - Error Messages and Solutions](../README.md#error-messages-and-solutions)

### Contributing
- [Contributing Guidelines](../CONTRIBUTING.md)
- [Developer Guide - Contributing](DEVELOPER_GUIDE.md#contributing)
- [Developer Guide - Development Workflow](DEVELOPER_GUIDE.md#development-workflow)

---

## 📊 Documentation Statistics

- **Total Pages:** 4 major documents
- **Total Lines:** ~3,500 lines
- **Total Words:** ~35,000 words
- **Code Examples:** 100+ examples
- **API Endpoints:** 50+ methods documented

---

## 🔍 Quick Reference

### Most Common Tasks

| Task | Documentation |
|------|--------------|
| Install ELESS | [Quick Start](QUICK_START.md#installation) |
| First-time usage | [Quick Start Tutorial](QUICK_START.md#5-minute-tutorial) |
| Configure databases | [Configuration Guide](QUICK_START.md#configuration-guide) |
| Process documents | [CLI Commands](QUICK_START.md#cli-command-reference) |
| Check status | [User Guide](../README.md#eless-status) |
| Resume processing | [User Guide](../README.md#migration-and-resumption) |
| Add new parser | [Developer Guide](DEVELOPER_GUIDE.md#adding-a-new-parser) |
| Add new database | [Developer Guide](DEVELOPER_GUIDE.md#adding-a-new-database-connector) |
| Run tests | [Developer Guide](DEVELOPER_GUIDE.md#testing) |
| Debug issues | [Developer Guide](DEVELOPER_GUIDE.md#debugging) |
| Contribute code | [Contributing](../CONTRIBUTING.md) |

### Most Used API Methods

| Component | Method | Documentation |
|-----------|--------|--------------|
| ElessPipeline | `run_process()` | [API Reference](API_REFERENCE.md#run_processsource_path-str) |
| StateManager | `get_all_files()` | [API Reference](API_REFERENCE.md#get_all_files---listdictstr-any) |
| Embedder | `embed_and_archive_chunks()` | [API Reference](API_REFERENCE.md#embed_and_archive_chunkschunks_generator-generator---generatordictstr-any-none-none) |
| DatabaseLoader | `initialize_database_connections()` | [API Reference](API_REFERENCE.md#initialize_database_connections) |
| ConfigLoader | `load_config()` | [API Reference](API_REFERENCE.md#load_configconfig_path-optionalstr--none-cli_overrides-optionaldict--none---dictstr-any) |

### Most Common Configurations

| Configuration | File | Documentation |
|--------------|------|--------------|
| Logging setup | `logging:` section | [Quick Start](QUICK_START.md#1-logging) |
| Embedding model | `embedding:` section | [Quick Start](QUICK_START.md#2-embedding) |
| Chunk size | `chunking:` section | [Quick Start](QUICK_START.md#3-chunking) |
| Database selection | `databases:` section | [Quick Start](QUICK_START.md#4-databases) |
| Resource limits | `resource_limits:` section | [Quick Start](QUICK_START.md#5-resource-limits) |

---

## 🆕 Recent Updates

### October 2025

- ✅ All 56 tests passing
- 🐛 Fixed file path overwriting bug
- 📚 Created comprehensive documentation
- 📖 Added Quick Start Guide
- 📘 Added API Reference
- 📗 Added Developer Guide
- 📝 Added Test Summary

---

## 🤝 Getting Help

### Documentation Not Clear?

- Open an issue: [GitHub Issues](https://github.com/Bandalaro/eless/issues)
- Start a discussion: [GitHub Discussions](https://github.com/Bandalaro/eless/discussions)

### Found a Bug?

- Check [Troubleshooting](QUICK_START.md#troubleshooting) first
- Check [Error Messages](API_REFERENCE.md#troubleshooting)
- Report it: [GitHub Issues](https://github.com/Bandalaro/eless/issues)

### Want to Contribute?

- Read [Contributing Guidelines](../CONTRIBUTING.md)
- Read [Developer Guide](DEVELOPER_GUIDE.md)
- Check [Open Issues](https://github.com/Bandalaro/eless/issues)

---

## 📝 Documentation Improvements

We welcome documentation improvements! To contribute:

1. Fork the repository
2. Edit the relevant `.md` file
3. Submit a pull request
4. Follow the [Contributing Guidelines](../CONTRIBUTING.md)

### Documentation Style Guide

- Use clear, concise language
- Include code examples
- Add diagrams where helpful
- Link to related sections
- Keep formatting consistent
- Test all code examples

---

## 📄 License

All documentation is licensed under MIT License - See [LICENSE](../LICENSE) file for details.

---

## 🔗 External Resources

### Vector Databases
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

### Embedding Models
- [Sentence Transformers](https://www.sbert.net/)
- [Hugging Face Models](https://huggingface.co/models)

### Python Tools
- [Click Documentation](https://click.palletsprojects.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [PyYAML Documentation](https://pyyaml.org/)

---

**Last Updated:** October 17, 2025  
**Version:** 1.0.0  
**Status:** Production Ready ✅
