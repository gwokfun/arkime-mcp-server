# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-04-25

### Changed
- **BREAKING**: Complete rewrite from TypeScript/Node.js to Python 3/FastMCP
- Replaced `@modelcontextprotocol/sdk` with FastMCP framework
- Replaced `digest-fetch` with custom httpx-based Digest authentication
- Project structure reorganized into proper Python package

### Added
- **Configuration System**: YAML configuration file support (`config.yaml`)
- **Environment Support**: .env file support via python-dotenv
- **Tool Management**: Enable/disable individual tools via configuration
- **18 New Tools** extending API coverage from 12 to 30+ tools:
  - `get_session_raw` - Get raw session data
  - `get_field_values` - Get possible values for a field
  - `get_current_user` - Get current user information
  - `get_settings` - Get Arkime viewer settings
  - `add_tags` - Add tags to sessions
  - `remove_tags` - Remove tags from sessions
  - `get_stats` - Get Arkime statistics
  - `get_es_stats` - Get Elasticsearch/OpenSearch statistics
  - `create_hunt` - Create hunt jobs for packet payload search
  - `get_hunts` - List hunt jobs
  - `delete_hunt` - Delete hunt jobs
  - `create_view` - Create saved views
  - `get_views` - List saved views
  - `delete_view` - Delete saved views
  - `get_notifiers` - List configured notifiers
  - `get_parliament` - Get parliament (multi-cluster) information
- **Documentation**:
  - Comprehensive README with all 30+ tools
  - MIGRATION.md guide for TypeScript to Python migration
  - examples.py with usage examples
  - config.example.yaml template
  - .env.example template
- **Testing**: Basic test suite (test_basic.py)
- **Utilities**: Improved helper functions for formatting

### Fixed
- Better error handling and validation
- Improved timestamp formatting
- More robust HTTP Digest authentication implementation

### Removed
- TypeScript/Node.js implementation (preserved in git history)
- npm dependencies
- Build step requirement

## [1.0.0] - 2024-XX-XX

### Added
- Initial TypeScript implementation
- 12 core tools for Arkime interaction
- HTTP Digest authentication via digest-fetch
- Basic environment variable configuration
- Support for session search, analysis, and network investigation
- Arkime cluster health monitoring
