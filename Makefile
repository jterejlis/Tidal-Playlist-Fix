.PHONY: help run shell audit fix

help:
	@python main.py --help

run:
	@. .venv/bin/activate && python main.py $(ARGS)

shell:
	@. .venv/bin/activate && python main.py shell

audit:
	@. .venv/bin/activate && python main.py health-audit --path "$(PATH)" --export-json --output "$(OUT)"

fix:
	@. .venv/bin/activate && python main.py fix --path "$(PATH)" --manual-accept --create-playlist --name "$(NAME)" --description "$(DESC)"
