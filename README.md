# rt_ota_package_cmd

## 介绍

此程序是 RT-OTA 固件打包器`rt_ota_packaging_tool.exe`的非官方命令行版本，使用`python`编写，原版程序使用可参考[STM32 通用 Bootloader&OTA](https://www.rt-thread.org/document/site/#/rt-thread-version/rt-thread-standard/application-note/system/rtboot/an0028-rtboot?id=stm32-通用-bootloader)

此程序主要用于自动化打包，通过修改脚本即可简单完成定制化。开发的主要的原因是需要同时编译不同版本固件并且完成打包，手动使用官方程序打包非常不方便，而且比较费时。

目前支持：**不压缩|不加密、不压缩|AES256加密、gzip压缩|不加密、gzip压缩|AES256加密**四种配置

> 建议搭配[基于 STM32 的开源 Bootloader 框架 - RT-FOTA](https://gitee.com/spunky_973/rt-fota)使用，或者查看[基于RTT完整版的移植版本](https://github.com/JassyL/STM32-RTThread-BootLoader)，但此bootloader的解压功能似乎有问题，所以暂未使用压缩功能，但未作更多的测试，建议使用'未压缩|AES256加密'配置
>
> 或者搭配**[rt-thread-qboot](https://github.com/qiyongzhong0/rt-thread-qboot)**,此版本的 bootloader 在 ART-PI H750 开发板上通过测试。

## 使用
使用的`python`版本为3.9，需要添加依赖：

```shell
pip install pycryptodome
```

首先参考`config.json`配置各项参数，可以对比官方打包器。

![image-20220108030439498](https://qiniu.datasheep.cn/image-20220108030439498.png)



其中`test.bin`需要自行准备固件，`RBLPath`为保存路径，加密和压缩算法参考源文件内定义，其余参数参考官方配置,运行效果如下：

![package](https://qiniu.datasheep.cn/package.gif)

## gzip 压缩支持
使用 python 的 gzip 包完成压缩，并与官方版本作二进制比较，测试将压缩等级设置为 6,则与官方版本效果相同，但数据头有一些差别，如图所示：

![image-20220119014416668](https://qiniu.datasheep.cn/image-20220119014416668.png)

可以看出来数据基本一致，其中有2个连接的4字节不一样是因为后边压缩文件不一致导致 CRC 结果不一致，实际上数据只有6个字节不一致，而且测试不同文件打包后都是差这几个字节。

由于并不了解 gzip，解决这个问题花了很多时间，最终找到 rfc1952 标准才找到问题的原因。压缩后的文件头组成如下：

![image-20220119014902195](https://qiniu.datasheep.cn/image-20220119014902195.png)

对比上一张图的数据，0x1f,0x8b 分别对应 ID1,ID2等等，重点在于差异部分，MTIME 占4字节，组成时间戳表示最后修改时间，官方版本打包后这4个字节均为0,而我使用 python 脚本打包后这4个字节是准确的时间戳，所以导致不一致。04 表示使用最快的算法，00表示FAT filesystem (MS-DOS, OS/2, NT/Win32),这些搞清楚后，将这些字节直接替换成固定的"00 00 00 00 04 00"可以解决差异。

![image-20220119015333234](https://qiniu.datasheep.cn/image-20220119015333234.png)

完成后测试，gzip 压缩率还是很可观的：

![image-20220119040447033](https://qiniu.datasheep.cn/image-20220119040447033.png)

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

## 测试
在**支持的四种配置**下，输出的二进制文件与官方版本完全一致，对比结果如下：
![](https://qiniu.datasheep.cn/comp.gif)

## 注意

### RBL头 时间戳参数
原版使用6个字节，此版本只使用4个字节，最多表示到`2106-02-07 14:28:15`

## TODO
- [ ] 参数检查
- [x] 压缩算法