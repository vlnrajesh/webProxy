#!/usr/bin/env python
try:
    from logging.handlers import RotatingFileHandler
    import os
    import sys
    from urlparse import urlparse
    import thread
    import socket
    import logging
except ImportError, err:
    print err

MAX_CONNECTIONS = 200
MAX_DATA_RECV = 99999
BLOCKED_SITES=['www.serviceaide.com']
class MyCustomException(Exception):
    pass

def logger_initalizer(filename):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # Console logging
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.INFO)
    _formatter = logging.Formatter("%(message)s")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    # File logging
    # _handler=logging.FileHandler(filename,'a',encoding=None,delay='true')
    _handler=RotatingFileHandler(filename,'a',maxBytes=1048576,encoding=None,backupCount=2,delay='true')
    _handler.setLevel(logging.DEBUG)
    _formatter=logging.Formatter\
        ("[%(asctime)s] [%(levelname)-6s] --- %(message)s (%(filename)s:%(lineno)s)", "%d-%m-%Y %H:%M:%S")
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)


def proxy_initializer(host,port):
    try:
        _socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        logging.debug("Binding the socket to %s and %s "%(host,port))
        _socket.bind((host,port))
        _socket.listen(MAX_CONNECTIONS)
        while 1:
            if _socket:
                _conn,_client_addr = _socket.accept()
                thread.start_new_thread(proxy_fork,(_conn,_client_addr))
    except IOError,err:
        logging.fatal("Socket open failes : %s" %err)
    except Exception,err:
        logging.fatal(err)
    finally:
        logging.info("Socket Closed and ending program")
        _socket.close()
        sys.exit(0)


def proxy_fork(conn,client_addr):
    try:
        _request = conn.recv(MAX_DATA_RECV)
        logging.debug("Forking connection to %s" %str(client_addr))
        _read_request=_request.split('\n')[0]
        logging.debug(_read_request)
        _url=_read_request.split(' ')[1]
        _url=urlparse(_url)
        (dest_url,dest_port)=(_url.hostname,_url.port)
        if dest_port is None: dest_port = 80
        logging.debug("Destination Url : %s" % dest_url)
        logging.debug("Destination Port: %s" % dest_port)
        if dest_url in BLOCKED_SITES:
            # raise IOError("%s is in Blocked list, hence not processing" %dest_url)
            raise MyCustomException()
        _client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        _client_socket.connect((dest_url,dest_port))
        _client_socket.send(_request)
        while 1:
            data = _client_socket.recv(MAX_DATA_RECV)
            if len(data)>0:
                conn.send(data)
            else:
                break
        conn.close()
        _client_socket.close()
    except IOError, err_fork:
        logging.fatal("Socket open failes for %s %s" % (dest_url,err_fork))
    except Exception, err_fork:
        logging.fatal(err_fork)
     # finally:
    #     _client_socket.close()


def main():
    try:
        logger_initalizer('messages.log')
        if len(sys.argv) < 2:
            _port=8080
            logging.warning("Port not defined,using default port : %s" % _port)
        else:
            _port = int(sys.argv[1])
        _host=''
        logging.info("Press Ctrl+C to terminate program")
        proxy_initializer(_host,_port)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
