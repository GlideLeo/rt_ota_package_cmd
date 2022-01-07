# rt_ota_package_cmd

## 介绍

此程序是 RT-OTA 固件打包器`rt_ota_packaging_tool.exe`的非官方命令行版本，使用`python`编写，原版程序使用可参考[STM32 通用 Bootloader&OTA](https://www.rt-thread.org/document/site/#/rt-thread-version/rt-thread-standard/application-note/system/rtboot/an0028-rtboot?id=stm32-通用-bootloader)

此程序主要用于自动化打包，通过修改脚本即可简单完成定制化。开发的主要的原因是需要同时编译不同版本固件并且完成打包，手动使用官方程序打包非常不方便，而且比较费时。

**官方版的压缩功能在此版本中尚未被支持**

> 建议搭配[基于 STM32 的开源 Bootloader 框架 - RT-FOTA](https://gitee.com/spunky_973/rt-fota)使用，或者查看[基于RTT完整版的移植版本](https://github.com/JassyL/STM32-RTThread-BootLoader)，但此bootloader的解压功能似乎有问题，所以暂未使用压缩功能。

## 使用
使用的`python`版本为3.9，主要依赖：

```shell
pip install pycryptodome
```

首先参考`config.json`配置各项参数，可以对比官方打包器。

![image-20220108030439498](https://qiniu.datasheep.cn/image-20220108030439498.png)



其中`test.bin`需要自行准备固件，`RBLPath`为保存路径，加密和压缩算法参考源文件内定义，其余参数参考官方配置,运行效果如下：

![package](https://qiniu.datasheep.cn/package.gif)

## 说明

调试输出了相关的RBL文件前96字节的细节，对比官方打包器可以看到参数均一致：

```shell
firmware raw size is : 105008bytes
firmware raw data hash value is : 0x6f275ae0
firmware last edit time is : 1641580225
out_data crc32 is : 0x598fcdc1
out_data size is : 105024bytes
info crc32 is : 0xdb5336cb
0x52 0x42 0x4c 0x0 0x2 0x0 0x0 0x0 0xc1 0x86 0xd8 0x61 0x61 0x70 0x70 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x31 0x32 0x30 0x35 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x0 0x30 0x30 0x30 0x31 0x30 0x32 0x30 0x33 0x30 0x34 0x30 0x35 0x30 0x36 0x30 0x37 0x30 0x38 0x30 0x39 0x0 0x0 0x0 0x0 0xc1 0xcd 0x8f 0x59 0xe0 0x5a 0x27 0x6f 0x30 0x9a 0x1 0x0 0x40 0x9a 0x1 0x0 0xcb 0x36 0x53 0xdb
info crc32 is : 0xdb5336cb
```

![image-20220108031214462](https://qiniu.datasheep.cn/image-20220108031214462.png)

其96字节具体含义可以参考王工在[基于 STM32 的开源 Bootloader 框架 - RT-FOTA](https://gitee.com/spunky_973/rt-fota)给出的描述

```
typedef struct {
	char type[4];				/* RBL 字符头 */
	rt_uint16_t fota_algo;		/* 算法配置: 表示是否加密或者使用了压缩算法 */
	rt_uint8_t fm_time[6];		/* 原始 bin 文件的时间戳, 6 位时间戳, 使用了 4 字节, 包含年月日信息 */
	char app_part_name[16];		/* app 执行分区名 */
	char download_version[24];	/* 固件代码版本号 */
	char current_version[24];	/* 这个域在 rbl 文件生成时都是一样的，我用于表示 app 分区当前运行固件的版本号，判断是否固件需要升级 */
	rt_uint32_t code_crc;		/* 代码的 CRC32 校验值, 它是的打包后的校验值, 即 rbl 文件 96 字节后的数据 */
	rt_uint32_t hash_val;		/* 估计这个域是指的原始代码本身的校验值，但不知道算法，无法确认，故在程序中未使用 */
	rt_uint32_t raw_size;		/* 原始代码的大小 */
	rt_uint32_t com_size;		/* 打包代码的大小 */
	rt_uint32_t head_crc;		/* rbl 文件头的 CRC32 校验值，即 rbl 文件的前 96 字节 */
} rt_fota_part_head, *rt_fota_part_head_t;
```

其中，hash 值的计算基于 fnv1a 算法，计算方法代码中已给出。

```python
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
```



## 注意

### 支持配置

目前仅支持**未压缩|AES256加密**

### 时间戳参数
原版使用6个字节，此版本只使用4个字节，最多表示到`2106-02-07 14:28:15`

## TODO
- [ ] 参数检查
- [ ] 压缩算法