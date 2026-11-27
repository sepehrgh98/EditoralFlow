.PHONY: start stop restart rebuild logs ps dev check test-live hooks

start:
	$(MAKE) -C backend start

stop:
	$(MAKE) -C backend stop

restart:
	$(MAKE) -C backend restart

rebuild:
	$(MAKE) -C backend rebuild

logs:
	$(MAKE) -C backend logs

ps:
	$(MAKE) -C backend ps

dev:
	$(MAKE) -C backend dev

check:
	$(MAKE) -C backend check

test-live:
	$(MAKE) -C backend test-live

hooks:
	$(MAKE) -C backend hooks
