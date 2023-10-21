# Data about the boundary of the matchmaking server


MATCHMAKING_ADDRESS = "127.0.0.1"
MATCHMAKING_PORT = 1235

MMS_OPCODE_SIZE = 8
MMS_OPCODE_ARGS_SEP = "|||"
MMS_RESPONSE_CODE_SIZE = 8
MMS_RESPONSE_CODE_ARGS_SEP = "|||"
MMS_MAX_ARGS_SIZE = 1024


class MmsOpCode:
    MAKE_AVAILABLE = 0
    MAKE_UNAVAILABLE = 1
    ACCEPT_MATCH = 2
    DECLINE_MATCH = 3


class MmsResponse:
    MATCH_AVAILABLE = 0
    USER_NOT_AUTHENTICATED = 1
    FAILED_TO_ACCEPT = 2
    MATCH_READY = 3
    IN_QUEUE = 4
    OUT_OF_QUEUE = 5
    OTHER_PLAYER_DECLINED = 6
