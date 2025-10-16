# network.py

import socket
import threading
import queue
import time
from settings import DISCOVERY_PORT, GAME_PORT, DISCOVERY_MESSAGE

class SharedData:
    def __init__(self):
        self.found_hosts = {}
        self.is_running = True
        self.connection_established = False

class Server:
    def __init__(self, q: queue.Queue, client_instance, shared_data: SharedData, port: int):
        self.q = q
        self.client = client_instance
        self.shared_data = shared_data
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', port))
        
        # ★★★ 1秒のタイムアウトを設定 ★★★
        # これにより、recvfromが永遠に待機するのを防ぎ、is_runningフラグを確認できるようになる
        self.sock.settimeout(1.0)

        self.my_port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.thread.start()

    def receive_loop(self):
        while self.shared_data.is_running:
            try:
                msg_bytes, cli_addr = self.sock.recvfrom(1024)
                msg_str = msg_bytes.decode('utf-8')
                
                if self.client.target_address is None and msg_str.startswith("HELLO:"):
                    try:
                        client_listening_port = int(msg_str.split(':')[1])
                        self.client.target_address = (cli_addr[0], client_listening_port)
                        self.shared_data.connection_established = True
                        self.q.put("CONNECTION_OK")
                    except (ValueError, IndexError):
                        print(f"不正なHELLOメッセージ: {msg_str}")
                else:
                    self.q.put(msg_str)
            
            except socket.timeout:
                # タイムアウトは正常。ループを続けて is_running をチェックする
                continue
            except Exception:
                break
        self.sock.close()
        print("サーバーソケットを閉じました。")

class Client:
    def __init__(self, q: queue.Queue, target_address=None):
        self.q = q
        self.target_address = target_address

    def send(self, msg: str):
        if self.target_address:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.sendto(msg.encode('utf-8'), self.target_address)

def broadcast_presence(shared_data: SharedData):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_address = ('<broadcast>', DISCOVERY_PORT)
    while shared_data.is_running and not shared_data.connection_established:
        message = f"{DISCOVERY_MESSAGE}:{GAME_PORT}".encode('utf-8')
        sock.sendto(message, broadcast_address)
        time.sleep(1)
    sock.close()
    print("ブロードキャストスレッドを停止しました。")

def listen_for_hosts(shared_data: SharedData):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', DISCOVERY_PORT))
    sock.settimeout(1.0)
    while shared_data.is_running and not shared_data.connection_established:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8')
            if message.startswith(DISCOVERY_MESSAGE):
                parts = message.split(':')
                port = int(parts[1])
                host_ip = addr[0]
                shared_data.found_hosts[host_ip] = port
        except socket.timeout:
            continue
        except Exception as e:
            print(f"探索エラー: {e}")
            break
    sock.close()
    print("ホスト探索スレッドを停止しました。")