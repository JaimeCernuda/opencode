# OpenCode TUI Integration Project

## Context
We are developing an integration between the OpenCode TUI (Terminal User Interface) and the Claude Agents SDK Python implementation. 

Find the baseline backend server on `@opencode-tui-adapter/src/opencode_tui_adapter/server.py`, which contains a Python server with a placeholder implementation of the endpoints described on `@OPENCODE_ENDPOINTS.md`.

Our goal is to connect these endpoints with the claude-agent-sdk in Python, while supporting the ability to add new agents (like opencode-sdk or gemini sdk or custom sdk).

### Available Resources
- **Baseline Backend Server**: Located in `@opencode-tui-adapter/src/opencode_tui_adapter/server.py` with placeholder REST API implementations
- **TUI Codebase**: Located in `@packages/tui`, built with Go and Bubbletea framework
- **TUI Code Documentation**: Located in `@TUI_ARCHITECTURE.md`
- **Claude SDK Documentation**: Available in `@CLAUDE_AGENT_SDK_PYTHON.md`
- **Claude SDK Codebase**: Accessible via claude-agent-sdk-python MCP server
- **API Specification**: REST endpoints documented in `@OPENCODE_ENDPOINTS.md`

## Objective
ultrathink and Create a comprehensive integration plan to connect the claude-agent-sdk to the TUI endpoints, ensuring proper communication protocols are established and maintained.

## Requirements

### Phase 1: Core Communication Infrastructure
**Priority: Critical**
- Establish session management (create, restore, close)
- Implement bidirectional message passing (send/receive)
- Set up basic request/response handling
- Configure comprehensive logging system with structured logging (JSON format)
- Ensure proper error handling with detailed logging and metrics collection
- Implement request tracing for debugging complex interactions

### Phase 2: UI Operations
**Priority: High**
- Implement theme switching functionality
- Support UI configuration endpoints
- Enable display preference management
- Maintain state consistency between TUI and SDK

### Phase 3: Extended Functionality
**Priority: Standard**
- Complete remaining endpoint implementations
- Add advanced features as specified in documentation
- Optimize performance and resource usage

## Development Guidelines

1. **Error Handling & Logging**: For unimplemented endpoints, return explicit error responses with:
   - Clear error messages indicating "Not Yet Implemented"
   - Timestamp of the request
   - Endpoint path that was called
   - Comprehensive logging framework with multiple levels (DEBUG, INFO, WARNING, ERROR)
   - Log entries for tracking implementation progress and debugging
   - Request/response logging for all API calls
   - Performance metrics logging for optimization insights

2. **Testing Strategy**:
   - **Unit Tests**: Achieve maximum code coverage for all implemented functions
   - **Integration Tests**: Python-based test suite that:
     - Deploys the server locally
     - Calls each endpoint directly
     - Validates request/response formats against TUI expectations
     - Ensures data integrity across the communication pipeline

## Deliverables

1. **Analysis Document**: 
   - Mapping between TUI endpoints and SDK capabilities
   - Communication protocol specifications
   - Data flow diagrams

2. **Implementation Plan**:
   - Detailed steps for each phase
   - Technical approach for endpoint integration
   - Dependency management strategy

3. **Code Implementation**:
   - Server implementation respecting TUI communication patterns
   - Comprehensive test suite
   - Documentation for each endpoint

## Specific Tasks

Please provide:
1. A detailed analysis of how the TUI endpoints map to Claude SDK functionality
2. A technical implementation plan for establishing the communication bridge
3. Code structure recommendations for the server implementation
4. Test scenarios covering all three phases

## Constraints
- Must maintain compatibility with existing TUI Go/Bubbletea implementation by only modifying the code on `@opencode-tui-adapter`
- Should respect the communication patterns established by the TUI
- Error responses must be informative for debugging purposes
- All implementations must be testable and maintainable
- All implementation must follow each supporting document and code standard
- After implementing each function check supporting document or code base to ensure proper implementation
- If your context window close to finish or compact please make sure summarize whatever you build and read from that point to continue
- Maintain logging consistency across all components for unified debugging experience

After each phase implemented, Start with unit tests. built tests for each with as much coverage of the implemented features as possible, ensure that they are executed and all pass, once the tests for the phase pass, then deploy the server and run Python integration tests that call the REST endpoints directly. Verify that all requests and responses match the TUI’s expectations and that errors are logged with actionable messages.

Please begin by analyzing the endpoint documentation and proposing an architecture that best connects these two systems.