#!/usr/bin/env python3

import re
import os
import sys
import socket
import logging
from http import cookies
from optparse import OptionParser
from websockify import WebSocketProxy
from websockify import ProxyRequestHandler


CERT = None


parser = OptionParser()
parser.add_option("-v",
                  "--verbose",
                  dest="verbose",
                  action="store_true",
                  help="Verbose mode",
                  default=False)

parser.add_option("-d",
                  "--debug",
                  dest="debug",
                  action="store_true",
                  help="Debug mode",
                  default=False)

parser.add_option("-H",
                  "--host",
                  dest="host",
                  action="store",
                  help="Listen host",
                  default='0.0.0.0')

parser.add_option("-p",
                  "--port",
                  dest="port",
                  action="store",
                  help="Listen port",
                  default=6080)

parser.add_option("-c",
                  "--cert",
                  dest="cert",
                  action="store",
                  help="Certificate file path",
                  default='cert.pem')

(options, args) = parser.parse_args()

FORMAT = "%(asctime)s - %(name)s - %(levelname)s : %(message)s"
if options.debug:
    logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    options.verbose = True
elif options.verbose:
    logging.basicConfig(level=logging.INFO, format=FORMAT)
else:
    logging.basicConfig(level=logging.WARNING, format=FORMAT)


def get_conn_data(token):
    port = None
    temptoken = token.split('-', 1)
    uuid = temptoken[1]
    try:
        conn = wvmInstance(name)
        port = conn.get_console_port()
    except Exception as e:
        logging.error(
            f'Fail to retrieve console connection infos for token {token} : {e}')
        raise
    return 'localhost', port


class CompatibilityMixIn(object):
    def _new_client(self, daemon, socket_factory):
        cookie = cookies.SimpleCookie()
        if not hasattr(self.headers, 'cookie'):
            logging.error('- Cookie not found')
            return False
        cookie.load(self.headers.get('cookie'))
        if 'token' not in cookie:
            logging.error('- Token not found')
            return False
        token = cookie.get('token').value
        console_host, console_port = get_conn_data(token)

        cnx_debug_msg = "Connection Info :\n"
        cnx_debug_msg += f"  - console_host : '{console_host}'\n"
        cnx_debug_msg += f"  - console_port : '{console_port}'"
        logging.debug(cnx_debug_msg)

        # Direct access
        tsock = socket_factory(console_host, console_port, connect=True)

        if self.verbose and not daemon:
            print(self.traffic_legend)

        # Start proxying
        try:
            self.vmsg(f"{console_host}:{console_port}: Websocket client or Target closed")
            self.do_proxy(tsock)
        except Exception:
            raise


class NovaProxyRequestHandler(ProxyRequestHandler, CompatibilityMixIn):
    def msg(self, *args, **kwargs):
        self.log_message(*args, **kwargs)

    def vmsg(self, *args, **kwargs):
        if self.verbose:
            self.msg(*args, **kwargs)

    def new_websocket_client(self):
        """
        Called after a new WebSocket connection has been established.
        """
        # Setup variable for compatibility
        daemon = self.server.daemon
        socket_factory = self.server.socket

        self._new_client(daemon, socket_factory)


if __name__ == '__main__':
    # Create the WebSocketProxy with NovaProxyRequestHandler handler
    server = WebSocketProxy(RequestHandlerClass=NovaProxyRequestHandler,
                            listen_host=options.host,
                            listen_port=options.port,
                            source_is_ipv6=False,
                            verbose=options.verbose,
                            cert=options.cert,
                            key=None,
                            ssl_only=False,
                            daemon=False,
                            record=False,
                            web=False,
                            traffic=False,
                            target_host='ignore',
                            target_port='ignore',
                            wrap_mode='exit',
                            wrap_cmd=None)
    server.start_server()
