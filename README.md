# JPEG Compressor

这是一个 JPEG 批量压缩工具，使用 Python 编写。该项目包含 GUI（图形界面），可递归压缩输入目录中的 JPEG 图像，并保存到输出目录。

该程序会尽量调整图像大小而不降低其质量。若输出目录中存在相同文件，则该文件将被跳过。若输入文件无法被压缩，则该文件将被复制到输出目录中。

该程序已在 Windows 11 上进行了测试。

## 运行

```powershell
python3.9 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
python main.py
```

## 发布

```powershell
.\venv\Scripts\Activate.ps1
pyinstaller main.py --onefile --icon=resources\icon.ico --noconsole --add-data="resources\icon.ico;resources" --name="JPEG-Compressor"
```

## 测试

- [ ] 点击开始，等待结束，点 X 关闭
- [ ] 点击开始, 不等结束, 点 X 关闭
- [ ] 点击开始, 不等结束, 点击停止； 点击开始, 等待结束； 点击开始，等待结束；点 X 关闭

## 致谢

<a href="https://www.flaticon.com/free-icons/neck-pillow" title="neck pillow icons">Neck pillow icons created by nawicon - Flaticon</a>

![](./resources/icon.png)
