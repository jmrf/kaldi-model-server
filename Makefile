.PHONY: clean test lint init check-readme

JOBS ?= 1

help:
	@echo "	install"
	@echo "		Install dependencies and download needed models."
	@echo "	clean"
	@echo "		Remove Python/build artifacts."
	@echo "	formatter"
	@echo "		Apply black formatting to code."
	@echo "	lint"
	@echo "		Lint code with flake8, and check if black formatter should be applied."
	@echo "	types"
	@echo "		Check for type errors using pytype."
	@echo "	pyupgrade"
	@echo "		Uses pyupgrade to upgrade python syntax."
	@echo "	readme-toc"
	@echo "			Generate a Table Of Content for the README.md"
	@echo "	test"
	@echo "		Run pytest on tests/."
	@echo "		Use the JOBS environment variable to configure number of workers (default: 1)."
	@echo "	build-docker"
	@echo "		Build package's docker image"
	@echo "	upload-package"
	@echo "		Upload package to Melior Pypi server"
	@echo " git-tag"
	@echo "		Create a git tag based on the current pacakge version and push"
	@echo " make-run"
	@echo "		Run the api"


install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip list

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f  {} +
	find . -name 'README.md.*' -exec rm -f  {} +
	rm -rf build/
	rm -rf .pytype/
	rm -rf dist/
	rm -rf docs/_build
	# rm -rf *egg-info
	# rm -rf pip-wheel-metadata

run:
	python -m kserver.run -m 12

formatter:
	black . --exclude kaldi/

lint:
	flake8 . tests --exclude tests/
	black --check . tests --exclude kaldi/

types:
	# https://google.github.io/pytype/
	pytype --keep-going . --exclude ./kaldi .venv

pyupgrade:
	find .  -name '*.py' | \
		grep -v 'proto\|eggs\|docs\|kaldi\|.venv' | \
		xargs pyupgrade --py36-plus

readme-toc:
	# https://github.com/ekalinin/github-markdown-toc
	find . \
		! -path './kaldi/*' \
		! -path './.venv/*' \
		-name README.md \
		-exec gh-md-toc --insert {} \;

test: clean
	# OMP_NUM_THREADS can improve overral performance using one thread by process
	# (on tensorflow), avoiding overload
	OMP_NUM_THREADS=1 pytest tests -n $(JOBS) --cov .

build-docker:
	./scripts/build_docker.sh


build-pykaldi-docker:
	# TODO: When ready change to:
	#
	# docker buildx build --push \
    # 	--platform linux/amd64,linux/arm/v7 \
	# 	-t jmrf/pykaldi:0.2.1-cp38 \
	# 	-f dockerfiles/pykaldi.Dockerfile .
	#
	# For now:
	#
	docker buildx build --load \
    	--platform linux/amd64 \
		-t jmrf/pykaldi:0.2.1-cp38 \
		-f dockerfiles/pykaldi.Dockerfile .


upload-package: clean
	python setup.py sdist
	twine upload dist/* -r melior

tag:
	git tag $$( python -c 'import .; print(..__version__)' )
	git push --tags

