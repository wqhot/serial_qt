# Serial_qt

该项目基于PyQt开发，接收串口数据，按照协议解析并显示解析结果。以下是使用步骤：

## 步骤一：安装miniconda3

请下载并安装[miniconda3](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py39_23.9.0-0-Windows-x86_64.exe)。根据你的操作系统选择合适的安装程序进行下载，并按照安装向导进行安装。

## 步骤二：创建环境

打开`powershell`，进入项目根目录，并执行以下命令创建环境：

```shell
conda env create -f ./env.yaml
```

该命令会根据提供的`env.yaml`文件创建一个名为`serial_qt`的环境，并安装所需的依赖项。

## 步骤三：应用环境并运行程序

执行以下命令激活环境：

```shell
conda activate serial_qt
```

激活环境后，你可以运行程序。使用以下命令启动应用程序：

```shell
python ./main.py
```

应用程序将开始运行，并根据其功能提供相应的操作界面。

## 修改指南

1. 串口波特率设置

    修改`main.py`: line 24 处的`BAUD_RATE`变量值

2. 显示文本框标签文本修改

    修改`main.py`: line 25 处`PARAMS_NAME`变量值