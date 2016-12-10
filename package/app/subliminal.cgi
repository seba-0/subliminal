#!/usr/bin/python
import logging
import logging.handlers 
import sys
from application.auth import requires_auth
from application.direct import Base
from flask import Flask, request, Response
from pyextdirect.api import create_api
from pyextdirect.router import Router
from wsgiref.handlers import CGIHandler
from flup.server.fcgi import WSGIServer

app = Flask('subliminal')

logfile = '/var/packages/subliminal/target/var/subliminal_cgi.log' 

@app.route('/direct/router', methods=['POST'])
@requires_auth(groups=['administrators'])
def route():
    logger = logging.getLogger()
    logger.debug(request)
    try:
        router = Router(Base)
        rsp = router.route(request.json or dict((k, v[0] if len(v) == 1 else v) for k, v in request.form.to_dict(False).iteritems()))
        logger.debug(rsp)
        return Response(rsp, mimetype='application/json')
    except Exception as inst:
        logger.error(inst)
        raise

@app.route('/direct/api')
@requires_auth(groups=['administrators'])
def api():
    logger = logging.getLogger()
    logger.debug('call /direct/router')
    return create_api(Base)

@app.route('/')
def ping():
    logger = logging.getLogger()
    logger.debug('call /')
    return Response('OK!', mimetype='plain/text')

def initLogging(file):
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=2097152, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s', datefmt='%m/%d/%Y %H:%M:%S'))
    root.handlers = [handler] 

if __name__ == '__main__':
    initLogging(logfile)
    logger = logging.getLogger()
    logger.debug('WSGI Server start.')
    #app.run(host='0.0.0.0', port=8080)
    CGIHandler().run(app)
    #WSGIServer(app).run()
    #WSGIServer(app, bindAddress='/tmp/subliminal_sock').run()
    #WSGIServer(app, bindAddress='/run/synoscgi.sock').run()
