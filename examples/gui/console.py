# from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget


class QIPythonWidget(RichJupyterWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
