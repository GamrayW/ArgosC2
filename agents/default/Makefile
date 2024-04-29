ifndef HOST
	HOST=\"192.168.56.1\"
endif

ifndef HOSTS
	HOSTS={\"127.0.0.1\"}
endif

ifndef PORT
	PORT=13337
endif

ifndef SLEEPTIME
	SLEEPTIME=2000
endif


out = agent.exe
CC = /usr/bin/x86_64-w64-mingw32-gcc


default:
	$(CC) -std=c11 -o $(out) -DHOST=$(HOST) -DHOSTS="$(HOSTS)" -DPORT=$(PORT) -DSLEEPTIME=$(SLEEPTIME) main.c -lwsock32 -lws2_32
