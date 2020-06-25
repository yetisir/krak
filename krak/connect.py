import json
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
        #print('test')
        self.sendObjects()
        self.transport.loseConnection()

    def connectionLost(self, reason):
        print(reason)
        reactor.stop()

    def connectionFailed(self, reason):
        print(reason)
        reacton.stop()

def send(objects, host='paraview'):
    # server = xmlrpc.client.ServerProxy('http://0.0.0.0:1235')
    # server.construct([obj.serialize() for obj in objects])
    endpoint = endpoints.TCP4ClientEndpoint(reactor, host, 1235)
    endpoints.connectProtocol(
        endpoint, KrakServerClient(objects))

    reactor.run()
