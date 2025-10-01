# Agentic Coding Guidelines for TMS Development Wizard

Compact guidelines for AI agents integrating with TMS Development Wizard MCP server tools.

## 🎯 CRITICAL RULES (Never Skip These)

1. **Create Todo List First** - Establish clear tasks with milestones before coding
2. **Three-Stage Validation Gate** - Complete ALL before proceeding to next stage:
   - ✅ Build validation (compiles without errors)
   - ✅ Test validation (all tests pass)
   - ✅ Functional validation (feature works as expected)
3. **Test Immediately** - Run unit tests right after each module implementation
4. **Update Tasks Atomically** - Mark in-progress when starting, completed when done (not in batches)
5. **Never Hardcode Secrets** - Use environment variables for API keys and credentials

## 📋 Development Methodology

### Plan-Driven Development
- Todo list with timeline and milestones
- Define test plans for each phase
- Track progress: pending → in-progress → completed
- Update status immediately after completion

### Modular Architecture
- **3-Layer Pattern**: Controller → Service → Repository
- Clear separation: data / service / view layers
- Single responsibility per module
- Define interfaces before implementation
- Derive DTOs and validation rules from `get_response_schema()` so each module consumes responses deterministically

### Iterative Development Cycle
1. Initial implementation (small, testable units)
2. Problem identification
3. Refinement and optimization
4. Unit testing and validation
5. Code cleanup and documentation

**Fail Fast**: Test immediately to identify issues early

### Incremental Documentation
- Maintain `development_notes.md` throughout project
- Document immediately: API results, parameter rules, decisions, error patterns
- Review notes before starting new phases

## 🔧 Tool Usage

### API Discovery (Progressive, Not All Upfront)
1. Start with overview: `get_basic_info()`, `list_endpoints()`
2. Explore as needed per development phase using `get_endpoint_overview()` and `get_request_body_schema()`
3. Design parsing logic with `get_response_schema()` before coding modules – identify required fields, nullability, and nesting so controllers/services can extract data predictably
4. Review examples for complex schemas: `list_examples()`, `get_example()`

### Debugging
- Re-examine existing info or explore new endpoints
- Analyze HTTP response codes and body content
- Verify API connectivity before complex implementations

## ✅ Testing Framework

### Validation Requirements (Each Stage)
**Never proceed without completing ALL three:**

| Type | Requirements |
|------|-------------|
| **Build** | Compiles without errors, no dependency conflicts, config verified |
| **Test** | Unit tests pass, regression tests for critical functionality |
| **Functional** | Feature works, realistic data tested, integration confirmed |

### Testing Best Practices
- **Lint First** → Run linters before testing
- **Test Immediately** → After each module
- **Debug Until Success** → Never skip failing tests
- **End-to-End** → Test complete flow after implementation
- **Realistic Data** → Use full addresses and complete structures

## 🔄 Workflow Rules

### Stage Progression
- Announce stage start and completion conditions
- Complete all three validations before proceeding
- On validation failure: fix → re-validate → repeat until success
- **No skipping validation steps**

### Error Handling
- Address errors immediately upon detection
- Root cause analysis, not just symptoms
- Document error patterns in development notes
- Implement preventive measures

### External API Integration
- Consider HTTP timeouts for long operations
- Omit null default fields unless explicitly required
- Validate responses before using data
- Implement proper error handling for all calls


## 🐍 Python | ☕ Java

### Python
- **Package Manager**: `uv init`, `uv add [package]`
- **UI Framework**: Streamlit for dashboards
- **Testing**: pytest with coverage
- **Linting**: ruff before committing

### Java
- **Build Tool**: Gradle or Maven
- **Version**: Java 17+
- **Spring Boot**: Use @RestController, @Service, @Repository, @ExceptionHandler
- **Frontend**: Thymeleaf for server-side rendering
- **Testing**: JUnit + MockMvc

---

**⚠️ Remember: Create TO DO lists based on these guidelines. Run unit tests between every module implementation!**
