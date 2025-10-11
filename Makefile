all:
	@echo "Guacalib Makefile targets:"
	@echo ""
	@echo "Development:"
	@echo "  make format     - Format Python code with black"
	@echo "  make format-check - Check code formatting without changes"
	@echo "  make tests      - Run full test suite"
	@echo "  make cleanup    - Clean up test database entries"
	@echo ""
	@echo "Build & Release:"
	@echo "  make build      - Build package for distribution"
	@echo "  make testpub    - Publish to PyPI test repository"
	@echo "  make pub        - Publish to PyPI production"
	@echo "  make push       - Create release tag and push to Git"

build: FORCE
	rm -rf build/ dist/ *.egg-info/
	python -m build

testpub: build
	python3 -m twine upload --repository testpypi dist/*

pub: build
	python3 -m twine upload dist/*

FORCE:
tests: FORCE
	pip uninstall -y guacalib
	pip install -e .
	/bin/bash tests/run_tests_with_summary.sh

cleanup: FORCE
	./tests/cleanup_test_entries.sh full

format: FORCE
	@echo "Formatting Python files with black..."
	@command -v black >/dev/null 2>&1 || { echo "Error: black is not installed. Install with: pip install black"; exit 1; }
	black guacalib/ *.py
	@echo "Formatting complete!"

format-check: FORCE
	@echo "Checking Python file formatting with black..."
	@command -v black >/dev/null 2>&1 || { echo "Error: black is not installed. Install with: pip install black"; exit 1; }
	black --check guacalib/ *.py

.PHONY: push
push:
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Working directory not clean"; \
		exit 1; \
	fi; \
	VERSION=$$(python3 -c "from guacalib.version import VERSION; print(VERSION)"); \
	if git rev-parse "v$$VERSION" >/dev/null 2>&1; then \
		echo "Error: Tag v$$VERSION already exists"; \
		exit 1; \
	fi; \
	echo "Updating version in README.md to $$VERSION..."; \
	sed -i.bak -E 's/version [0-9]+\.[0-9]+(\.[0-9]+)?/version '"$$VERSION"'/g' README.md; \
	rm README.md.bak; \
	git add README.md; \
	git commit -m "Update version to $$VERSION in README.md"; \
	echo "Creating and pushing tag v$$VERSION..."; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	git push origin main; \
	git push origin "v$$VERSION"
	git push
