from fabric import api
from fabric.contrib.project import upload_project
from fabric.contrib import files
from fabric.operations import reboot
from fabric.decorators import hosts

from deployment import config
from rendering import render_to_file


api.env.hosts = config.hosts
api.env.user = config.user
api.env.password = config.password


def add_line_if_absent(line, file):
    api.sudo("grep -q -F '{line}' {file} || echo '{line}' >> {file}".format(**locals()))


def update_apt():
    with api.settings(prompts={'Do you want to continue [Y/n]? ': 'Y'}):
        api.sudo('apt-get update')
        api.sudo('apt-get upgrade -y')
        api.sudo('apt-get dist-upgrade')


def install_python3_prereqs():
    with api.settings(prompts={'Do you want to continue [Y/n]? ': 'Y'}):
        api.sudo('apt-get install build-essential libncursesw5-dev libgdbm-dev libc6-dev')
        api.sudo('apt-get install zlib1g-dev libsqlite3-dev tk-dev')
        api.sudo('apt-get install libssl-dev openssl')
        api.sudo('apt-get install nginx')


def fetch_get_pip_script():
    if not files.exists('/get-pip.py'):
        api.run('wget https://bootstrap.pypa.io/get-pip.py')


def install_pip3():
    api.sudo('python3.5 get-pip.py')


def install_pip2():
    api.sudo('python get-pip.py')


def install_python3():
    if not files.exists('/Python-3.5.0.tgz'):
        api.run('wget https://www.python.org/ftp/python/3.5.0/Python-3.5.0.tgz')
    if not files.exists('/Python-3.5.0'):
        api.run('tar -zxvf Python-3.5.0.tgz')

    with api.cd('Python-3.5.0'):
        api.run('./configure')
        api.run('make')
        api.sudo('make install')


def install_requirements():
    api.sudo('pip3.5 install -r rpi/requirements.txt')


def install_supervisor():
    api.sudo('pip install supervisor')


def update_boot_file():
    add_line_if_absent('dtoverlay=w1-gpio', '/boot/config.txt')


def update_iptables():
    api.sudo('iptables -A INPUT -p tcp --dport {} -j ACCEPT'.format(config.redirect_port))
    api.sudo('iptables -A PREROUTING -t nat -p tcp --dport {} -j REDIRECT --to-port {}'.format(config.redirect_port,
                                                                                               config.proxy_port))


@hosts('localhost')
def render_templates():
    render_to_file('supervisord.conf.j2', 'supervisord.conf', **config.__dict__)
    render_to_file('nginx.conf.j2', 'nginx.conf', **config.__dict__)


def full_deploy():
    update_apt()
    install_python3_prereqs()
    install_python3()
    fetch_get_pip_script()
    install_pip3()
    install_pip2()
    render_templates()
    upload_project(remote_dir=config.remote_dir)
    install_requirements()
    install_supervisor()
    update_boot_file()
    reboot()
    update_iptables()


def update():
    render_templates()
    upload_project(remote_dir=config.remote_dir)


def start():
    with api.cd('rpi'):
        api.run('supervisord -c supervisord.conf')


def stop():
    api.run('kill -s SIGTERM `cat /tmp/supervisord.pid`')


def update_and_restart():
    try:
        stop()
    finally:
        update()
        start()
