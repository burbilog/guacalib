all:
	echo make tests or make build or make testpub

build:
	rm -rf build/ dist/ *.egg-info/
	python -m build

testpub: build
	python3 -m twine upload --repository testpypi dist/*

FORCE:
tests: FORCE
	./tests/test_guacaman.bats

.PHONY: push
push:
	@VERSION=$$(python3 -c "from guacalib.version import VERSION; print(VERSION)"); \
	if git rev-parse "v$$VERSION" >/dev/null 2>&1; then \
		echo "Error: Tag v$$VERSION already exists"; \
		exit 1; \
	fi; \
	if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Working directory not clean"; \
		exit 1; \
	fi; \
	echo "Creating and pushing tag v$$VERSION..."; \
	git tag -a "v$$VERSION" -m "Release v$$VERSION"; \
	git push origin "v$$VERSION"; \
	git push
