from flask import Flask, render_template
# import paramiko
from fabric import Connection
from fabric import task
from conf import *

app = Flask(__name__)


# servers are imported from conf.py and are in the following structure:
# servers = {
#     's1': {
#         'host': 'xxxxx',
#         'port': 22,
#         'username': 'xxx',
#         'password': 'xxx',
#         'proxy': {
#             'host': 'xxx',
#             'port': 22,
#             'username': 'xxx',
#             'password': 'xxx',
#         }
#     },
#     's2': {
#         ...
#     },
# }
def get_gpu_usage(connection):
    output = connection.run("nvidia-smi --query-gpu=name,memory.used,memory.total,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader").stdout.strip()
    try:
        lines = output.split("\n")
        usage = []
        for line in lines:
            data = line.strip().split(",")
            name = data[0].strip()
            memory_used = int(data[1].strip().split()[0])
            memory_total = int(data[2].strip().split()[0])
            memory_free = int(data[3].strip().split()[0])
            temperature = int(data[4].strip().split()[0])
            utilization = int(data[5].strip().split()[0])
            usage.append({'name': name, 'memory_used': memory_used, 'memory_total': memory_total, 'memory_free': memory_free, 'temperature': temperature, 'utilization': utilization})
    except Exception as e:
        print(e)
        return "Error"
    return usage

@app.route('/')
def index():
    gpu_info = {}
    for server_name, server_info in servers.items():
        try:
            if 'proxy' in server_info:
                proxy_info = server_info['proxy']
                proxy_conn = Connection(
                    host=proxy_info['host'],
                    port=proxy_info['port'],
                    user=proxy_info['username'],
                    connect_kwargs={"password": proxy_info['password']}
                )
                conn = Connection(
                    host = server_info['host'],
                    port=server_info['port'],
                    user=server_info['username'],
                    connect_kwargs={"password": server_info['password']},
                    gateway=proxy_conn)
                gpu_info[server_name] = get_gpu_usage(conn)
            else:
                with Connection(
                    host=server_info['host'],
                    port=server_info['port'],
                    user=server_info['username'],
                    connect_kwargs={"password": server_info['password']}
                ) as conn:
                    gpu_info[server_name] = get_gpu_usage(conn)
        except Exception as e:
            print(e)
            gpu_info[server_name] = "Error getting GPU usage"
    print(gpu_info)
    return render_template('gpu_status.html', gpu_info=gpu_info)

if __name__ == '__main__':
    app.run(debug=True)
