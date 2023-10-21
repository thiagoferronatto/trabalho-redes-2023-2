# Matchmaking Server


from ias_interface_data import *
from mms_interface_data import *
from style import *
from socket import *


class LogMessage:
    def server_available():
        return f"{Style.blue("[INFO]")} Servidor disponível pela porta {Style.bold(MATCHMAKING_PORT)}."

    def match_available(player_1, player_2):
        return f"{Style.blue("[INFO]")} Partida(s) disponível(is). Pareando {Style.bold(player_1)} com {Style.bold(player_2)}."

    def declined_match(player_1, player_2):
        return f"{Style.warn("[AVISO]")} Jogador {Style.bold(player_1)} recusou a partida com {Style.bold(player_2)}; expulsando {Style.bold(player_1)} da fila."

    def match_ready(player_1, player_2):
        return f"{Style.blue("[INFO]")} Partida pronta entre {Style.bold(player_1)} e {Style.bold(player_2)}; enviando os dados de um para o outro."

    def queued(player_name):
        return f"{Style.blue("[INFO]")} Jogador {Style.bold(player_name)} entrou na fila."

    def queueing_failed(player_name):
        return f"{Style.warn("[AVISO]")} Jogador {Style.bold(player_name)} quis entrar na fila, mas não estava autenticado."

    def unqueued(player_name):
        return f"{Style.blue("[INFO]")} Jogador {Style.bold(player_name)} saiu da fila."

    def unqueueing_failed(player_name):
        return f"{Style.warn("[AVISO]")} Jogador {Style.bold(player_name)} quis sair da fila, mas não estava autenticado."


def main():
    matchmaking_queue = []

    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(("", MATCHMAKING_PORT))

    print(LogMessage.server_available())

    while True:
        qlen = len(matchmaking_queue)
        if qlen > 0 and qlen % 2 == 0:
            print(LogMessage.match_available(matchmaking_queue[0][0], matchmaking_queue[1][0]))

            p1_socket = socket(AF_INET, SOCK_DGRAM)
            p2_socket = socket(AF_INET, SOCK_DGRAM)

            p1, p2 = matchmaking_queue[0], matchmaking_queue[1]

            p1_addr, p2_addr = p1[1], p2[1]

            msg = str(MmsResponse.MATCH_AVAILABLE).encode()
            p1_socket.sendto(msg, p1_addr)
            p2_socket.sendto(msg, p2_addr)

            p1_decision = int(p1_socket.recv(MMS_OPCODE_SIZE).decode())
            p2_decision = int(p2_socket.recv(MMS_OPCODE_SIZE).decode())

            p1_declined, p2_declined = False, False

            if p1_decision == MmsOpCode.DECLINE_MATCH:
                print(LogMessage.declined_match(p1[0], p2[0]))
                matchmaking_queue.remove(p1)
                p1_declined = True
            if p2_decision == MmsOpCode.DECLINE_MATCH:
                print(LogMessage.declined_match(p2[0], p1[0]))
                matchmaking_queue.remove(p2)
                p2_declined = True

            if p1_declined and p2_declined:
                p1_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p1_addr)
                p2_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p2_addr)
            elif p1_declined:
                p1_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p1_addr)
                p2_socket.sendto(str(MmsResponse.OTHER_PLAYER_DECLINED).encode(), p2_addr)
            elif p2_declined:
                p2_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p1_addr)
                p1_socket.sendto(str(MmsResponse.OTHER_PLAYER_DECLINED).encode(), p2_addr)
            if p1_declined or p2_declined:
                p1_socket.close()
                p2_socket.close()
                continue

            print(LogMessage.match_ready(matchmaking_queue[0][0], matchmaking_queue[1][0]))
            opsep = str(MmsResponse.MATCH_READY) + MMS_RESPONSE_CODE_ARGS_SEP
            msg = opsep + p2_addr[0] + " " + str(p2_addr[1])
            p1_socket.sendto(msg.encode(), p1_addr)
            msg = opsep + p1_addr[0] + " " + str(p1_addr[1])
            p2_socket.sendto(msg.encode(), p2_addr)

            matchmaking_queue.remove(p1)
            matchmaking_queue.remove(p2)

            p1_socket.close()
            p2_socket.close()

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
                server_socket.sendto(str(MmsResponse.IN_QUEUE).encode(), addr)
                print(LogMessage.queued(username))
            else:
                server_socket.sendto(
                    str(MmsResponse.USER_NOT_AUTHENTICATED).encode(), addr
                )
                print(LogMessage.queueing_failed(username))
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
                server_socket.sendto(str(MmsResponse.OUT_OF_QUEUE).encode(), addr)
                print(LogMessage.unqueued(username))
            else:
                server_socket.sendto(
                    str(MmsResponse.USER_NOT_AUTHENTICATED).encode(), addr
                )
                print(LogMessage.unqueueing_failed(username))


if __name__ == "__main__":
    main()
