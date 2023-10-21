# Matchmaking Server


from ias_interface_data import *
from mms_interface_data import *
from socket import *


def main():
    matchmaking_queue = []

    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(("", MATCHMAKING_PORT))

    while True:
        # TODO: if the queue is not empty and is even in length, propose a match
        # if one of the proposees declines, they should be removed from the queue

        buflen = MMS_OPCODE_SIZE + len(MMS_OPCODE_ARGS_SEP) + MMS_MAX_ARGS_SIZE
        data, addr = server_socket.recvfrom(buflen)
        opcode, args = data.decode().split(MMS_OPCODE_ARGS_SEP)

        opcode = int(opcode)

        if opcode == MmsOpCode.MAKE_AVAILABLE:  # args are token and username
            token, username = args.split(" ")
            auth_socket = socket()
            auth_socket.connect((IAS_ADDRESS, IAS_PORT))
            msg = str(IasOpCode.VERIFY) + IAS_OPCODE_ARGS_SEP + token + " " + username
            auth_socket.send(msg.encode())
            status = int(auth_socket.recv(IAS_RESPONSE_CODE_SIZE).decode())
            auth_socket.close()
            if status == IasResponse.VERIFICATION_SUCCESSFUL:
                if (element := (username, addr)) not in matchmaking_queue:
                    matchmaking_queue.append(element)
            else:
                server_socket.sendto(MmsResponse.USER_NOT_AUTHENTICATED, addr)
        elif opcode == MmsOpCode.MAKE_UNAVAILABLE:  # args are token and username
            token, username = args.split(" ")
            auth_socket = socket()
            auth_socket.connect((IAS_ADDRESS, IAS_PORT))
            msg = str(IasOpCode.VERIFY) + IAS_OPCODE_ARGS_SEP + token + " " + username
            auth_socket.send(msg.encode())
            status = int(auth_socket.recv(IAS_RESPONSE_CODE_SIZE).decode())
            auth_socket.close()
            if status == IasResponse.VERIFICATION_SUCCESSFUL:
                if (element := (username, addr)) in matchmaking_queue:
                    matchmaking_queue.remove(element)
            else:
                server_socket.sendto(MmsResponse.USER_NOT_AUTHENTICATED, addr)
        elif opcode == MmsOpCode.ACCEPT_MATCH:
            # TODO
            pass
        elif opcode == MmsOpCode.DECLINE_MATCH:
            # TODO
            pass


if __name__ == "__main__":
    main()
