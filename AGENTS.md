# Development Rules for LLMs

## Code Style and Structure
- Use meaningful variable and function names
- Add type hints to function signatures
- Structure code in logical modules and packages

## Documentation
- Write docstrings for all public functions, classes, and modules
- Use Google-style or NumPy-style docstrings consistently
- Include parameter descriptions, return types, and examples
- Update README.md when adding new features

## Code Quality
- Write code for clarity first. Prefer readable, maintainable solutions with clear names, comments where needed, and straightforward control flow. 
- Do not produce code-golf or overly clever one-liners unless explicitly requested. 
- Use high verbosity for writing code and code tools.
- Don't add unnecessary dependencies
- Avoid deeply nested code structures
- Use descriptive error messages
- Handle exceptions appropriately
- Avoid global variables
- Strictly adhere to single-responsibility principles

## Security
- Never hardcode sensitive information
- Validate all user inputs
- Handle file paths securely
- Use secure default settings

## Performance
- Optimize for readability first, then performance
- Comment any non-obvious optimizations
- Consider memory usage for large data operations

## When Suggesting Changes
- Explain the reasoning behind proposed changes
- Offer complete solutions, not partial fixes
- Respect the existing architecture

## When reviewing the code
- Check for issues such as rule violations in this rules file, deviations from best practices, design patterns, or security concerns. Have it document these reviews into a file for follow-up AI sessions to iteratively address each issue.

## Running the tests

The test suite uses bats (Bash Automated Testing System)

To run the tests TEST_CONFIG must be set up. By default it 
should be set /home/rm/.guacaman.ini unless user prompts something
else.

```bash
# Set TEST_CONFIG to point to a valid .guacaman.ini file:
export TEST_CONFIG=/home/rm/.guacaman.ini
bats -t --print-output-on-failure tests/test_guacaman.bats
or
make tests
```

## Project specific details

Details are in CLAUDE.md file.
