# Agentic Coding Guidelines for TMS Development Wizard

This document provides comprehensive guidelines for AI coding agents to effectively navigate the development process when integrating with the TMS Development Wizard MCP server tools. These guidelines focus on methodology, workflow, and best practices.
## Core Development Methodology

### 1. Plan-Driven Development
- **Create a Todo List First**: Before writing any code, establish a clear todo list with timeline and milestones
- **Define Test Plans**: Include testing strategy for each development phase
- **Track Progress**: Mark tasks as in-progress when starting, completed when done
- **Atomic Updates**: Update task status immediately after completion, not in batches

### 2. Modular Architecture Approach
- **Layer Separation**: Maintain clear separation between data, service, and view layers
- **3-Layer Architecture**: Follow controller-service-repository pattern for backend implementations
- **Responsibility Isolation**: Each module should have a single, well-defined responsibility
- **Interface Design**: Define clear interfaces between modules before implementation

### 3. Iterative & Retrospective Development
- **Small Increments**: Implement features in small, testable units
- **Continuous Improvement Cycle**:
  1. Initial implementation
  2. Problem identification and analysis
  3. Refinement and optimization
  4. Unit testing and validation
  5. Code cleanup and documentation
- **Fail Fast**: Identify issues early through immediate testing after each implementation

### 4. Incremental Note-Taking Strategy
- **Document Critical Information Immediately**:
  - API investigation results
  - Parameter rules and constraints
  - Implementation decisions and rationale
  - Error patterns and resolutions
- **Update Development Notes**: Maintain a `development_notes.md` file throughout the project
- **Review Before New Phases**: Always review existing notes before starting new development phases

## Tool Usage Best Practices

### 1. API Discovery Process
- **Start with Overview**: Use `get_basic_info()` and `list_endpoints()` for initial exploration
- **Progressive Investigation**: Don't investigate all APIs upfront - explore as needed per development phase
- **Schema Analysis**: For complex endpoints, examine both request and response schemas
- **Example Validation**: When schemas are complex, review examples to understand usage patterns

### 2. Debugging and Refinement
- **Iterative Clarification**: When issues arise, re-examine existing information or explore new endpoints
- **Response Analysis**: Always analyze HTTP response codes and body content for error diagnosis
- **Validation First**: Verify API connectivity and basic functionality before complex implementations

## Testing and Validation Framework

### 1. Multi-Level Validation (Required at Each Stage)
**Never proceed to the next stage without completing all validations:**

#### Build Validation
- Ensure the project compiles/builds without errors
- Check for dependency conflicts
- Verify configuration files are properly set

#### Test Validation
- Execute unit tests for newly implemented code
- Ensure all tests pass before proceeding
- Create regression tests for critical functionality

#### Functional Validation
- Verify the implemented feature works as expected
- Test with realistic data scenarios
- Confirm integration with existing components

### 2. Testing Best Practices
- **Test Immediately**: Run unit tests right after implementing each module
- **Debug Until Success**: Never skip failing tests - debug until all pass
- **Maintain Smoke Tests**: Update core functionality tests as the project evolves
- **Lint First**: Run linters before testing to catch syntax and style issues
- **End-to-End Validation**: Test the complete application flow after implementation

### 3. Test Data Management
- Create realistic dummy data based on actual use cases
- Use full addresses and complete data structures for testing
- Maintain test data sets for different scenarios

## Development Workflow

### 1. Stage Progression Rules
- **Explicit Stage Declaration**: Announce stage start and completion conditions
- **Validation Gates**: Complete all three validations (build, test, functional) before proceeding
- **Failure Handling**: On validation failure, fix and re-validate until success
- **No Skipping**: Never bypass validation steps

### 2. Error Handling and Recovery
- **Immediate Response**: Address errors as soon as they're detected
- **Root Cause Analysis**: Investigate underlying causes, not just symptoms
- **Documentation**: Record error patterns and solutions in development notes
- **Preventive Measures**: Update code to prevent similar errors in future

### 3. External API Integration
- **Connection Timeout Awareness**: Consider HTTP timeouts for long-running operations
- **Default Value Handling**: Omit request body fields with null defaults unless explicitly required
- **Response Validation**: Always validate API responses before using data
- **Error Response Handling**: Implement proper error handling for all API calls

## Security and Best Practices

### 1. Sensitive Information Management
- **No Hardcoding**: Never hardcode API keys or credentials in source code
- **Environment Variables**: Use configuration files or environment variables for sensitive data
- **Key Rotation**: Be prepared to update keys without code changes

### 2. Code Quality Standards
- **Follow Existing Patterns**: Match the codebase's existing style and conventions
- **Dependency Management**: Use appropriate package managers (uv for Python, Gradle/Maven for Java)
- **Clean Code Principles**: Write readable, maintainable, and self-documenting code

## Programming Language Specific Tips

### Python Development
- **Dependency Management**: Use `uv` for project initialization and package management
  - `uv init`: Initialize project in current directory
  - `uv add [package]`: Add new dependencies
- **Framework Choice**: Prefer Streamlit for dashboard/UI development
- **Testing**: Use pytest for unit testing, maintain test coverage
- **Linting**: Run `ruff` before committing code

### Java Development
- **Build Tool**: Use Gradle or Maven for dependency management
- **Spring Boot**: Follow Spring Boot best practices for web applications
  - Use appropriate annotations (@RestController, @Service, @Repository)
  - Implement proper exception handling with @ExceptionHandler
- **Version**: Target Java 17+ for modern features
- **Frontend Integration**: Use Thymeleaf for server-side rendering with Spring Boot
- **Testing**: Utilize JUnit and MockMvc for comprehensive testing

## Communication and Reporting

### 1. Progress Updates
- Provide clear stage transition announcements
- Report validation results explicitly
- Communicate blockers immediately

### 2. Documentation Standards
- Maintain clear, concise documentation
- Update README with setup and usage instructions
- Document API contracts and data models

## Final Checklist Before Completion

- [ ] All todo items marked as completed
- [ ] All tests passing
- [ ] Application runs without errors
- [ ] Linting checks passed
- [ ] Sensitive information properly managed
- [ ] Development notes updated
- [ ] Code follows established patterns
- [ ] Documentation complete
