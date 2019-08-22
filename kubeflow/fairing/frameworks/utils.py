import socket
import json
import os
import time
import tempfile
import configparser
import logging

logger = logging.getLogger(__name__)


def parse_cluster_spec_env():
    """ parse cluster spec env variables"""
    env_config = os.environ.get('CLUSTER_SPEC') or os.environ.get('TF_CONFIG')
    cluster = None
    if env_config:
        env_config_json = json.loads(env_config)
        cluster = env_config_json.get('cluster')
    if not cluster:
        return [], []
    hosts = []
    ports = []
    for val in cluster.values():
        if not isinstance(val, list):
            raise ValueError("Expecting list type values in cluster spec dict. \
                             cluster spec: {}".format(env_config))
        for item in val:
            host, port = item.split(":")
            hosts.append(host)
            ports.append(port)
    ips = [nslookup(host) for host in hosts]

    # Finding the RANK of the current node using hostname or ip address of the current node
    cur_hostname = socket.gethostname()
    cur_host_ip = socket.gethostbyname(cur_hostname)
    if cur_hostname and cur_hostname in hosts:
        rank = hosts.index(cur_hostname)
    elif cur_host_ip and cur_host_ip in ips:
        rank = ips.index(cur_host_ip)
    else:
        print("Can't find rank for current host (hostname={}, \
              ip={})".format(cur_hostname, cur_host_ip))
        rank = 0

    return hosts, ips, ports, rank


def nslookup(hostname, retries=600):
    """Does nslookup for the hostname and returns the IPs for it.

    :param hostname:  hostname to be looked up
    :param retries:  Number of retries before failing. In autoscaled cluster,
                    it might take upto 10mins to create a new node so the default value
                    is set high.(Default value = 600)

    """
    last_exception = None
    for _ in range(retries):
        try:
            time.sleep(1)
            ais = socket.getaddrinfo(hostname, 0, 0, 0, 0)
            return ais[0][-1][0]
        except Exception as e:
            logger.info("not able to lookup ip for %s", hostname)
            last_exception = e
    if last_exception:
        raise last_exception #pylint:disable=raising-bad-type


def write_ip_list_file(file_name, ips, port=None):
    """write list of ips into a file

    :param file_name: fine name
    :param ips: list of ips
    :param port:  default port(Default value = None)

    """
    with open(file_name, 'w') as f:
        if port:
            content = ["{} {}".format(ip, port) for ip in ips]
            content.sort()
            f.write("\n".join(content))
        else:
            sorted_ips = ips.copy().sort()
            f.write("\n".join(sorted_ips))
        f.write("\n")


def load_properties_config_file(config_file):
    """load config from a file

    :param config_file: config file path

    """
    config_parser = configparser.ConfigParser(allow_no_value=True)
    with open(config_file, 'r') as f:
        # Hack to get config parser work with properties files
        buf = "[default]\n" + f.read()
        config_parser.read_string(buf)
        config = dict(config_parser.items(section="default"))
    return config


def save_properties_config_file(config, file_name=None):
    """save config into a file

    :param config: dictionary of give configs
    :param file_name:  path to config file(Default value = None)

    """
    if not file_name:
        _, file_name = tempfile.mkstemp()

    with open(file_name, 'w') as fh:
        content = []
        for k, v in config.items():
            if isinstance(v, bool):
                v = str(v).lower()
            content.append("{}={}".format(k, v))
        fh.write("\n".join(content))
        fh.write("\n")
    return file_name


def update_config_file(file_name, field_name, new_value):
    """update config file

    :param file_name: file name
    :param field_name: field name
    :param new_value: new value to be added/updated

    """
    config = load_properties_config_file(file_name)
    config[field_name] = new_value
    save_properties_config_file(config, file_name)


def scrub_fields(config, filed_names):
    """scrub fields in config

    :param config: config spec
    :param filed_names: name of fields

    """
    for field in filed_names:
        if field in config:
            config.pop(field)
            logger.info("Ignoring %s filed in the config", field)


def get_config_value(config, field_names):
    """get value for a config entry

    :param config:
    :param field_names:

    """
    buf = {}
    for field in field_names:
        if field in config:
            buf[field] = config.get(field)
    if len(buf.items()) > 1:
        raise RuntimeError(
            "More than one field alias is specified: {}".format(buf))
    if len(buf.items()) > 0: #pylint:disable=no-else-return,len-as-condition
        return list(buf.items())[0]
    else:
        return None, None


def init_lightgbm_env(config_file, mlist_file):
    """initialize env for lightgbm

    :param config_file: path to config path
    :param mlist_file: path to file to write ip list

    """
    hosts, ips, ports, rank = parse_cluster_spec_env()
    #print("Rank: {}".format(rank))
    if len(set(ports)) > 1:
        raise RuntimeError(
            "Expecting cluster spec to have same port for all instances/pods."
            " Ports: {}".format(ports))
    port = ports[0]
    write_ip_list_file(mlist_file, ips, port)
    update_config_file(config_file, "local_port", port)
    logger.info("Cluster setup:")
    for x, y, z in zip(hosts, ips, ports):
        logger.info("{}\t{}\t{}".format(x, y, z)) #pylint:disable=logging-format-interpolation
    return rank
