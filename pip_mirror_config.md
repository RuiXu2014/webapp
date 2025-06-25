# 国内镜像源配置指南

## 临时使用镜像源

在安装依赖时添加 `-i` 参数：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 永久配置镜像源

### Windows

1. 创建或编辑 `%APPDATA%\pip\pip.ini` 文件：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

### Linux/macOS

1. 创建或编辑 `~/.pip/pip.conf` 文件：

```ini
[global]
index-url = https://pypi.tuna.tsinghua.edu.cn/simple
trusted-host = pypi.tuna.tsinghua.edu.cn
```

## 常用国内镜像源

1. 清华大学镜像（推荐）：
   ```
   https://pypi.tuna.tsinghua.edu.cn/simple
   ```

2. 阿里云镜像：
   ```
   https://mirrors.aliyun.com/pypi/simple
   ```

3. 腾讯云镜像：
   ```
   https://mirrors.cloud.tencent.com/pypi/simple
   ```

4. 华为云镜像：
   ```
   https://repo.huaweicloud.com/repository/pypi/simple
   ```

5. 中国科技大学镜像：
   ```
   https://pypi.mirrors.ustc.edu.cn/simple
   ```
