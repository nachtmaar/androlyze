
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

############################################################
#---CLI Commands
############################################################

# available commands
COMMAND = "command"
COMMAND_IMPORT = "import"
COMMAND_ANALYZE = "analyze"
COMMAND_QUERY = "query"
COMMAND_SYNC = "sync"
COMMAND_EVAL = "eval"
# available commands for query
SUBCOMMAND_QUERY_IMPORT = "import"
SUBCOMMAND_QUERY_RESULT = "result"

COMMAND_DELETE = "delete"
COMMANDS_ALL = (COMMAND_ANALYZE, COMMAND_IMPORT,
                COMMAND_QUERY, COMMAND_SYNC,
                COMMAND_DELETE, COMMAND_EVAL)

# available commands for delete
SUBCOMMAND_DELETE_IMPORT = "import"
SUBCOMMAND_DELETE_RESULT = "result"