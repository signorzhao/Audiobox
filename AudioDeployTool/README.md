# Audio Deploy

音频工作站自动化部署工具
Audio workstation deployment tool

把"DAW、驱动、效果器一个一个手动点下一步"变成"勾一勾、一键装完"。
Turn the tedious "install one by one" routine into "tick and go".

---

## 中文使用说明

### 获取最新版本（首次使用 / 想确认是不是最新版）

双击程序根目录里的 **`sync_to_T.bat`**。它会自动从服务器拉取开发者维护的最新版，同步到你**本地 T 盘**上的程序文件夹——新增的安装包会下载下来，已经过期/被移除的文件也会被清理掉。

> - 默认同步目标是本地 **T 盘**（你电脑上的一块本地硬盘盘符），程序日常运行也在这里。
> - 同步过程是**增量比对**的：没变化的文件不会重复传输，第二次起会很快。
> - 同步完成后，再按下面的步骤启动程序，新增的软件就会出现在列表里。

### 启动程序

**在主程序图标上点右键 → 选择「以管理员身份运行」**，然后在弹出的 UAC 窗口里点「是」。

直接双击运行可能没反应或启动失败（尤其在企业域电脑上）。本程序需要管理员权限来安装驱动、写注册表，**请务必走「以管理员身份运行」这一步**。

### 操作流程

1. **看列表**
   程序会按**类型**和**厂牌**把所有可装软件分组列出来；已经装过的会自动标记 `[已安装]`。

2. **搜索筛选**（界面顶部）
   在搜索栏里输入关键词即可模糊查找软件，下列任意一种都能命中：

   | 关键词类型 | 例子 |
   |------------|------|
   | 文件名 | `reaper`、`.exe` |
   | 软件名 | `FabFilter Pro-C 2` |
   | 类型 | `DAW`、`PLUGIN`、`SOFTWARE` |
   | 厂牌 | `fabfilter`、`soundtoys` |

   - 多个关键词**用空格分开**，需要全部命中才会显示（例 `fab q3`）。
   - **已勾选的软件**即使不匹配搜索词也会**保留在列表里**，避免漏装。

3. **勾选要安装的软件**
   一项一项打勾，也可以用底部「**全选**」/「**清除勾选**」一次性操作。

4. **点「开始安装」**
   不用看着屏幕，进度条会显示当前进度。整个过程是静默的，不需要点任何安装向导的「下一步」。

5. **查看结果**
   安装完成后会弹出一份汇总报告，列出每个软件是「完成」「失败」还是「已跳过」，并给出失败建议。

### 常见问题

- **双击没反应 / 启动失败？**
  请改用**右键「以管理员身份运行」**，再在 UAC 弹窗里点「是」。直接双击在部分电脑上会被静默拒绝。

- **某个软件装失败了，去哪看日志？**
  程序所在目录下有一个 `logs/` 文件夹，里面是最近一次运行的错误日志，可以直接发给维护这台机器的同事。

- **怎么切换中英文界面？**
  跟随系统语言自动切换，无需手动设置。

- **列表里看不到我想装的某个软件？**
  先双击 **`sync_to_T.bat`** 拉一下服务器上的最新版本，再重新启动程序；如果同步后还是没有，说明这个软件还没被开发者加进可装清单，请联系开发者补上。

- **怎么知道我现在用的是不是最新版本？**
  双击 **`sync_to_T.bat`** 就行——它会增量比对服务器与本地的差异；如果本地已经是最新，几乎是秒完，不会重复下载。建议每次准备给新机器部署前都跑一下。

- **同一个软件之前装过，列表里却没有标「已安装」？**
  说明检测路径与你电脑上的实际安装位置不一致，不影响使用，重复勾选安装也不会损坏现有版本，只会被静默覆盖。

---

## English Usage Guide

### Update to the latest version (first run / when you want to make sure it's current)

Double-click **`sync_to_T.bat`** in the program's root folder. It pulls the latest version — maintained by the developer — from the server and syncs it into the program folder on your **local T: drive**. New installers are downloaded; files that have been removed upstream are cleaned up too.

> - The default sync target is the local **T: drive** (a physical drive letter on your own PC), where the program normally runs.
> - The sync is **incremental** — unchanged files aren't re-transferred, so subsequent runs are fast.
> - Once the sync finishes, launch the program as below and the newly added software will show up in the list.

### Launch

**Right-click the main program icon and choose "Run as administrator"**, then click **Yes** in the UAC dialog.

A plain double-click may do nothing or fail to start (especially on domain-joined corporate PCs). The program needs administrator privileges to install drivers and write to the registry, so **always use "Run as administrator"**.

### How to use

1. **Browse the list**
   Every available installer is grouped by **category** and **vendor**. Items already installed are tagged `[Installed]`.

2. **Search & filter** (top bar)
   Type any keyword in the search bar to fuzzy-find software. Matches any of:

   | Field | Example |
   |-------|---------|
   | Filename | `reaper`, `.exe` |
   | Display name | `FabFilter Pro-C 2` |
   | Category | `DAW`, `PLUGIN`, `SOFTWARE` |
   | Vendor | `fabfilter`, `soundtoys` |

   - Multiple keywords **separated by spaces** are AND-matched (e.g. `fab q3`).
   - **Already-checked items stay visible** even when they don't match the search, so you never forget what you've queued.

3. **Tick the items you want**
   Tick one by one, or use **Select all** / **Clear** at the bottom for a one-shot toggle.

4. **Click Install**
   Sit back. The progress bar shows live status. Every installer runs silently — you don't need to click any wizard's "Next" buttons.

5. **Review the report**
   When it's done, a summary dialog lists each item as Success / Failed / Skipped, with hints for failures.

### FAQ

- **Double-click does nothing / fails to launch?**
  Use **Right-click → "Run as administrator"** instead, then click **Yes** in the UAC dialog. Plain double-click is silently rejected on some machines.

- **Where can I find the error logs?**
  Inside the `logs/` folder next to the program. It holds the most recent run — feel free to send it to whoever maintains the machine.

- **How do I switch between Chinese and English?**
  It follows your system locale automatically; no manual setup needed.

- **Why can't I see a particular installer in the list?**
  First, double-click **`sync_to_T.bat`** to pull the latest version from the server, then restart the program. If it still isn't there, the developer hasn't added it to the catalog yet — let them know.

- **How do I know if I'm running the latest version?**
  Just double-click **`sync_to_T.bat`** — it compares the server against your local folder incrementally; if you're already up to date it finishes in a second without re-downloading anything. It's a good idea to run it before deploying to a fresh machine.

- **I installed this app before but it isn't tagged `[Installed]`?**
  The detection path doesn't match your actual install location. It's harmless — ticking it again will only silently re-install over the existing version.
