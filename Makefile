PY ?= python
export PYTHONPATH := src

.PHONY: all ingest run test
all: ingest run
ingest:
	$(PY) -m ycs.ingest
run:
	$(PY) -m ycs.pipeline
test:
	$(PY) -m pytest -q tests
