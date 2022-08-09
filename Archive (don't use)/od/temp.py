from widgets.worker import Worker
from functions.od import RedPitaya
from PyQt5.QtCore import QThreadPool

threadpool = QThreadPool()
print("Multithreading with maximum %d threads" % threadpool.maxThreadCount())

def OD_connect_worker():
    worker = Worker(connectthis)
    worker.signals.finished.connect(lambda: print("This"))
    threadpool.start(worker)

def connectthis(progress_callback):
    rp = RedPitaya.RedPitaya()

OD_connect_worker()