.PHONY: install run smoke lint type

install:
	pip install -r requirements.txt

run:
	streamlit run app.py

smoke:
	python -m compileall .

lint:
	ruff check .

type:
	pyright
