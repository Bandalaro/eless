# ELESS Quick Start Guide

This guide provides a fast path to get ELESS up and running.

## Installation

### Basic Installation

```bash
git clone https://github.com/Bandalaro/eless.git
cd eless
pip install -e .
```

### Full Installation (Recommended)

```bash
pip install -e ".[full]"
```

This includes all features: embedding models, database connectors, and document parsers.

## Health Check

Verify your installation:

```bash
eless health
```

## Initialize Configuration

Run the setup wizard:

```bash
eless init
```

Or use a quick-start template:

```bash
eless template create lightweight
```

## Process Your First Documents

### Simple Processing

```bash
eless go /path/to/documents
```

### Full Control

```bash
eless process /path/to/documents \
  --databases chroma,faiss \
  --chunk-size 512 \
  --log-level INFO
```

### Interactive Mode

```bash
eless process -i
```

## Check Status

```bash
eless status --all
```

## Try the Demo

```bash
eless demo
```

## Next Steps

- Refer to [README.md](../README.md) for detailed configuration and architecture.
- See [EXAMPLES_AND_USAGE.md](EXAMPLES_AND_USAGE.md) for more usage examples.
- Check [API_REFERENCE.md](API_REFERENCE.md) for programmatic usage.

**Quick Start Version**: 1.0  
**Last Updated**: 2025-10-25