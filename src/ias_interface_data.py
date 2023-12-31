"""
ias_interface_data.py

Authors: Thiago Ferronatto and Yuri Moraes Gavilan

This file contains data about the boundary of the information and authentication
server.
"""


IAS_ADDRESS = "127.0.0.1"
IAS_PORT = 1234

IAS_AUTH_TOKEN_SIZE = 16
IAS_AUTH_TOKEN_HEX_STR_LENGTH = 2 * IAS_AUTH_TOKEN_SIZE
IAS_RESPONSE_CODE_SIZE = 8
IAS_OPCODE_SIZE = 8
IAS_OPCODE_ARGS_SEP = "|||"
IAS_RESPONSE_CODE_ARGS_SEP = "|||"


class IasOpCode:
    AUTHENTICATE = 0
    REGISTER = 1
    VERIFY = 2
    LOGOUT = 3
    LIST_USERS = 4


class IasResponse:
    LOGIN_SUCCESSFUL = 0
    WRONG_CREDENTIALS = 1
    USER_NOT_FOUND = 2
    REGISTRATION_SUCCESSFUL = 3
    DATABASE_ERROR = 4
    VERIFICATION_SUCCESSFUL = 5
    VERIFICATION_FAILED = 6
    USER_ALREADY_EXISTS = 7
    LOGIN_FAILED = 8
    LOGOUT_SUCCESSFUL = 9
    LOGOUT_FAILED = 10
    USER_LIST = 11
