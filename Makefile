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
