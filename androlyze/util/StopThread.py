
# encoding: utf-8

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from threading import Event
import threading

class StopThread(threading.Thread):
    ''' Extends the `Thread` with an `Event` and the `terminate` method
    like the `multiprocessing` api offers it.
    
    Calling it will trigger the `Event`.
    Just implement your cleanup code for this event.
    '''
    
    def __init__(self, *args, **kwargs):
        super(StopThread, self).__init__(*args, **kwargs)
        self.shall_terminate_event = Event()
        
    def terminate(self):
        ''' Immitate the `processing` API and offer a way to do some clean up in the `Thread`. '''
        self.shall_terminate_event.set()        

    def shall_terminate(self):
        ''' Can be queried to know if the `Thread` shall do some cleanup '''
        return self.shall_terminate_event.is_set()