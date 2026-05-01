# Windows 11 下打包 EXE 与外置配置说明

本文说明如何在 **Windows 11** 上用 **Python 3.11** 把 [AudioDeployTool](../AudioDeployTool/) 打成 **exe**，并保证 **`Installers/`**、**`packages.csv`**、**`config.yaml`** 等与 exe **放在同一文件夹里即可随时修改**，无需重新打包。

程序已使用 `config_loader.runtime_base_dir()`：打包后从 **exe 所在目录** 读配置和安装包目录（不是临时解压目录）。

---

## 0. 你需要先有什么

| 项目 | 说明 |
|------|------|
| 系统 | Windows 11 64 位 |
| Python | **本机已安装 Python 3.11**（与当前开发机一致）。若尚未安装，请到 [python.org](https://www.python.org/downloads/) 下载 3.11 安装包，安装时勾选 **Add python.exe to PATH**。 |
| 项目代码 | 已克隆或解压 **Audiobox** 仓库，里面有文件夹 **`AudioDeployTool`**。 |

> **说明：** 项目源码要求 **Python 3.10 及以上**；**打包用机固定用 3.11** 即可，避免多版本搞混。若你电脑上装着 3.8、3.12 等多个版本，请严格按下面命令里的 **`py -3.11`** 操作。

---

## 1. 第一次：创建虚拟环境并安装依赖（只做一次）

### 1.1 打开 PowerShell

键盘 **Win**，输入 **PowerShell**，打开 **Windows PowerShell**（或 **终端**）。

### 1.2 进入 `AudioDeployTool` 文件夹

把下面第一行里的路径改成你电脑上 **Audiobox\AudioDeployTool** 的真实路径，整段复制执行：

```powershell
cd D:\你的路径\Audiobox\AudioDeployTool
```

执行后没有报错即可（若提示找不到路径，说明路径写错了）。

### 1.3 确认 Python 3.11 可用

复制执行：

```powershell
py -3.11 --version
```

应看到类似：`Python 3.11.x`。

- 若提示 **`py` 不是内部或外部命令**：安装 Python 时未装启动器，可改用 **「开始菜单 → Python 3.11」** 自带的 **Python 3.11 (64-bit)** 打开命令行，再 `cd` 到上面目录后执行 **`python -m venv .venv`**（把下面 1.4 里的 `py -3.11` 换成 `python` 即可）。
- 若 **`py -3.11` 报错**：说明没装 3.11，请先安装再继续。

### 1.4 用 3.11 创建专用虚拟环境（只做一次）

仍在 **`AudioDeployTool`** 目录下，复制执行：

```powershell
py -3.11 -m venv .venv
```

完成后，当前目录下会出现文件夹 **`.venv`**。

### 1.5 激活虚拟环境（每次新开 PowerShell 要打包时都要做）

```powershell
cd D:\你的路径\Audiobox\AudioDeployTool
.\.venv\Scripts\Activate.ps1
```

激活成功后，提示符前面会出现 **`(.venv)`**。

若执行 `Activate.ps1` 报错 **禁止运行脚本**，先复制执行下面**一行**（只需做一次），再重新执行上面的 `Activate.ps1`：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.6 安装依赖和 PyInstaller（有 `(.venv)` 时再执行）

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
```

等待全部显示成功，无红色报错即可。

---

## 2. 以后每次：打包成 exe

### 2.1 打开 PowerShell，进入目录并激活环境

把第一行路径改成你的真实路径：

```powershell
cd D:\你的路径\Audiobox\AudioDeployTool
.\.venv\Scripts\Activate.ps1
```

确认提示符前有 **`(.venv)`**。

### 2.2 执行打包命令（推荐：一个文件夹 + exe，启动快）

复制整段执行：

```powershell
pyinstaller --noconfirm --clean --name AudioDeploy --onedir --windowed main.py
```

完成后，当前目录下会出现文件夹 **`dist\AudioDeploy`**，里面有 **`AudioDeploy.exe`** 和 **`_internal`** 等文件。

| 参数 | 简单说明 |
|------|----------|
| `--onedir` | 生成「exe + 一堆依赖文件」，适合 PySide6，别删 `_internal`。 |
| `--windowed` | 双击 exe 不弹出黑色命令行窗口。程序在 **frozen** 时默认走 **GUI**；需要终端菜单时在命令行运行 **`AudioDeploy.exe --cli`**。若要保留黑窗口看日志，把 `--windowed` 删掉再打包。 |
| `--name AudioDeploy` | 生成的 exe 名字，可改成别的英文名。 |

### 2.3 若运行 exe 时提示缺 Qt 插件（少数电脑）

在同一环境、同一目录下再试一次（体积会变大一些）：

```powershell
pyinstaller --noconfirm --clean --name AudioDeploy --onedir --windowed --collect-all PySide6 main.py
```

---

## 3. 交给用户时文件夹里要有什么（外置、可改）

把整个 **`dist\AudioDeploy`** 复制出来（或打成 zip），**与 exe 同级**放入或保留：

| 文件/文件夹 | 是否必须 | 说明 |
|-------------|----------|------|
| `config.yaml` | 必须 | 全局路径池等；可直接用仓库里 `AudioDeployTool` 下的那份复制过来。 |
| `packages.csv` | 若有 CSV 配置则必须 | 用户改表格即可增删包、改静默参数。 |
| `locales\` | 必须 | 至少包含 `zh-CN.json`、`en-US.json`，从仓库复制。 |
| `Installers\` | 按实际安装包 | 放各分类子目录和 exe/msi 等安装包。 |

示例（用户解压后）：

```text
AudioDeploy/                    ← 可随意命名
├── AudioDeploy.exe
├── _internal/
├── config.yaml
├── packages.csv
├── locales/
│   ├── zh-CN.json
│   └── en-US.json
└── Installers/
    ├── daw/
    ├── software/
    └── plugin/
```

**用户以后只改：** `Installers\` 里的安装包、`packages.csv`（和必要时 `config.yaml`），**不用**再找你重新打 exe，除非你改了程序代码。

> **可选：** 若希望 zip 里一开始不带 `locales`，可用打包参数 `--add-data "locales;locales"` 把语言打进包；程序仍会优先读 **exe 旁边** 的 `locales`（若有）。

---

## 4. 多版本 Python 时怎么保证没用错

| 你想做的事 | 命令习惯 |
|------------|----------|
| **第一次创建 venv** | 用 **`py -3.11 -m venv .venv`**，锁死 3.11。 |
| **已激活 `(.venv)`** | 直接 **`python`**、**`pip`**、**`pyinstaller`** 即可，不必再写 3.11。 |
| **不想激活 venv** | 用 **`.\.venv\Scripts\python.exe -m pip install ...`** 和 **`.\.venv\Scripts\pyinstaller.exe ...`**，同样一定是 3.11。 |

---

## 5. 交付前自检清单

- [ ] 用户目录里是否有 **`config.yaml`、`packages.csv`、`locales`**（若未打进包）。  
- [ ] **`Installers`** 是否与 exe 同级。  
- [ ] 非管理员双击：UAC 是否正常（仅 Windows）。  
- [ ] 改 exe 旁的 **`packages.csv`** 后重启程序，列表是否更新。  
- [ ] 往 **`Installers`** 里加一个安装包后是否能被扫到并安装。

---

## 6. 常见问题

**用户电脑没有装 Python 能运行吗？**  
能。exe 里已经带了打包时的 Python，**不要求**用户安装 Python。

**SmartScreen / 杀毒拦截**  
未签名 exe 可能被拦截；正式分发可考虑代码签名。

**CSV 中文乱码**  
请用 **UTF-8** 保存 `packages.csv`（Excel 另存时注意编码）。

---

## 7. 根目录说明（给维护的人看）

| 场景 | 程序认为的「根目录」 |
|------|----------------------|
| 源码运行 `python main.py` | `AudioDeployTool` 源码所在文件夹 |
| 运行打好的 `AudioDeploy.exe` | **exe 所在文件夹**（外置配置与 `Installers` 放这里） |

---

## 8. GitHub Actions 云端打包（可选）

仓库已配置工作流 **`.github/workflows/build-windows.yml`**：

- 在 **windows-latest** 运行器上使用 **Python 3.11** 执行与上文相同的 **`pyinstaller --onedir --windowed`**。
- 将 **`dist/AudioDeploy`** 与仓库内 **`AudioDeployTool/packaging/default_sidecar/`** 合并为 **`staging/AudioDeploy`**：内含 **`config.yaml`、`locales/`、仅表头的 `packages.csv`、`Installers/` 三个空分类目录（含占位 `.gitkeep`）、`logs/` 空目录**，以及说明 **`README.txt`**（无示例安装包，由你自行放入）。上传 Artifact 时开启 **`include-hidden-files`**，避免仅含 `.gitkeep` 的目录在压缩包中丢失。
- 通过 **Actions → 对应运行 → Artifacts** 下载 **`AudioDeploy-Windows-<commit>`** 压缩内容即可分发。打好的 **exe 默认启动图形界面**；需要终端菜单时在 PowerShell 中执行 **`.\AudioDeploy.exe --cli`**。

触发条件：**`main` 分支 push**、**指向 `main` 的 Pull Request**、以及 **手动 workflow_dispatch**。
