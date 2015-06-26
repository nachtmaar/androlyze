
# encoding: utf-8

from __future__ import absolute_import

__author__ = "Nils Tobias Schmidt"
__email__ = "schmidt89 at informatik.uni-marburg.de"

from multiprocessing import Value, RLock

from androlyze.log.Log import log
from celery import current_app as app

class TaskCollection(object):
    ''' Collection of tasks (by id) '''

    def __init__(self, total_cnt_apks):
        super(TaskCollection, self).__init__()
        self.__task_ids = []
        self.__send_tasks = Value('i', 0, lock = RLock())
        self.__total_cnt_apks = total_cnt_apks

    def get_total_cnt_apks(self):
        return self.__total_cnt_apks

    def set_total_cnt_apks(self, value):
        self.__total_cnt_apks = value

    def del_total_cnt_apks(self):
        del self.__total_cnt_apks

    def inc_send_tasks(self):
        with self.send_tasks.get_lock():
            self.send_tasks.value += 1

    def get_send_tasks(self):
        return self.__send_tasks

    def set_send_tasks(self, value):
        self.__send_tasks = value

    def del_send_tasks(self):
        del self.__send_tasks

    def get_task_ids(self):
        return self.__task_ids

    def set_task_ids(self, value):
        self.__task_ids = value

    def del_task_ids(self):
        del self.__task_ids

    def __str__(self):
        return str(self.task_ids)

    def __repr__(self):
        return repr(self.task_ids)

    task_ids = property(get_task_ids, set_task_ids, del_task_ids, "list<str> - List of task ids")
    send_tasks = property(get_send_tasks, set_send_tasks, del_send_tasks, "Value(int) : Number of send tasks (shared memory)")
    total_cnt_apks = property(get_total_cnt_apks, set_total_cnt_apks, del_total_cnt_apks, "int : total number of apks to analyze")

    def revoke_all(self, *args, **kwargs):
        ''' Revoke tasks '''
        log.warn("will revoke %d tasks", len(self.task_ids))
        app.control.revoke(self.task_ids, *args, **kwargs)

    def all_tasks_published(self):
        ''' Check if all tasks have been published '''
        return self.send_tasks == self.total_cnt_apks
