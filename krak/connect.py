import json
from twisted.internet import reactor, endpoints
from twisted.protocols import basic


class KrakServerClient(basic.LineReceiver):

    def __init__(self, objects):
        self.objects = objects
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

    #def dataReceived(self, data):
    #    "As soon as any data is received, write it back."
    #    print('Server said:', data)

    def connectionLost(self, reason):
        print(reason)
        reactor.stop()

    def connectionFailred(self, reason):
        print('connection failed:', reason)


def send(objects):
    # server = xmlrpc.client.ServerProxy('http://0.0.0.0:1235')
    # server.construct([obj.serialize() for obj in objects])
    endpoint = endpoints.TCP4ClientEndpoint(reactor, '0.0.0.0', 1235)
    endpoints.connectProtocol(
        endpoint, KrakServerClient(objects))
    reactor.run()
