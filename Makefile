.PHONY: start stop restart rebuild logs ps

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
