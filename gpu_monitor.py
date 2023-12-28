import json
import argparse
from flask import Flask, render_template
# import paramiko
from fabric import Connection
from fabric import task

# Create an argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--no-proxy", action="store_true", help="Disable proxy")

# Parse the command-line arguments
args = parser.parse_args()

# Import the appropriate configuration file based on the command-line argument
if args.no_proxy:
    from conf_no_proxy import *
else:
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
# def get_gpu_usage(connection):
#     output = connection.run("nvidia-smi --query-gpu=name,memory.used,memory.total,memory.free,temperature.gpu,utilization.gpu --format=csv,noheader").stdout.strip()
#     try:
#         lines = output.split("\n")
#         usage = []
#         for idx, line in enumerate(lines):
#             data = line.strip().split(",")
#             name = data[0].strip()
#             memory_used = int(data[1].strip().split()[0])
#             memory_total = int(data[2].strip().split()[0])
#             memory_free = int(data[3].strip().split()[0])
#             temperature = int(data[4].strip().split()[0])
#             utilization = int(data[5].strip().split()[0])
#             usage.append({'idx': idx, 'name': name, 'memory_used': memory_used, 'memory_total': memory_total, 'memory_free': memory_free, 'temperature': temperature, 'utilization': utilization})
#     except Exception as e:
#         print(e)
#         return "Error"
#     return usage

def get_gpu_usage(connection):
    output = connection.run("/home/jiayin/.local/bin/gpustat -cu --json").stdout.strip()
    output = json.loads(output)
    '''
        "gpus": [
        {
            "index": 0,
            "uuid": "GPU-c763845b-87a5-1d7b-e46d-5efb095d4451",
            "name": "NVIDIA GeForce RTX 2080 Ti",
            "temperature.gpu": 38,
            "fan.speed": 30,
            "utilization.gpu": 0,
            "utilization.enc": 0,
            "utilization.dec": 0,
            "power.draw": 18,
            "enforced.power.limit": 250,
            "memory.used": 1,
            "memory.total": 11264,
            "processes": [
                {
                    "username": "10001",
                    "command": "python",
                    "full_command": [
                        "/home/jibo/anaconda3/envs/open-mmlab/bin/python",
                        "-u",
                        "main_train_psnr_lr.py",
                        "--local_rank=0",
                        "--opt",
                        "options/lr_swinir/swinir_a00_b031_roicenter2400_x2.json",
                        "--dist",
                        "True"
                    ],
                    "gpu_memory_usage": 8965,
                    "cpu_percent": 99.4,
                    "cpu_memory_usage": 4158091264,
                    "pid": 1654093
                }
            ]
        },
    '''
    try:
        usage = []
        # user_ids = set()
        for gpu in output['gpus']:
            idx = gpu['index']
            name = gpu['name']
            memory_used = int(gpu['memory.used'])
            memory_total = int(gpu['memory.total'])
            memory_free = memory_total - memory_used
            temperature = int(gpu['temperature.gpu'])
            utilization = int(gpu['utilization.gpu'])
            processes = []
            if len(gpu['processes']) > 0:
                for proc in gpu['processes']:
                    username = proc['username']
                    if username.isdigit():
                        # user_ids.add(username)
                        username = connection.run(f"id -nu {username}").stdout.strip()
                    full_command = ' '.join(proc['full_command'])
                    gpu_memory_usage = int(proc['gpu_memory_usage'])
                    processes.append({'username': username, 'full_command': full_command, 'gpu_memory_usage': gpu_memory_usage})
            usage.append({'idx': idx, 'name': name, 'memory_used': memory_used, 'memory_total': memory_total, 'memory_free': memory_free, 'temperature': temperature, 'utilization': utilization, 'processes': processes})
    except Exception as e:
        print("Error", e, "Output", output)
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
    return render_template('gpu_status.html', gpu_info=gpu_info)

if __name__ == '__main__':
    app.run(debug=False)
