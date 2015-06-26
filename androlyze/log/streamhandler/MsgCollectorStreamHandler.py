
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from Queue import Empty
from logging import StreamHandler

class MsgCollectorStreamHandler(StreamHandler):
    ''' `StreamHandler` that collects stdout/stderr messages in a `Queue<bool,str> '''

    def __init__(self, msg_queue, is_stderr = False):
        '''
        Parameters
        ----------
        is_stderr : bool
            Indicate if logging to stdout.
        msg_queue : Queue<bool, str>
            Collect the messages in this queue
        '''
        super(MsgCollectorStreamHandler, self).__init__()
        self.is_stderr = is_stderr
        self.__msg_queuing = False
        self.msg_queue = msg_queue

    def get_msg_queue(self):
        return self.__msg_queue

    def set_msg_queue(self, value):
        self.__msg_queue = value

    def del_msg_queue(self):
        del self.__msg_queue

    def get_msg_queuing(self):
        return self.__msg_queuing

    msg_queuing = property(get_msg_queuing, None, None, "bool : If true collect msg in `self.msg_queue`")
    msg_queue = property(get_msg_queue, set_msg_queue, del_msg_queue, "Queue<bool, str> : Collect the log messages here.")

    def start_msg_queing(self):
        ''' Start putting messages into the queue '''
        self.__msg_queuing = True

    def stop_msg_queing(self):
        ''' Stop collection messages into the queue and clear it '''
        self.__msg_queuing = False

        # remove all elements
        try:
            while self.msg_queue.get(block = False):
                pass
        except Empty:
            pass

    def emit(self, record):
        """
        Emit a record.
        """
        try:
            msg = self.format(record)
            if self.msg_queuing:
                self.msg_queue.put((msg, self.is_stderr))

        except (KeyboardInterrupt, SystemExit):
            raise