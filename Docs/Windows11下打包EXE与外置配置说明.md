# Windows 11 下打包 EXE 与外置配置说明

本文说明如何在 **Windows 11** 上使用 **PyInstaller** 将 [AudioDeployTool](../AudioDeployTool/) 打成可执行文件，并保证 **`Installers/` 安装包目录** 与 **`packages.csv`（及 `config.yaml`）** 与 exe **同目录外置**，便于在不重新打包的情况下增删插件、修改表格与全局路径池。

项目已通过 `config_loader.runtime_base_dir()` 在打包后（`sys.frozen`）将根目录解析为 **`sys.executable` 所在文件夹**，因此外置文件必须与 **exe 放在同一目录**（见下文目录结构）。

---

## 1. 环境与目录约定

### 1.1 开发机要求

- Windows 11 x64  
- 已安装 **Python 3.10+**（与 `requirements.txt` 一致）  
- 建议在项目内使用虚拟环境，避免污染全局 Python：

```powershell
cd AudioDeployTool
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
```

### 1.2 交付给用户时的目录结构（推荐 `onedir`）

打包完成后，建议把整个输出文件夹打成 zip 分发。用户解压后目录应类似：

```text
AudioDeploy/                    ← 用户可随意命名此文件夹
├── AudioDeploy.exe             ← 主程序（或你在 spec 里指定的名字）
├── _internal/                  ← PyInstaller 生成的依赖目录（勿删）
├── config.yaml                 ← 外置：可编辑
├── packages.csv                ← 外置：可编辑
├── locales/                    ← 外置：zh-CN.json、en-US.json
│   ├── zh-CN.json
│   └── en-US.json
├── Installers/                 ← 外置：放置各分类子目录与安装包
│   ├── 01_必备运行环境/
│   ├── 02_宿主软件/
│   └── 03_效果器插件/
└── logs/                       ← 运行时生成；若无写权限需放在可写盘
```

**约定：**

- 新增/替换安装包：只改 **`Installers/`** 下文件即可。  
- 新增或调整软件条目、静默参数、厂牌分组等：只改 **`packages.csv`**（及必要时 **`config.yaml`** 中的 `global_settings`）。  
- **无需重新运行 PyInstaller**，除非你要升级程序逻辑本身。

若使用 **`--onefile` 单文件 exe**，exe 旁仍应放置上述 `config.yaml`、`packages.csv`、`locales`、`Installers`；程序会从 exe **所在目录**读取这些路径（与 `onedir` 相同）。

---

## 2. 使用 PyInstaller 打包（命令行示例）

在 **`AudioDeployTool`** 目录下、已激活 venv 且安装好依赖后执行。

### 2.1 推荐：`onedir` 模式

依赖与 Qt 文件较多，`onedir` 启动更快、排错更容易。

```powershell
cd path\to\Audiobox\AudioDeployTool
.\.venv\Scripts\activate

pyinstaller --noconfirm --clean --name AudioDeploy `
  --onedir `
  --windowed `
  main.py
```

说明：

| 参数 | 含义 |
|------|------|
| `--onedir` | 输出为「exe + `_internal`」目录，便于携带 Qt 等 DLL。 |
| `--windowed` | 无控制台窗口；若希望保留控制台日志，可改为 `-c` / 默认带控制台。 |
| `--name AudioDeploy` | 生成的 exe 名称，可按需修改。 |

**入口说明：** 当前 `main.py` 同时支持 CLI 与 `--gui`。若希望用户**默认打开图形界面**，可把 spec 或入口改为 `gui_main.py`，或给用户发快捷方式：`AudioDeploy.exe --gui`（若使用 `console` 入口，用户可在快捷方式里加参数）。

### 2.2 必须把语言包打进包时（可选）

若你希望 **首次解压目录里可以不包含 `locales/`**，可把语言 JSON 打进包内，同时仍把 **`packages.csv`、`config.yaml`、`Installers/`** 放在 exe 旁供用户编辑。示例（路径按你本机仓库调整）：

```powershell
pyinstaller --noconfirm --clean --name AudioDeploy `
  --onedir `
  --add-data "locales;locales" `
  main.py
```

注意：`--add-data` 在 Windows 上格式为 **`源;目标`**（分号）。打进包内的 `locales` 会与 exe 旁外置文件并存时，需明确程序**优先读哪一侧**；当前实现只读 **`runtime_base_dir()/locales`**，即 exe 同目录。若 exe 旁已有 `locales` 文件夹，会优先使用外置副本，便于用户无法改源码时仍能替换翻译。

### 2.3 PySide6 / Qt 插件

PyInstaller 对 PySide6 通常能自动收集大部分依赖。若运行时提示缺少 Qt 插件，可再使用官方 hook 或手动 `--collect-all PySide6`（会增大体积）：

```powershell
pyinstaller --noconfirm --clean --name AudioDeploy --onedir `
  --collect-all PySide6 `
  main.py
```

首次打包后应在 **目标 Win11 机器** 上完整跑一遍：CLI、`--gui`、实际静默安装一条。

---

## 3. 首次交付前检查清单

- [ ] 解压目录中存在 **`config.yaml`、`packages.csv`、`locales/`**（若未打进包内）。  
- [ ] **`Installers/`** 与 exe 同级，子目录与 CSV 中 `category` / 路径约定一致。  
- [ ] 以**非管理员**双击：UAC 提权是否正常（仅 Windows）。  
- [ ] 修改 **exe 旁的 `packages.csv`** 后再次启动，菜单是否反映新条目。  
- [ ] 往 **`Installers/`** 新增一个安装包后，扫描与执行路径是否正确。

---

## 4. 常见问题

**SmartScreen / 杀毒拦截**  
未签名的 exe 可能被标记。正式对内分发可考虑 **代码签名证书**；与「外置 CSV」无关。

**路径与编码**  
`packages.csv` 建议使用 **UTF-8（带 BOM 也可）**，避免 Excel 另存为 ANSI 导致中文乱码。

**单文件 exe 的启动速度**  
`--onefile` 每次运行会解压到临时目录，启动略慢；外置数据仍读 exe **所在目录**，不是临时目录。

---

## 5. 与源码行为的对照

| 场景 | 根目录解析 |
|------|------------|
| 源码运行 `python main.py` | `AudioDeployTool` 源码目录 |
| PyInstaller 打包后运行 exe | **exe 所在目录**（`sys.executable` 的父目录） |

因此：**只要把可编辑的配置与 `Installers` 与 exe 放在一起**，即可在 **不重新打包** 的前提下持续维护插件列表与安装参数。
