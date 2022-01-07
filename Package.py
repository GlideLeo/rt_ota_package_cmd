import json
import argparse
import pathlib


class Package:
    def __init__(self):
        self.config = {}

    def get_config(self, json_file):
        with open(json_file, "r", encoding='utf-8') as f:
            config_obj = json.loads(f.read())
            for key, value in config_obj.items():
                self.config[key] = value


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description='rt ota packaging tool CMD')
    ap.add_argument('-c', '--config', nargs='?', type=pathlib.Path, default='./config.json',
                    help='input the config file, config.json for example')
    args = vars(ap.parse_args())['config']
    package = Package()
    package.get_config(args)
    print(package.config)
    # TODO: 打包包头信息
    # 开始打包
    
