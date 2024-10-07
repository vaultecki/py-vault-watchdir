# import time module, Observer, FileSystemEventHandler
import time
import watchdog.observers
import watchdog.events
import PySignal
import threading


class VaultWatch:
    """
    watch directory for changes
    """
    def __init__(self, watch_directory, sleep_time):
        """
        :param watch_directory: directory path
        :type watch_directory: str
        :param sleep_time:  sleep time
        :type sleep_time: int
        """
        self.directory = watch_directory
        self.sleep_time = sleep_time
        self.observer = watchdog.observers.Observer()
        self.stop_flag = False
        self.event_handler = None
        threading.Timer(0.2, self.__start).start()

    def __start(self):
        # create handler,
        self.event_handler = Handler()
        self.observer.schedule(self.event_handler, self.directory, recursive=True)
        # start observer thread
        self.observer.start()
        try:
            while not self.stop_flag:
                time.sleep(self.sleep_time)
        except:
            self.observer.stop()
            print("Observer Stopped")

        # self.observer.join()

    def stop(self):
        self.stop_flag = True


class Handler(watchdog.events.FileSystemEventHandler):
    """
    create pysignal signals for changes
    """

    create_signal = PySignal.ClassSignal()
    dir_create_signal = PySignal.ClassSignal()
    change_signal = PySignal.ClassSignal()
    dir_change_signal = PySignal.ClassSignal()
    delete_signal = PySignal.ClassSignal()
    dir_delete_signal = PySignal.ClassSignal()

    # @staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            if event.event_type == "created":
                self.dir_create_signal.emit(event.src_path)
            elif event.event_type == 'modified':
                self.dir_change_signal.emit(event.src_path)
            elif event.event_type == 'deleted':
                self.dir_delete_signal.emit(event.src_path)
        # creating three different functions
        elif event.event_type == 'created':
            # Event is created, you can process it now
            # print("Watchdog received file created - % s." % event.src_path)
            self.create_signal.emit(event.src_path)
        elif event.event_type == 'modified':
            # Event is modified, you can process it now
            # print("Watchdog received file modified - % s." % event.src_path)
            self.change_signal.emit(event.src_path)
        elif event.event_type == 'deleted':
            # print("Watchdog received file deleted - % s." % event.src_path)
            self.delete_signal.emit(event.src_path)


def function_test(path_string):
    print("receved path: {}".format(path_string))


if __name__ == '__main__':
    print("start watch directory")
    watch = VaultWatch("C:\\temp", 5)
    time.sleep(2)
    print("connect test function - create")
    watch.event_handler.create_signal.connect(function_test)
    time.sleep(5)
    print("stop watching")
    watch.stop()
