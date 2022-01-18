import json
import argparse
import pathlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import time
import os
import zlib
import struct
import gzip

algorithm_code = {'RT_OTA_CRYPT_ALGO_NONE': 0, 'RT_OTA_CRYPT_ALGO_AES256': 2,
                  'RT_OTA_CMPRS_ALGO_GZIP': 256, 'RT_OTA_CMPRS_ALGO_GZIP_AES256': 258}


# 输出十六进制类型数组
def print_hex(data):
    b = [hex(int(i)) for i in data]
    print(" ".join(b))


class RblHeader:
    def __init__(self):
        self.magic = [82, 66, 76, 0]
        self.algorithm = ""
        self.timestamp = 0
        self.firmware_partition_name = 1  # 16 bytes
        self.firmware_version = 1  # 24 bytes
        self.sn = 0  # 24 bytes
        self.crc32 = 0
        self.hash = 0
        self.size_raw = 0
        self.size_package = 0
        self.info_crc32 = 0

    def get_rbl_header(self):
        header = struct.pack('<4B2HI16s24s24s4I', 82, 66, 76, 0, algorithm_code[self.algorithm], 0, int(self.timestamp),
                             self.firmware_partition_name.encode("utf-8"),
                             self.firmware_version.encode("utf-8"), self.sn.encode("utf-8"),
                             self.crc32, self.hash, self.size_raw, self.size_package)
        self.info_crc32 = zlib.crc32(header)
        print('info crc32 is : %#x' % self.info_crc32)
        header_crc32 = struct.pack('<I', self.info_crc32)
        header = header + header_crc32
        return header


class Fnv1a:
    def __init__(self):
        self.fnv_32_prime = 0x01000193
        self.fnv1_32_init = 0x811c9dc5

    def fnv1a(self, data):
        assert isinstance(data, bytes)
        hash_value = self.fnv1_32_init
        fnv_size = 2 ** 32
        for i in range(0, len(data)):
            hash_value = hash_value ^ data[i]
            hash_value = (hash_value * self.fnv_32_prime) % fnv_size
        return hash_value


class Package:
    def __init__(self):
        self.config = {}
        self.rbl_hdr = RblHeader()

    def get_config(self, json_file):
        with open(json_file, "r", encoding='utf-8') as f:
            config_obj = json.loads(f.read())
            for key, value in config_obj.items():
                self.config[key] = value

    def encrypt(self, data):
        cipher = AES.new(self.config['EncryptionKey'].encode("utf-8"), AES.MODE_CBC,
                         self.config['EncryptionIV'].encode("utf-8"))
        pad_data = pad(data, 16, style='pkcs7')
        return cipher.encrypt(pad_data)

    def gzip_compress(self, data):
        result = gzip.compress(data, compresslevel=6)
        with open('./temp_file.bin', 'wb+') as temp_write:
            temp_write.write(result)
            temp_write.seek(0x04, 0)
            temp_write.write(b'\x00\x00\x00\x00\x04\x00')
        with open('./temp_file.bin', 'rb') as temp_read:
            result = temp_read.read()
        os.remove('./temp_file.bin')
        return result


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

    with open(package.config['FirmwarePath'], 'rb') as f:
        raw_data = f.read()
        package.rbl_hdr.size_raw = len(raw_data)
        print('firmware raw size is : ' + str(package.rbl_hdr.size_raw) + 'bytes')
        package.rbl_hdr.hash = Fnv1a().fnv1a(raw_data)
        print('firmware raw data hash value is : %#x' % package.rbl_hdr.hash)
        package.rbl_hdr.timestamp = os.path.getmtime(package.config['FirmwarePath'])
        print('firmware last edit time is : %#d' % package.rbl_hdr.timestamp)
        if package.config['CompressionEncryptionAlgorithm'] == 'RT_OTA_CRYPT_ALGO_NONE':
            out_data = raw_data
        if package.config['CompressionEncryptionAlgorithm'] == 'RT_OTA_CRYPT_ALGO_AES256':
            out_data = package.encrypt(raw_data)
        if package.config['CompressionEncryptionAlgorithm'] == 'RT_OTA_CMPRS_ALGO_GZIP':
            out_data = package.gzip_compress(raw_data)
        if package.config['CompressionEncryptionAlgorithm'] == 'RT_OTA_CMPRS_ALGO_GZIP_AES256':
            out_data = package.gzip_compress(raw_data)
            out_data = package.encrypt(out_data)
        package.rbl_hdr.crc32 = zlib.crc32(out_data)
        print('out_data crc32 is : %#x' % package.rbl_hdr.crc32)
        package.rbl_hdr.size_package = len(out_data)
        print('out_data size is : ' + str(package.rbl_hdr.size_package) + 'bytes')
        package.rbl_hdr.sn = "00010203040506070809\0\0\0\0"
        package.rbl_hdr.algorithm = package.config['CompressionEncryptionAlgorithm']
        package.rbl_hdr.firmware_partition_name = package.config['FirmwarePartitionName']
        str(package.rbl_hdr.firmware_partition_name).ljust(16, '\0')
        package.rbl_hdr.firmware_version = package.config['FirmwareVersion']
        str(package.rbl_hdr.firmware_version).ljust(24, '\0')
        print_hex(package.rbl_hdr.get_rbl_header())
        rbl = open(package.config['RBLPath'], 'wb+')
        rbl.write(package.rbl_hdr.get_rbl_header())
        rbl.write(out_data)
        rbl.close()
