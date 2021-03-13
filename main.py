import os

import requests
import yaml
import time


def getTimeStamp():
    return round(time.time() * 1000)


def yaml_dump(path, data):
    with open(path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, encoding='utf-8', allow_unicode=True)


class SubUrlNode:
    def __init__(self, site_name, sub_name, sub_url: str):
        self.site_name = site_name
        self.sub_name = sub_name
        self.sub_url = sub_url.replace("https%3A%2F%2F", "https://").replace("http%3A%2F%2F", "http://")
        self.tmp_store_path = "{}/{}_{}-{}.yaml".format(os.getcwd(), site_name, sub_name, getTimeStamp())


class ClamilConfig:
    clamil_config = {
        "version": "1.0",
        "port": 7890,
        "socks_port": 7891,
        "allow_lan": True,
        "udp": True,
        "mixed-port": 7893,
        "ipv6": False,
        "mode": "Rule",
        "log-level": "info",
        "external-controller": "0.0.0.0:9090",
        "subs": [
            {
                "site_name": "abc",
                "sub_name": "zero",
                "sub_url": "..."
            },
        ],
        "rules": [
            "DOMAIN,blog.aewf.xyz,PROXY",
            "DOMAIN-SUFFIX,aewf.xyz,DIRECT"
        ],
        "skip_key": [
            "version", "subs", "skip_key"
        ]
    }
    _clamil_config_path = "{}/clamil.yaml".format(os.getcwd())

    def __init__(self, config_path=None):
        if config_path:
            self._clamil_config_path = config_path
        self.load_clamil_config()

    def set_base_config(self, k, v):
        self.clamil_config[k] = v

    def load_clamil_config(self):
        if not os.path.exists(self._clamil_config_path):
            yaml_dump(self._clamil_config_path, self.clamil_config)
            print("clamil.yaml is not exists\ncreated and exiting...\nplease config manually")
            exit(-1)
        else:
            with open(self._clamil_config_path, 'r') as f:
                self.clamil_config = yaml.safe_load(f)

    def get_subs(self):
        s = []
        for i in self.clamil_config.get("subs"):
            s.append(
                SubUrlNode(i["site_name"], i["sub_name"], i["sub_url"])
            )
        return s


class Clamil:
    _headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36"}
    _config = {
        "proxies": [],
        "rules": []
    }

    def __init__(self):
        self.clamilConfig = ClamilConfig()
        self._sub_urls = self.clamilConfig.get_subs()

    def resolve(self):
        self._read()
        self._yamly()
        self._override()
        self._write()
        self._clean()

    def _read(self):
        for i in range(len(self._sub_urls)):
            try:
                r = requests.get(self._sub_urls[i].sub_url, headers=self._headers)
                with open(self._sub_urls[i].tmp_store_path, 'w', encoding='utf-8') as f:
                    f.write(r.text)
                r.close()
            except Exception as e:
                print(e)
                exit(-1)

    def _yamly(self):
        for i in range(len(self._sub_urls)):
            with open(self._sub_urls[i].tmp_store_path, 'r', encoding='utf-8') as f:
                yaml_tmp = yaml.safe_load(f)
                a = yaml_tmp.get("proxies")
                for ii in range(len(a)):
                    a[ii]["name"] = "{}-{}".format(self._sub_urls[i].sub_name, a[ii]["name"])
                self._config["proxies"].extend(a)
                b = yaml_tmp.get("rules")
                self._config["rules"].extend(b)
        self._config["rules"] = list(set(self._config["rules"]))

    def _override(self):
        for i in self.clamilConfig.clamil_config.keys():
            if i not in self.clamilConfig.clamil_config.get("skip_key"):
                if i == "proxies" or i == "rules":
                    self._config[i].extend(self.clamilConfig.clamil_config[i])
                else:
                    self._config[i] = self.clamilConfig.clamil_config[i]

    def _write(self):
        new_config_file_full_name = "{}/{}.yaml".format(os.getcwd(), "config")
        if os.path.exists(new_config_file_full_name):
            os.remove(new_config_file_full_name)
        yaml_dump(new_config_file_full_name, self._config)

    def _clean(self):
        for i in self._sub_urls:
            os.remove(i.tmp_store_path)


if __name__ == '__main__':
    c = Clamil()
    # c.c.set_base_config()
    c.resolve()
