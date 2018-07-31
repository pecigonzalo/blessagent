test: lint
	@echo "--> Running Python tests"
	pipenv run py.test -s tests || exit 1
	@echo ""

lint:
	@echo "--> Linting Python files"
	PYFLAKES_NODOCTEST=1 pipenv run flake8 bless
	@echo ""
