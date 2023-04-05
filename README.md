# gpu_monitor
A gpu monitor script to monitor gpu uages across multiple servers in one single webpage, using ssh to access the data.

## Usage

1. Install dependencies if needed:
    ```sh
    pip install fabric flask
    ```
2. Create a `conf.py` file to store ssh info of the remote servers. The required date structure is described in `gpu_monitor.py`. Support ProxyJump if you provide `proxy`, but not necessary.
3. Run:
    ```sh
    python gpu_monitor.py
    ```
