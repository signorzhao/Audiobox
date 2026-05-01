# Audio Deploy CLI

音频工作站自动化部署工具 — 用于快速批量部署 DAW、驱动、效果器插件等音频软件。

## 快速开始

### 环境要求

- Python 3.10+（源码运行）；**Windows 下打包 exe 推荐使用 Python 3.11**，步骤见 [Windows11 打包说明](../Docs/Windows11下打包EXE与外置配置说明.md)。
- Windows 10/11（主要平台）或 macOS（基础兼容）

### 安装依赖

```bash
cd AudioDeployTool
pip install -r requirements.txt
```

### 运行

```bash
python main.py              # 终端界面（默认自动检测系统语言）
python main.py --lang en-US # 指定英文界面
python main.py --no-uac     # 跳过 UAC 提权（调试用）
python main.py --gui        # PySide6 图形界面（树形勾选，需 pip install -r requirements.txt）
python main.py --gui --lang en-US
python main.py --gui --no-uac   # 图形界面下调试（跳过提权）
```

PyInstaller 打成的 **exe**：默认**直接进图形界面**（双击即可）；需要终端菜单时加 **`--cli`**。

也可直接：`python gui_main.py`（等价于仅启动 GUI）。

Windows 11 下 PyInstaller 打包 exe，并保持 **`packages.csv` / `config.yaml` / `Installers/` 与 exe 同目录可编辑** 的说明见：[Windows11下打包EXE与外置配置说明.md](../Docs/Windows11下打包EXE与外置配置说明.md)。

云端打包：仓库 **GitHub Actions**（`.github/workflows/build-windows.yml`）在 `main` 推送、PR 或手动运行时构建 Windows 产物，可在 Actions 页面下载 **Artifacts**（内含 exe、`_internal`、外置目录骨架，无示例安装包）。

## 目录结构

```
AudioDeployTool/
├── main.py              # 主入口（CLI；支持 --gui）
├── gui_main.py          # PySide6 图形界面入口
├── config.yaml          # 全局路径池（VST 检测路径等）
├── packages.csv         # 安装包表格（文件名、静默参数、检测字段等）
├── config_loader.py     # 配置与语言包加载
├── packages_csv.py      # CSV 包表解析
├── detector.py          # 已安装状态检测
├── privilege.py         # UAC 自动提权（仅 Windows）
├── menu.py              # 交互式复选菜单
├── grouped_checkbox.py  # 带「全选」与组内条目联动显示的复选（基于 questionary）
├── executor.py          # 安装执行引擎
├── logger.py            # 错误日志
├── reporter.py          # 结果报告表
├── requirements.txt     # Python 依赖
├── locales/
│   ├── zh-CN.json       # 中文语言包
│   └── en-US.json       # 英文语言包
├── logs/                # 运行时错误日志输出
└── Installers/          # 安装包存放目录
    ├── 01_必备运行环境/
    ├── 02_宿主软件/
    └── 03_效果器插件/
```

## 如何添加新安装包

1. 将安装包文件放入 `Installers/<一级分类目录>/` 下；若需要菜单中的「子文件夹 + 全选本组」，可再放一层子目录（如 `Installers/03_效果器插件/fabfilter/xxx.exe`），或在表格中填写 `menu_subfolder`。
2. 在 `packages.csv` 中追加一行（可用 Excel、Numbers 或文本编辑器；**UTF-8** 保存，Excel 建议带 BOM 的 UTF-8，本工具已支持 `utf-8-sig`）。

### packages.csv 列说明

| 列名 | 必填 | 说明 |
|------|------|------|
| `filename` | 是 | 与 `Installers` 下安装包**文件名**完全一致 |
| `name` | 是 | 菜单显示名称 |
| `category` | 是 | 一级分组标题（与 `=== category ===` 对应） |
| `menu_subfolder` | 否 | 非空时：在该分类下显示子分组、树形前缀，并提供「全选本分组」（同一分组内至少 2 个包时显示） |
| `is_priority` | 否 | `true` / `1` / `yes` 表示优先安装 |
| `win32_args` | 否 | Windows 静默安装参数 |
| `darwin_args` | 否 | macOS 安装参数（预留） |
| `check_absolute_path` | 否 | 已安装检测：绝对路径 |
| `check_vst_file` | 否 | 已安装检测：VST 文件名 |
| `vst_format` | 否 | 与 `check_vst_file` 搭配，对应 `config.yaml` 里 `vst_paths` 的键 |
| `post_install_cmd` | 否 | 安装成功后执行的命令 |
| `help_text` | 否 | 失败时在报告中的提示 |

若未放置 `packages.csv` 或表内无有效数据行，则仅使用 `config.yaml` 中的 `packages`（YAML 字典）作为兼容方案。

### config.yaml 中仍保留的内容

全局 `global_settings.vst_paths` 等；安装包条目可留空 `packages: {}`，改由 CSV 维护。

## 工作流程

1. 启动时自动检测管理员权限（Windows），无权限则弹出 UAC 提权
2. 加载 `config.yaml`、`packages.csv`（若存在）与语言包
3. 扫描 `Installers/` 目录，匹配配置项
4. 渲染交互式复选菜单；子分组内可选「全选本分组」；已安装的标注 `[已安装]`
5. 用户选择后，按优先级排序执行静默安装
6. 安装完成后执行 `post_install_cmd` 钩子
7. 输出结果汇总报告表，失败项写入错误日志
