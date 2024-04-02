#include <stdio.h>
#include <winsock2.h>
#include <ws2tcpip.h>

int PORT = 13337;
const char HOST[] = "0.0.0.0";

int main() {
    SOCKET serverSocketFd;
    struct sockaddr_in serverHost;
    WSADATA WSAData;

    WSAStartup(MAKEWORD(2,0), &WSAData);

    serverSocketFd = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocketFd == INVALID_SOCKET) {
        printf("Erreur creation socket\n");
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    if (closesocket(serverSocketFd) == SOCKET_ERROR) {
        printf("Could not close socket correctly\n");
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    serverHost.sin_family = AF_INET;
    serverHost.sin_port = htons(PORT);  // to little endian
    serverHost.sin_addr.s_addr = inet_addr(HOST);

    int result = connect(serverSocketFd, (SOCKADDR *) &serverHost, sizeof(serverHost));

    if (result == SOCKET_ERROR) {
        printf("Could not connect to server.%d\n", WSAGetLastError());
        WSACleanup();
        exit(EXIT_FAILURE);
    }

    WSACleanup();
    printf("hello!\n");
}