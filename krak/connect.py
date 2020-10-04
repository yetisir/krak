import json
import subprocess
import platform

from twisted.internet import reactor, endpoints
from twisted.protocols import basic

from . import mesh


class KrakServerClient(basic.LineReceiver):

    def __init__(self, objects):
        self.objects = [obj for obj in objects if isinstance(obj, mesh.Mesh)]
        super().__init__()

    def sendObjects(self):
        serialized_objects = json.dumps(
            [obj.serialize() for obj in self.objects])

        print(len(serialized_objects))
        self.sendLine(serialized_objects.encode())

    def connectionMade(self):
        self.sendObjects()
        self.transport.loseConnection()

    def connectionLost(self, reason):
        print(reason)
        reactor.stop()

    def connectionFailed(self, reason):
        print(reason)
        reactor.stop()


def send(host='render'):
    sanitized_host = ''.join(
        char for char in host if char.isalnum() or char == '.')

    packets_flag = '-n' if platform.system().lower() == 'windows' else '-c'

    command = ['ping', packets_flag, '1', sanitized_host]
    response = subprocess.call(command, stderr=subprocess.DEVNULL)
    if int(response) > 0:
        return

    endpoint = endpoints.TCP4ClientEndpoint(reactor, sanitized_host, 1235)
    endpoints.connectProtocol(
        endpoint, KrakServerClient(mesh.Mesh._registry))
    reactor.run()
