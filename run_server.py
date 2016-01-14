from heater.server import run_server
from deployment.config import app_port


if __name__ == '__main__':
    run_server(port=app_port)
