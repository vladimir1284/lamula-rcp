# Atajos de los gates de CI, para correrlos en local antes de commitear.
# Mismos nombres que en los proyectos LAMULA DRx y DSP, a proposito: quien salta
# entre los tres repositorios no tiene que aprender tres vocabularios.
#
#   make check   todo lo que corre el CI
#   make test    solo los tests de Python
#   make docs    compila el sitio en modo estricto

PY ?= .venv/bin/python

.PHONY: check lint test docs mmi-check

# El ancla del contrato vendorizado: nada de contract/vendor/ ni de
# mmi/src/contracts/ se edita a mano, ni siquiera para formatear.
lint:
	$(PY) tools/check_vendored_contract.py

test:
	$(PY) -m pytest tests -q

docs:
	uvx --with mkdocs-material==9.* mkdocs build --strict

mmi-check:
	cd mmi && npx vue-tsc --build

check: lint test docs
