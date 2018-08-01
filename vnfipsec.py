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

def config_path(config, path):
    return (config.get_path_prefix() / Path(path)).as_posix()


def template_charon(env, config):
    template = env.get_template('charon.conf.jinja2')
    template.stream(vti=config.get().get_bool('vti')).dump(config_path(config, 'strongswan.d/charon.conf'))


def template_farp(env, config):
    template = env.get_template('farp.conf.jinja2')
    template.stream(load_module=config.v.get_bool('vti')).dump(config_path(config, 'strongswan.d/charon/farp.conf'))


def template_configurations(env, config):
    template_charon(env, config)
    template_farp(env, config)


def start_strongswan():
    return None

def create_session(socket_path):
    sock = socket.socket(socket.AF_UNIX)
    sock.connect(socket_path)
    session = vici.Session(sock)
    return session


def setup_connections(session: vici.Session, connections: dict):
    for key, value in connections.items():
        msg = session.load_conn({key: value})
        print(msg)


def setup_secrets(session: vici.Session, secrets: dict):
    for key, value in secrets.items():
        struct = {'id': key, 'type': value['type'], 'owners': value['ids'], 'data': value['key']}
        msg = session.load_shared(struct)
        print(msg)


def start_all_conns(session: vici.Session, connections: dict):
    for key, value in connections.items():
        for child in value['children'].keys():
            struct = {'child': child, 'ike': key, 'timeout': 500}
            print(struct)
            msg = session.initiate(struct)
            for i in msg:
                print(i)

def terminate_all_active_conns(session: vici.Session):
    child_sas = set()
    for i in session.list_sas():
        for key, value in i.items():
            for c, value in value['child-sas'].items():
                sa = value['name']
                child_sas.add((key, sa))
    print(child_sas)
    for sa in child_sas:
        for line in session.terminate({'child': sa[1], 'ike': sa[0], 'timeout': 500}):
            print(line)


def termination_handler(signum, frame):
    print('killing me softly', signum)
    global running
    running = False


if __name__ == '__main__':
    config = configuration.Configuration()
    # default_config = "config/defaults.yaml"
    # config.update_configuration_yaml(Path(default_config))
    print(config)

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

    while True:
        time.sleep(1)
        print('sleep')
        if not running:
            terminate_all_active_conns(vici_session)
            exit(0)
