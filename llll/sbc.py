# socket based communicator
import os,socket

# from https://stackoverflow.com/a/30375198
def int_to_bytes(x):
    return x.to_bytes(4, 'big')
def int_from_bytes(xbytes):
    return int.from_bytes(xbytes, 'big')

env_var_name = 'PARENT_PORT'

class sbc:
    def __init__(self,port=None,verbose=False):
        self.verbose = verbose

        # attempt to extract port number from environment variables
        if port is None:
            try:
                k = os.environ[env_var_name]
                port = int(k)
                # print(port)
            except Exception as e:
                # print('extraction failed',e)
                pass

        # if port is specified -> child
        # if port is not specified -> parent

        if port is None:
            self.is_parent=True
        else:
            self.is_parent=False

        # create socket and bind to an arbitary port
        sock = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
        self.sock = sock
        sock.bind(('localhost',0))
        bindaddr, bindport = sock.getsockname()

        # if parent, wait for child to connect
        if self.is_parent:
            self.port = bindport
            sock.listen()
            self.conn_ready = False
            if self.verbose:
                print('[sbc(parent)] listening on port',self.port)

        # if child, connect to the parent
        else:
            sock.connect(('localhost',port))
            self.conn = sock
            self.port = port
            if self.verbose:
                print('[sbc(child)] connecting to port',self.port,'from port',bindport)

    # wait for connection to establish if necessary.
    def readyup(self):
        # only parent(server) need to wait for incoming connection;
        # child(client) can connect whenever he want
        if self.is_parent:
            if not self.conn_ready:
                # block forever if child failed to connect to parent
                conn,address = self.sock.accept()
                self.conn = conn
                self.conn_ready = True

    # read bytearray from other partner blockingly
    def read(self):
        self.readyup()

        c = self.conn
        length = c.recv(4)
        if len(length)!=4:
            raise EOFError('EOF on read(), expect 4, got {}'.format(len(length)))
        length = int_from_bytes(length)

        content = bytearray() # efficient for concatenation
        remain = length
        while 1:
            temp = c.recv(remain)
            content += temp
            remain -= len(temp)

            if remain>0:
                continue
            elif remain<0:
                raise Exception('overread')
            else:
                return content

    # write bytearray to other partner blockingly
    def write(self,bytes):
        self.readyup()

        c = self.conn
        length = len(bytes)
        length_bytes = int_to_bytes(length)
        if c.send(length_bytes) != 4:
            raise EOFError('EOF on write()')
        if c.send(bytes) != length:
            raise EOFError('EOF on write()')
        return True

    # send/recv pickled objects
    def send(self,obj):
        import pickle
        bytes = pickle.dumps(obj)
        self.write(bytes)

    def recv(self):
        import pickle
        bytes = self.read()
        return pickle.loads(bytes)

    def __del__(self):
        self.conn.close()
