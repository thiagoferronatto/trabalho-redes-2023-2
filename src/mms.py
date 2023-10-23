"""
mms.py

Authors: Thiago Ferronatto and Yuri Moraes Gavilan

This file contains the functions for a game matchmaking server.

The server uses UDP sockets to communicate with the clients and TCP sockets to
communicate with the Information and Authentication Server (IAS). The server
maintains a matchmaking queue and a match list, and tries to create matches
between the players in the queue. The server also validates the users by sending
their tokens and usernames to the IAS. The server handles different types of
requests from the users based on the opcodes sent by them. The server also logs
the relevant messages using a logger object.
"""


from ias_interface_data import *
from mms_interface_data import *
from datetime import *
from logger import *
from socket import *
from style import *


MMS_LOG_FILE_NAME = "mms.log"
"""The name of the log file that records the messages from the MMS."""


class LogMessage:
    """
    A class that contains methods for generating log messages for the
    matchmaking server.
    """

    def server_available():
        return f"Servidor disponível pela porta {MATCHMAKING_PORT}."

    def match_available(player_1, player_2):
        return f"Partida(s) disponível(is). Pareando {player_1} com {player_2}."

    def declined_match(player_1, player_2):
        return f"Jogador {player_1} recusou a partida com {player_2}; expulsando {player_1} da fila."

    def match_ready(player_1, player_2):
        return f"Partida pronta entre {player_1} e {player_2}; enviando os dados de um para o outro."

    def queued(player_name):
        return f"Jogador {player_name} entrou na fila."

    def queueing_failed(player_name):
        return f"Jogador {player_name} quis entrar na fila, mas não estava autenticado."

    def unqueued(player_name):
        return f"Jogador {player_name} saiu da fila."

    def unqueueing_failed(player_name):
        return f"Jogador {player_name} quis sair da fila, mas não estava autenticado."

    def mm_list_given(player_name):
        return f"Jogador {player_name} recebeu uma lista de jogadores."

    def mm_list_request_failed(player_name):
        return f"Jogador {player_name} solicitou uma lista de jogadores, mas não estava autenticado."

    def match_list_given(player_name):
        return f"Jogador {player_name} recebeu uma lista de partidas em andamento."

    def match_list_request_failed(player_name):
        return f"Jogador {player_name} solicitou uma lista de partidas em andamento, mas não estava autenticado."

    def match_ended(player_name):
        return f"Jogador {player_name} reportou o fim de sua partida."

    def match_report_failed(player_name):
        return f"Jogador {player_name} tentou reportar o fim de uma partida, mas não estava autenticado."

    def unauthorized_user(player_name):
        return f"Usuário não autenticado {player_name} tentou acessar o servidor."


def valid_user(token, username):
    """
    Checks if a user is valid by sending a verification request to the
    Information and Authentication Server (IAS).

    Parameters
    ----------
    token : str
        The authentication token of the user.
    username : str
        The username of the user.

    Returns
    -------
    bool
        True if the user is valid, False otherwise.
    """
    auth_socket = socket()
    auth_socket.connect((IAS_ADDRESS, IAS_PORT))
    msg = str(IasOpCode.VERIFY) + IAS_OPCODE_ARGS_SEP + token + " " + username
    auth_socket.send(msg.encode())
    status = int(auth_socket.recv(IAS_RESPONSE_CODE_SIZE).decode())
    auth_socket.close()
    return status == IasResponse.VERIFICATION_SUCCESSFUL


def create_match():
    """
    Tries to create a match between the first two players in the matchmaking
    queue.

    Returns
    -------
    bool
        True if a match was successfully created, False otherwise.
    """
    assert len(matchmaking_queue) >= 2

    p1, p2 = matchmaking_queue[0], matchmaking_queue[1]
    p1_name, p2_name = p1[0], p2[0]
    p1_addr, p2_addr = p1[1], p2[1]

    logger.log(LogMessage.match_available(p1_name, p2_name), Logger.INFO)

    p1_socket = socket(AF_INET, SOCK_DGRAM)
    p2_socket = socket(AF_INET, SOCK_DGRAM)

    msg = str(MmsResponse.MATCH_AVAILABLE).encode()
    p1_socket.sendto(msg, p1_addr)
    p2_socket.sendto(msg, p2_addr)

    p1_decision = int(p1_socket.recv(MMS_OPCODE_SIZE).decode())
    p2_decision = int(p2_socket.recv(MMS_OPCODE_SIZE).decode())

    p1_declined, p2_declined = False, False

    if p1_decision == MmsOpCode.DECLINE_MATCH:
        logger.log(LogMessage.declined_match(p1_name, p2_name), Logger.WARNING)
        matchmaking_queue.remove(p1)
        p1_declined = True
    if p2_decision == MmsOpCode.DECLINE_MATCH:
        logger.log(LogMessage.declined_match(p2_name, p1_name), Logger.WARNING)
        matchmaking_queue.remove(p2)
        p2_declined = True

    if p1_declined and p2_declined:
        p1_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p1_addr)
        p2_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p2_addr)
    elif p1_declined:
        p1_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p1_addr)
        p2_socket.sendto(str(MmsResponse.OTHER_PLAYER_DECLINED).encode(), p2_addr)
    elif p2_declined:
        p2_socket.sendto(str(MmsResponse.FAILED_TO_ACCEPT).encode(), p2_addr)
        p1_socket.sendto(str(MmsResponse.OTHER_PLAYER_DECLINED).encode(), p1_addr)
    if p1_declined or p2_declined:
        p1_socket.close()
        p2_socket.close()
        return False

    logger.log(LogMessage.match_ready(p1_name, p2_name), Logger.INFO)
    opsep = str(MmsResponse.MATCH_READY) + MMS_RESPONSE_CODE_ARGS_SEP
    msg = opsep + p2_addr[0] + " " + str(p2_addr[1]) + " " + str(p1_addr[1])
    p1_socket.sendto(msg.encode(), p1_addr)
    msg = opsep + p1_addr[0] + " " + str(p1_addr[1])
    p2_socket.sendto(msg.encode(), p2_addr)

    p1_socket.close()
    p2_socket.close()

    match_list.append((p1, p2))

    matchmaking_queue.remove(p1)
    matchmaking_queue.remove(p2)

    return True


def queue(username, addr):
    """
    Adds a user to the matchmaking queue if they are not already in it.

    Parameters
    ----------
    username : str
        The username of the user.
    addr : tuple
        The address of the user's socket.

    Returns
    -------
    bytes
        A byte string representing the response code for being in queue.
    """
    if (element := (username, addr)) not in matchmaking_queue:
        matchmaking_queue.append(element)
    logger.log(LogMessage.queued(username), Logger.INFO)
    return str(MmsResponse.IN_QUEUE).encode()


def unqueue(username, addr):
    """
    Removes a user from the matchmaking queue if they are in it.

    Parameters
    ----------
    username : str
        The username of the user.
    addr : tuple
        The address of the user's socket.

    Returns
    -------
    bytes
        A byte string representing the response code for being out of queue.
    """
    if (element := (username, addr)) in matchmaking_queue:
        matchmaking_queue.remove(element)
    logger.log(LogMessage.unqueued(username), Logger.INFO)
    return str(MmsResponse.OUT_OF_QUEUE).encode()


def list_matches(username):
    """
    Returns a list of live matches that have been made by the matchmaking
    server.

    Parameters
    ----------
    username : str
        The username of the user who requested the list.

    Returns
    -------
    bytes
        A byte string representing the response code and the list of matches,
        each with two players' usernames, IP addresses and port numbers,
        separated by tabs, "vs" and newlines.
    """
    response = str(MmsResponse.MATCH_LIST) + MMS_RESPONSE_CODE_ARGS_SEP
    for match in match_list:
        p1, p2 = match[0], match[1]
        response += p1[0] + " @ " + p1[1][0] + ":" + str(p1[1][1])
        response += " vs "
        response += p2[0] + " @ " + p2[1][0] + ":" + str(p2[1][1])
        response += "\n"
    logger.log(LogMessage.match_list_given(username), Logger.INFO)
    return response.encode()


def end_match(username):
    """
    Ends a match that involves the given user and removes it from the match
    list.

    Parameters
    ----------
    username : str
        The username of the user who wants to end the match.

    Returns
    -------
    bytes
        A byte string representing the response code for ending the match.
    """
    for match in match_list:
        p1, p2 = match[0], match[1]
        if p1[0] == username or p2[0] == username:
            match_list.remove(match)
            break
    logger.log(LogMessage.match_ended(username), Logger.INFO)
    return str(MmsResponse.MATCH_ENDED).encode()


matchmaking_queue = []
match_list = []
logger = Logger(MMS_LOG_FILE_NAME)


def main():
    """
    Starts the matchmaking server and listens for requests from users.

    The server handles different types of requests based on the opcode sent by
    the user, validates the user by sending their token and username to the IAS,
    and maintains a matchmaking queue and a match list, and tries to create
    matches when possible.
    """
    server_socket = socket(AF_INET, SOCK_DGRAM)
    server_socket.bind(("", MATCHMAKING_PORT))

    logger.log(LogMessage.server_available(), Logger.INFO)

    while True:
        if len(matchmaking_queue) >= 2 and not create_match():
            continue

        buflen = MMS_OPCODE_SIZE + len(MMS_OPCODE_ARGS_SEP) + MMS_MAX_ARGS_SIZE
        data, addr = server_socket.recvfrom(buflen)
        opcode, args = data.decode().split(MMS_OPCODE_ARGS_SEP)
        token, username = args.split(" ")

        if not valid_user(token, username):
            server_socket.sendto(str(MmsResponse.USER_NOT_AUTHENTICATED).encode(), addr)
            logger.log(LogMessage.unauthorized_user(username), Logger.WARNING)
            continue

        opcode = int(opcode)

        if opcode == MmsOpCode.MAKE_AVAILABLE:
            server_socket.sendto(queue(username, addr), addr)
        elif opcode == MmsOpCode.MAKE_UNAVAILABLE:
            server_socket.sendto(unqueue(username, addr), addr)
        elif opcode == MmsOpCode.LIST_PLAYERS:
            pass  # operation no longer supported
        elif opcode == MmsOpCode.LIST_MATCHES:
            server_socket.sendto(list_matches(username), addr)
        elif opcode == MmsOpCode.MATCH_ENDED:
            server_socket.sendto(end_match(username), addr)


if __name__ == "__main__":
    main()
