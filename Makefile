# deps that can't be installed automatically
check-deps:

# installable deps
check-installable-deps:
	test -f models/deepspeech-0.9.3-models.pbmm || wget -P models https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.pbmm
	test -f models/deepspeech-0.9.3-models.scorer || wget -P models https://github.com/mozilla/DeepSpeech/releases/download/v0.9.3/deepspeech-0.9.3-models.scorer

install: check-deps check-installable-deps
	pipenv install

start:
	python src/main.py
