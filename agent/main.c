#include <stdio.h>
#include <winsock2.h>
#include <unistd.h>

#define LEN_MSG 256
#define HOST "192.168.56.1"
#define PORT 13337
#define SLEEPTIME 2


SOCKET connectToServer() {
    SOCKET serverSocketFd;
    struct sockaddr_in serverHost;
    WSADATA WSAData;

    WSAStartup(MAKEWORD(2,0), &WSAData);

    serverSocketFd = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocketFd == INVALID_SOCKET) {
        printf("Error while creating socket. (%d)\n", WSAGetLastError());
        return SOCKET_ERROR;
    }

    serverHost.sin_family = AF_INET;
    serverHost.sin_port = htons(PORT);  // to little endian
    serverHost.sin_addr.s_addr = inet_addr(HOST);

    int result = connect(serverSocketFd, (SOCKADDR *) &serverHost, sizeof(serverHost));
    if (result == SOCKET_ERROR) {
        printf("Error while creating socket. (%d)\n", WSAGetLastError());
        closesocket(serverSocketFd);
        return SOCKET_ERROR;
    }

    u_long mode = 1;
    ioctlsocket(serverSocketFd, FIONBIO, &mode);

    return serverSocketFd;
}


int main() {
    char message[LEN_MSG];
    char response[8] = "Hello!\n";
    int sendSize = (int)strlen(response);

    while (1) {
        SOCKET serverFd = connectToServer();
        if (serverFd == SOCKET_ERROR) {
            WSACleanup();
            exit(EXIT_FAILURE);
        }

        int readBytes;
        int count = 0;

        do {
            readBytes = recv(serverFd, message, sizeof(message), 0);
            count++;

            printf("%d\n", count);
        } while(WSAGetLastError() == WSAEWOULDBLOCK);


        if (readBytes < 0) {
            printf("Error while reading data. (%d)", WSAGetLastError());
            closesocket(serverFd);
            WSACleanup();
            exit(EXIT_FAILURE);
        }

        printf("Data (%d): %s\n", readBytes, message);

        if (send(serverFd, response, sendSize, 0) != sendSize) {
            printf("Error while sending data. (%d)", WSAGetLastError());
            WSACleanup();
            closesocket(serverFd);
            exit(EXIT_FAILURE);
        }

        closesocket(serverFd);
        memset(message, 0x00, sizeof(message));

        sleep(SLEEPTIME);
    }
}