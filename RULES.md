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
