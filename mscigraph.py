import socket
import datetime
import threading
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("Agg")
import matplotlib.backends.backend_agg as agg
import ssl
from time import sleep

import pygame

"""
DataVisBot for SARP 2021
Adam Furman

You need to have
"pip install matplotlib pygame" to use this on python3
"""

class IRCClient(object):
    def __init__(self, server: str, port: int, uname: str, pwd: str, channel: str):
        self.server = server
        self.port = port
        self.uname = uname
        self.password = pwd
        self.channel = channel

    def connect(self):
        print("[I] Connecting.")
        ssl_ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
        insec_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = ssl_ctx.wrap_socket(insec_soc)
        self.socket.connect((self.server, self.port))

        self.joined = False
        self.cmd("PASS", self.password)
        self.cmd("NICK", self.uname)
        self.cmd("USER", "{} * * :{}".format(self.uname, self.uname))
        while not self.joined:
            resp = self.receive().rstrip()
            if "PING" in resp:
                self.cmd("PONG", resp.split(":")[1])
            if "MODE " + self.uname in resp:
                print("[I]  Joining channel.")
                self.cmd("JOIN", self.channel)
            if "433" in resp:
                print("[E] Username is already taken")
                self.socket.close()
                return False
            if "366" in resp:
                print("[I] Joined successfully.")
                self.joined = True
        return True

    def receive(self) -> str:
        return self.socket.recv(512).decode("utf-8")

    def cmd(self, cmd: str, data: str):
        self.socket.send(
            "{} {}\r\n".format(cmd, data).encode("utf-8")
        )

    def message(self, text: str):
        print("[I] Sending to {}: {}".format(self.channel, text))
        self.cmd(
            "PRIVMSG {}".format(self.channel),
            ":" + text
        )

    def close(self):
        self.cmd("QUIT", "Offline.")
        self.socket.close()
        self.joined = False

class DataCollector(object):
    def __init__(self, vars: list):
        self.variables = [v.upper() for v in vars]
        self.data = {v : ([], []) for v in self.variables}
        self.start = datetime.datetime.now()

    def collect(self, var, val):
        try:
            val = float(val)
            var = var.upper()
            if var in self.data.keys():
                self.data[var][0].append((datetime.datetime.now() - self.start).total_seconds())
                self.data[var][1].append(val)
                print("[D] {}: {} = {}".format(self.data[var][0][-1], var, self.data[var][1][-1]))
            else:
                print("[W] Unrecognized variable {}".format(var))
        except:
            print("[W] Unable to log point ({}, {})".format(var, val))

    def process(self, data):
        print("[I] {}".format(data))
        data = " " + data
        for chunk in data.split(","):
            found_vars = list(sorted([v for v in self.variables if chunk.find(" " + v) != -1], key=len))
            if len(found_vars) > 0:
                var = found_vars[-1]
                if chunk.find(var) != -1:
                    words = chunk.split()
                    for word in words:
                        if word.find(var) != -1: continue
                        try:
                            val = float("".join([c for c in word if c.isdigit() or c=="."]))
                            self.collect(var, val)
                            break
                        except ValueError:
                            pass

    def monitor(self, client):
        print("[I] Monitor starting.")
        while client.joined:
            resp = client.receive()
            if resp:
                data = resp.rstrip().split(":")
                if "PING" in data[0]:
                    client.cmd("PONG", ":"+data[1])
                    continue
                #user = data[0].split("!")[0]
                try:
                    content = data[2].strip().upper()
                    self.process(content)
                except:
                    print("[W] Failed to process: {}".format(resp))
                
        print("[I] Monitor quit.")


class Visualizer(object):
    def __init__(self, collector, interval=0.5, time_xscale=120):
        self.coll = collector
        self.interval = interval
        self.xscale = time_xscale

        self.fig, self.axs = plt.subplots(len(self.coll.variables), 1, figsize=(8, (2 * len(self.coll.variables))))
        self.fig.tight_layout()
        self.generate()

        pygame.init()
        pygame.display.set_caption("SARP DC-8 Visualizer")
        self.img_scalef = (pygame.display.Info().current_h * 0.8) / self.image_size[1]
        self.screen = pygame.display.set_mode((int(self.image_size[0] * self.img_scalef), int(self.image_size[1] * self.img_scalef)), pygame.RESIZABLE)

    def render(self):
        img = pygame.image.fromstring(self.image_data, self.image_size, "RGB")
        img = pygame.transform.scale(img, (self.screen.get_width(), self.screen.get_height()))
        self.screen.blit(img, (0, 0))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return False
        return True
    
    def generate(self, render=False):
        for i, ax in enumerate(self.axs):
            var = self.coll.variables[i]
            ax.set_title(var)

            t_now = (datetime.datetime.now() - self.coll.start).total_seconds()
            if t_now <= self.xscale:
                ax.set_xlim([0, t_now])
            else:
                ax.set_xlim([t_now - self.xscale, t_now])
            ax.set_ylim([0, max(max(self.coll.data[var][1] if len(self.coll.data[var][1]) > 0 else [0]) * 1.2, 1)])
            ax.plot(self.coll.data[var][0], self.coll.data[var][1], color="b")

        canvas = agg.FigureCanvasAgg(self.fig)
        canvas.draw()
        renderer = canvas.get_renderer()
        self.image_data = renderer.tostring_rgb()
        self.image_size = canvas.get_width_height()

    def run(self):
        while self.render():
            self.generate()
            sleep(self.interval)

if __name__ == "__main__":
    client = IRCClient(
        "asp-interface.info",
        6668,
        "datavisbot",
        "t@lksci3nc3",
        "#SARP2021"
    )
    coll = DataCollector(
        ["CH4", "CO", "NOX", "HCHO", "O3"]
    )
    vis = Visualizer(coll, 1, 300)

    client.connect()
    client.message("DataVisBot is collecting: {}".format(", ".join(coll.variables)))

    monitor_th = threading.Thread(target=coll.monitor, args=(client,))
    monitor_th.daemon = True
    monitor_th.start()

    try:
        vis.run()
    except KeyboardInterrupt:
        pass
    client.close()
