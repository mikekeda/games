import json
from django.utils.log import ServerFormatter


class LogFormatter(ServerFormatter):
    """ Extend ServerFormatter to warp logs into json.dumps. """

    def format(self, record):
        record.msg = record.msg.replace('"', "")
        return json.dumps(super().format(record))
