

### 1. 项目概述

本项目旨在开发一款轻量级、跨平台兼容（前期主打 Windows）、高度可配置的终端命令行工具。用于音频团队快速批量部署数字音频工作站（DAW）、系统运行环境（如 iLok）、硬件驱动及各类效果器/音源插件。

### 2. 技术栈选型

- **开发语言：** Python 3.10+
    
- **终端交互：** `questionary`（提供方向键与复选框支持的多级交互菜单）
    
- **界面渲染与进度：** `rich`（提供高亮输出、动态进度条及最终结果数据表）
    
- **配置解析：** `PyYAML`（解析全局路径与静默安装指令字典）
    
- **打包分发：** `PyInstaller`（编译为独立 `.exe` 文件）
    

### 3. 核心机制设计

- **配置驱动与环境分离：** 程序的执行逻辑与安装包数据完全解耦。通过 `config.yaml` 定义安装参数、依赖关系和检测路径。脚本运行时动态扫描本地 `Installers` 目录，匹配配置项后渲染交互菜单。
    
- **多维度已安装状态检测：**
    
    - **绝对路径检测：** 针对 DAW 或核心组件，通过校验独立可执行文件（如 `.exe`）判定状态。
        
    - **VST 插件动态池检测：** 将 Windows 复杂的 VST2/VST3 路径定义在全局配置池中，脚本按需组合插件文件名（如 `xxx.vst3`）进行全池遍历，命中即视为已安装。
        
- **UAC 自动提权：** 启动时利用 `ctypes` 检测管理员权限，无权限则自动静默弹窗重载，保障底层服务（如 PACE License Services）和注册表的写入权限。
    
- **优先级排序与后置命令钩子：** 针对 iLok 等核心依赖，配置 `is_priority` 标识确保其在执行队列的最前端，并支持配置 `post_install_cmd` 在安装完毕后唤醒相关系统服务。
    

### 4. 目录结构规范

Plaintext

```
AudioDeployTool/
├── main.py                 # 主程序源码入口
├── config.yaml             # 核心配置（参数、检测路径、环境池）
├── locales/                # 语言包目录
│   ├── zh-CN.json
│   └── en-US.json
├── logs/                   # 运行日志与错误报告输出目录
└── Installers/             # 安装包存放目录 (需按需建立子文件夹如 01_Env, 02_DAW)
```

---

## 核心骨架与模板代码

以下文件可以直接交由负责开发的程序员作为基座进行扩充。

### 1. 核心配置文件 (`config.yaml`)

YAML

```
# ==========================================
# 全局检测路径池 (Global Settings)
# ==========================================
global_settings:
  vst_paths:
    vst2_x64:
      - "C:\\Program Files\\VSTPlugins"
      - "C:\\Program Files\\Steinberg\\VstPlugins"
    vst3_x64:
      - "C:\\Program Files\\Common Files\\VST3"
    aax:
      - "C:\\Program Files\\Common Files\\Avid\\Audio\\Plug-Ins"

# ==========================================
# 安装包执行与检测逻辑 (Packages)
# ==========================================
packages:
  # 核心环境：绝对路径检测 + 提权服务唤醒
  "iLok License Support Win64.exe":
    name: "iLok License Support"
    category: "01_必备运行环境"
    is_priority: true
    win32_args: '/s /f1"C:\\ilok_setup.iss" /v"/qn /norestart"'
    check_absolute_path: "C:\\Program Files (x86)\\iLok License Manager\\iLok License Manager.exe"
    post_install_cmd: "net start LDSvc"
    help_text: "如安装失败，请手动重启电脑或卸载旧版 iLok Manager。"

  # 宿主软件：绝对路径检测
  "reaper769_x64-install.exe":
    name: "REAPER v7.69"
    category: "02_宿主软件 (DAW)"
    is_priority: false
    win32_args: "/S"
    check_absolute_path: "C:\\Program Files\\REAPER\\reaper.exe"
    help_text: "请确保后台没有正在运行的 REAPER 进程。"

  # 效果器插件：全局池相对路径检测
  "SoundtoysV55Bundle_5.5.4.18982_64.exe":
    name: "Soundtoys V5 Bundle"
    category: "03_效果器插件"
    is_priority: false
    win32_args: "/VERYSIlENT /SUPPRESSMSGBOXES /NORESTART"
    check_vst_file: "Decapitator.vst3"
    vst_format: "vst3_x64"
    help_text: "VST3 文件未找到，检查是否安装到自定义路径。"
```

### 2. 多语言文件 (`locales/zh-CN.json`)

JSON

```
{
  "title": "音频工作站自动化部署工具",
  "menu_prompt": "请按 <空格> 勾选需要部署的组件，<回车> 确认执行:",
  "tag_installed": "[已安装]",
  "progress_total": "总体部署进度",
  "progress_current": "正在安装: {app_name}",
  "status_success": "完成",
  "status_failed": "失败",
  "report_title": "安装结果汇总报告",
  "col_app": "软件名称",
  "col_status": "状态",
  "col_help": "后续建议/帮助内容",
  "msg_done": "所有选定的任务已处理完毕！请在保存工作后手动重启电脑以确保驱动生效。"
}
```

### 3. 核心逻辑框架 (`main.py`)

Python

```
import os
import sys
import json
import yaml
import ctypes
import subprocess
from pathlib import Path
import questionary
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

console = Console()

class AudioDeployController:
    def __init__(self, lang='zh-CN'):
        self.base_dir = Path(__file__).parent.absolute()
        self.config = self._load_yaml("config.yaml")
        self.i18n = self._load_json(f"locales/{lang}.json")
        self.installers_dir = self.base_dir / "Installers"
        
    def _load_yaml(self, filename):
        with open(self.base_dir / filename, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _load_json(self, filename):
        with open(self.base_dir / filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def check_uac(self):
        """检查并请求管理员权限"""
        if sys.platform != 'win32':
            return True
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False
            
        if not is_admin:
            console.print("[yellow]请求管理员权限以执行底层驱动和注册表配置...[/yellow]")
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit()

    def is_installed(self, pkg_config):
        """多维度判定软件是否已安装"""
        # 1. 绝对路径检测
        if 'check_absolute_path' in pkg_config:
            if os.path.exists(pkg_config['check_absolute_path']):
                return True
                
        # 2. VST 插件目录池遍历检测
        if 'check_vst_file' in pkg_config and 'vst_format' in pkg_config:
            file_name = pkg_config['check_vst_file']
            format_key = pkg_config['vst_format']
            paths_to_check = self.config.get('global_settings', {}).get('vst_paths', {}).get(format_key, [])
            
            for base_path in paths_to_check:
                if os.path.exists(os.path.join(base_path, file_name)):
                    return True
        return False

    def build_menu(self):
        """扫描目录并结合 config 构建交互式菜单"""
        choices = []
        # TODO: 待开发人员实现 - 遍历 self.installers_dir
        # TODO: 待开发人员实现 - 结合 self.is_installed() 给已安装的加上 self.i18n['tag_installed']
        # 演示用假数据:
        choices.append(questionary.Separator(f"=== 01_必备运行环境 ==="))
        choices.append(questionary.Choice("iLok License Support Win64.exe", value="iLok License Support Win64.exe"))
        
        selected_files = questionary.checkbox(
            self.i18n['menu_prompt'],
            choices=choices
        ).ask()
        
        return selected_files

    def execute_queue(self, selected_files):
        """带有 Rich 进度条的安装执行队列"""
        if not selected_files:
            return []

        results = []
        
        # TODO: 待开发人员实现 - 根据 config 中的 is_priority 对 selected_files 进行排序重组

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
        ) as progress:
            
            total_task = progress.add_task(f"[yellow]{self.i18n['progress_total']}", total=len(selected_files))
            
            for filename in selected_files:
                pkg_info = self.config['packages'].get(filename, {})
                app_name = pkg_info.get('name', filename)
                args = pkg_info.get('win32_args', '')
                
                desc = self.i18n['progress_current'].format(app_name=app_name)
                progress.update(total_task, description=f"[cyan]{desc}")
                
                # 拼接完整执行路径
                installer_path = self.installers_dir / pkg_info.get('category', '') / filename
                cmd = f'"{installer_path}" {args}'
                
                try:
                    # TODO: 待开发人员实现 - 实际执行 subprocess 并记录 stdout/stderr 到 log 文件
                    # process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    # return_code = process.returncode
                    
                    # 模拟执行成功
                    return_code = 0 
                    
                    success = return_code in [0, 3010]
                    
                    # TODO: 待开发人员实现 - 检测并执行 post_install_cmd 钩子 (如重启 PACE 服务)
                    
                except Exception as e:
                    success = False

                results.append({
                    "name": app_name,
                    "success": success,
                    "help": pkg_info.get('help_text', '')
                })
                
                progress.advance(total_task)

        return results

    def show_report(self, results):
        """渲染最终报告表"""
        if not results:
            return
            
        table = Table(title=f"🛠️ {self.i18n['report_title']}", show_header=True, header_style="bold magenta")
        table.add_column(self.i18n['col_app'], style="dim")
        table.add_column(self.i18n['col_status'])
        table.add_column(self.i18n['col_help'], width=50)

        for res in results:
            status_str = f"[green]✅ {self.i18n['status_success']}[/]" if res['success'] else f"[red]❌ {self.i18n['status_failed']}[/]"
            table.add_row(res['name'], status_str, res['help'])

        console.print(table)
        console.print(f"\n[bold green]✨ {self.i18n['msg_done']}[/bold green]\n")

if __name__ == "__main__":
    app = AudioDeployController()
    app.check_uac()
    
    console.print(f"[bold cyan]{app.i18n['title']}[/bold cyan]\n")
    
    selected = app.build_menu()
    exec_results = app.execute_queue(selected)
    app.show_report(exec_results)
```