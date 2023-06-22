# JPEG Compressor

这是一个 JPEG 批量压缩工具，使用 Python 编写, 支持多进程。该项目包含 GUI（图形界面），可递归压缩输入目录中的 JPEG 图像，并保存到输出目录。

该程序会尽量调整图像大小而不降低其质量。若输出目录中存在相同文件，则该文件将被跳过。若输入文件无法被压缩，则该文件将被复制到输出目录中。

## 快速开始

[下载](https://gitee.com/jackjyq/jpeg-compressor/releases) 适合自己系统的版本, 双击运行。

## 开发

### Windows 11

```powershell
python3.9 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
python main.py
```

### macOS

**已知问题: 启动时任务栏图标会消失数秒**

```shell
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

## 打包

### Windows 11

```powershell
.\venv\Scripts\Activate.ps1
pyinstaller main.py --onefile --icon=resources\icon.ico --noconsole --add-data="resources\icon.ico;resources" --name="JPEG-Compressor"
```

### macOS

```shell
pyinstaller main.py --onefile --icon=resources/icon.ico --noconsole --add-data="resources/icon.ico:resources" --name="JPEG-Compressor"
```

## 测试项目

- [ ] 点击开始，等待结束，点 X 关闭
- [ ] 点击开始, 不等结束, 点 X 关闭
- [ ] 点击开始, 不等结束, 点击停止； 点击开始, 等待结束； 点击开始，等待结束；点 X 关闭

## 致谢

<a href="https://www.flaticon.com/free-icons/neck-pillow" title="neck pillow icons">Neck pillow icons created by nawicon - Flaticon</a>

![](./resources/icon.ico)
