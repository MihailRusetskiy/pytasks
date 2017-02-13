import os
import getpass
import subprocess
from cursesmenu import CursesMenu
from cursesmenu.items import FunctionItem
from collections import defaultdict


def read_config_file(path):
    hosts = []
    with open(path, 'rt') as f:

        is_host_entries = False
        for line in f:
            if line.startswith('Host '):
                is_host_entries = True
                host = defaultdict()
                host['Host'] = line.strip().split()[1]
                continue

            if not line.strip():
                if is_host_entries:
                    hosts.append(host)
                is_host_entries = False

            if is_host_entries:
                entries = line.strip().split()
                host[entries[0]] = entries[1]
        return hosts


def open_connection(hostname, user, identity_file_path):
    data = subprocess.Popen(["ssh", "-i"+identity_file_path, " {}@{}".format(user, hostname), 'ls']).communicate()


def show_menu(hosts):
    menu = CursesMenu("SSH config file viewer")

    for host in hosts:
        if '*' in host['Host']:
            continue
        host_id = host['Host']
        hostname = host['Hostname']
        user = host['User'] if 'User' in host else getpass.getuser()
        identity_file = host['IdentityFile'] if 'IdentityFile' in host else ''
        identity_file_path = os.path.expanduser(identity_file) if identity_file else os.path.expanduser("~/.ssh/id_rsa")
        menu.append_item(FunctionItem("{} ({}@{}) {}".format(host_id, user, hostname, identity_file), \
                                      open_connection, [host_id, user, identity_file_path]))
        open_connection(hostname, user, identity_file_path)

    menu.show()

hosts = read_config_file(os.path.expanduser('~/.ssh/config1'))
show_menu(hosts)
