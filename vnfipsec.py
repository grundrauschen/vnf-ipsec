#!/usr/bin/env python3
import configuration
from pathlib import Path
import subprocess
import socket
import vici
import signal, os, time

from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
import jinja2

running = True

import logging
from pythonjsonlogger import jsonlogger
import logs
logger = logging.getLogger(__name__)

def setup_root_logger():
    root_logger = logging.getLogger()
    logHandler = logging.StreamHandler()
    filter_attributes = ['args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
        'funcName', 'levelno', 'lineno', 'module',
        'msecs', 'pathname', 'process',
        'processName', 'relativeCreated', 'stack_info', 'thread', 'threadName']
    formatter = logs.CustomJsonFormatter(timestamp=True, reserved_attrs=filter_attributes)
    logHandler.setFormatter(formatter)
    root_logger.handlers = []
    root_logger.addHandler(logHandler)



def config_path(config, path):
    return (config.get_path_prefix() / Path(path)).as_posix()


def template_charon(env, config):
    logger.info("create config for charon")
    template = env.get_template('charon.conf.jinja2')
    template.stream(vti=config.get().get_bool('vti')).dump(config_path(config, 'strongswan.d/charon.conf'))


def template_farp(env, config):
    logger.info("create config for farp module")
    template = env.get_template('farp.conf.jinja2')
    template.stream(load_module=config.v.get_bool('vti')).dump(config_path(config, 'strongswan.d/charon/farp.conf'))


def template_configurations(env, config):
    logger.info("create configurations from templates")
    template_charon(env, config)
    template_farp(env, config)


def start_strongswan():
    return None

def create_session(socket_path):
    logger.info("connect to Strongswan via VICI interface")
    sock = socket.socket(socket.AF_UNIX)
    sock.connect(socket_path)
    session = vici.Session(sock)
    return session


def setup_connections(session: vici.Session, connections: dict):
    logger.info("add connections to strongswan")
    for key, value in connections.items():
        logger.info("add connection {}".format(key), extra={'connection': key})
        msg = session.load_conn({key: value})
        if msg:
            logger.info(msg)


def setup_secrets(session: vici.Session, secrets: dict):
    logger.info("add secrets to strongswan")
    for key, value in secrets.items():
        logger.info("add secret {}".format(key), extra={'connection': key})
        struct = {'id': key, 'type': value['type'], 'owners': value['ids'], 'data': value['key']}
        msg = session.load_shared(struct)
        if msg:
            logger.info(msg)


def start_all_conns(session: vici.Session, connections: dict):
    """
    :param session:
    :param connections:
    :return:
    """
    logger.info("establish all configured connections")
    for key, value in connections.items():
        for child in value['children'].keys():
            struct = {'child': child, 'ike': key, 'timeout': 500}
            msg = session.initiate(struct)
            for i in msg:
                log_strongswan_respone(i)


def terminate_all_active_conns(session: vici.Session):
    logger.info("terminate all active connections")
    child_sas = set()
    ike = set()
    for i in session.list_sas():
        for key, value in i.items():
            ike.add(key)
            if 'child-sas' in value:
                for c, value in value['child-sas'].items():
                    sa = value['name']
                    child_sas.add((key, sa))
    print(child_sas)
    for sa in child_sas:
        for line in session.terminate({'child': sa[1], 'ike': sa[0], 'timeout': 500}):
            log_strongswan_respone(line)
    for i in ike:
        for line in session.terminate({'ike': i, 'timeout': 500}):
            log_strongswan_respone(line)


def termination_handler(signum, frame):
    logger.info('killing me softly', extra={'signum': signum})
    global running
    running = False

def log_strongswan_respone(message):
    message['message'] = message['msg'].decode('utf-8')
    del message['msg']
    logger.info(message, extra={'component': 'strongswan'})

if __name__ == '__main__':
    setup_root_logger()
    config = configuration.Configuration()
    # default_config = "config/defaults.yaml"
    # config.update_configuration_yaml(Path(default_config))
    logger.info("current config", extra={'config': config.get_cleaned()})

    env = Environment(
        loader=PackageLoader('vnfipsec', 'templates'),
        # loader=FileSystemLoader('./templates'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template_configurations(env, config)

    strongswan_process = start_strongswan()

    vici_session = create_session(config.get().get_string('vnf_ipsec.socket_path'))
    setup_connections(vici_session, config.get().get('ipsec.connections'))

    setup_secrets(vici_session, config.get().get('ipsec.secrets'))

    start_all_conns(vici_session, config.get().get('ipsec.connections'))

    signal.signal(signal.SIGTERM, termination_handler)
    signal.signal(signal.SIGINT, termination_handler)

    logger.info("going into sleep mode")
    while True:
        time.sleep(1)
        if not running:
            terminate_all_active_conns(vici_session)
            exit(0)
