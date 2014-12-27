
deps:
	@$(PIP) install -i http://pypi.douban.com/simple -r requirements.txt

clean_pyc:
	find . -not \( -path './venv' -prune \) -name '*.pyc' -exec rm -f {} \;
