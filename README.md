# winactive

長時間の処理中にWindowsのスリープを防ぐ軽量CLIツールです。  
A lightweight CLI tool that keeps Windows awake during long-running work.

[日本語](#日本語) | [English](#english)

## 日本語

### 概要

AIジョブやデータ処理などの待機中に、Windowsがアイドル状態によってスリープすることを防ぎます。Windows APIの`SetThreadExecutionState`を使用し、マウス移動やキー入力の偽装は行いません。

- 標準ではシステムのスリープと画面の自動消灯を抑止します。
- 画面の消灯を許可したまま、システムだけを起動状態に保てます。
- 指定時間で自動終了できます。
- 通常終了時に、このプロセスのスリープ抑止要求を解除します。

実行中のジョブを自動検出する機能はありません。必要な間、このツールを起動しておく方式です。電源プランやセッションのタイムアウト設定自体は変更しません。

### 動作環境

- Windows（macOSとLinuxには非対応）
- ソースから実行する場合はPython 3.7以降。外部パッケージは不要です。
- exeをビルドする場合は、使用するPyInstallerが対応するPython環境が必要です。

### 実行方法

実行方法は次の2種類です。

1. ローカルのPython実行環境を使用して、Pythonスクリプトとして実行する。Python標準ライブラリのみで動作し、外部パッケージは不要です。
	```powershell
	python .\winactive.py
	```
2. ビルド済みのexeを実行する。Pythonがインストールされていない環境でも実行できます。
	- GitHub Actionsでビルドされたファイルを`Artifacts`からダウンロードして実行する
	- 自分でビルドして実行する（手順は[exeのビルド](#exeのビルド)を参照）

	```powershell
	.\release\winactive.exe --duration 2h
	```

### クイックスタート

ソースコードをダウンロードまたはクローンし、プロジェクトフォルダでPowerShellを開きます。

```powershell
# 停止するまで実行
python .\winactive.py

# 2時間だけ実行
python .\winactive.py --duration 2h

# 画面の自動消灯を許可
python .\winactive.py --no-display

# 90分間、画面消灯を許可し、10秒ごとに要求を更新
python .\winactive.py --duration 90m --no-display --interval 10s
```

終了するには`Ctrl+C`を押します。既定では60秒間隔で待機するため、停止要求や指定時間の経過から終了まで、最大で約1待機間隔の遅れが生じます。応答を早めたい場合は`--interval 5s`などを指定してください。

### コマンドラインオプション

| オプション | 内容 | 既定値 |
| --- | --- | --- |
| `-h`, `--help` | ヘルプを表示して終了 | — |
| `--duration TIME` | 指定時間の経過後に終了 | 時間制限なし |
| `--interval TIME` | スリープ抑止要求の更新間隔 | 60秒 |
| `--no-display` | システムのスリープのみを抑止し、画面の自動消灯を許可 | 無効（画面消灯も抑止） |
| `--away-mode` | Away Modeの要求を追加。主にデスクトップPC向けで、効果は環境に依存 | 無効 |
| `--once` | APIを1回呼び出して成功を表示し、要求を解除して終了 | 無効 |

`TIME`には`s`（秒）、`m`（分）、`h`（時間）を指定できます。**単位を省略すると分として扱います。これは`--interval`にも適用されます。** 例えば`--interval 5`は5分で、5秒ではありません。

小数も使用でき、`1.5h`は90分です。秒未満の端数は切り捨てられ、変換後に1秒以上となる正の値が必要です。

```powershell
python .\winactive.py --help
python .\winactive.py --once
```

`--once`はAPI呼び出しの簡易確認です。長時間のスリープ抑止やRDP接続維持を検証するものではありません。現在、起動時のヘルプと実行メッセージは英語です。

### テスト

`tests`ディレクトリに、標準ライブラリの`unittest`のみを使ったテストがあります。追加のパッケージは不要です。

```powershell
python -m unittest discover -s tests -v
```

### exeのビルド

Windows上で、プロジェクトフォルダから実行します。以下では仮想環境にビルド用の依存関係をインストールします。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --onefile --name winactive --distpath .\release .\winactive.py
```

ビルド後、`release\winactive.exe`が生成されます。生成済みexeはソースコードには含まれません。このexeはPythonがインストールされていないWindows環境でも実行できます。

```powershell
.\release\winactive.exe --duration 2h
```

同梱の設定ファイルを使用してビルドすることもできます。

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --distpath .\release .\winactive.spec
```

### GitHub Actionsでの自動ビルド

GitHubへ`main`または`master`ブランチをpushすると、GitHub ActionsがWindows上でexeをビルドします。`v1.0.0`のようなタグをpushした場合もビルドされます。手動で実行する場合は、リポジトリの`Actions`タブから`Build Windows executable`を選び、`Run workflow`を実行してください。

ビルド完了後、Workflowの実行結果にある`Artifacts`から`winactive-windows`をダウンロードできます。成果物には`winactive.exe`が含まれます。

### 制約とRDP・Azureでの利用

このツールはWindowsに起動状態の維持を要求します。次の制御を解除・回避するものではありません。

- RDPのアイドルセッションや切断済みセッションに対する時間制限
- Azure Bastion、VPN、ゲートウェイなどの接続タイムアウト
- 組織のセキュリティポリシーによる自動ロックや切断
- スクリーンセーバー（[MicrosoftのAPI仕様](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate)では抑止対象外）

Azure Windows VMでも、効果はOSの電源管理設定やホスト側の制御に依存します。RDP切断が問題の場合は、管理者とセッション制限・接続経路のタイムアウトを確認してください。

長時間ジョブをRDP接続とは独立して継続させたい場合は、タスクスケジューラ、Windowsサービス、バッチ処理など、対話セッションに依存しない実行方式を検討してください。

### ファイル構成

| ファイル | 役割 |
| --- | --- |
| `winactive.py` | CLI本体 |
| `winactive.spec` | PyInstallerのビルド設定 |
| `tests/test_winactive.py` | unittestによるテスト |
| `.github/workflows/build-windows.yml` | GitHub ActionsでのWindowsビルド設定 |
| `README.md` | 日本語・英語の説明 |
| `LICENSE` | MITライセンスの全文 |
| `.gitignore` | ビルド成果物・キャッシュなどの除外設定 |

### トラブルシューティング

- **`python`が見つからない:** PythonのインストールとPATHを確認してください。WindowsのPythonランチャーがあれば`py .\winactive.py`でも実行できます。
- **`release\winactive.exe`がない:** 上記の手順でビルドするか、Pythonから直接実行してください。
- **Ctrl+Cですぐ終了しない:** 現在の待機間隔が終わると停止します。`--interval 5s`などで間隔を短くできます。
- **画面がロックされる・RDPが切断される:** スリープ抑止とは別の制御です。該当するポリシーや接続設定を確認してください。
- **API呼び出しでエラーになる:** `--once`で再現を確認し、Windows環境と表示されたエラーを確認してください。

### ライセンス

このプロジェクトはMITライセンスのもとで公開します。

## English

### Overview

Keep Windows from entering idle sleep while you wait for AI jobs, data processing, or other long-running work. The tool uses the Windows `SetThreadExecutionState` API and does not simulate mouse movement or keyboard input.

- Prevents system idle sleep and display idle timeout by default.
- Can keep the system awake while allowing the display to turn off.
- Supports automatic exit after a specified duration.
- Clears this process's wakefulness request on normal exit.

The tool does not detect running jobs. Start it for as long as you need it. It does not modify power plans or session timeout settings.

### Requirements

- Windows (macOS and Linux are not supported)
- Python 3.7 or later to run from source; no third-party packages required
- A Python environment supported by your chosen PyInstaller version to build an executable

### Ways to run

There are two ways to run the tool:

1. Run the Python script with a local Python runtime. It uses only the Python standard library and needs no external packages.
	```powershell
	python .\winactive.py
	```
2. Run a prebuilt executable. It can run on Windows without Python installed.
	- Download the file built by GitHub Actions from `Artifacts` and run it.
	- Build it yourself locally (see [Build an executable](#build-an-executable)).

	```powershell
	.\release\winactive.exe --duration 2h
	```

### Quick start

Download or clone the source and open PowerShell in the project directory.

```powershell
# Run until stopped
python .\winactive.py

# Run for two hours
python .\winactive.py --duration 2h

# Allow the display to turn off
python .\winactive.py --no-display

# Run for 90 minutes, allow display sleep, and refresh every 10 seconds
python .\winactive.py --duration 90m --no-display --interval 10s
```

Press `Ctrl+C` to stop. The tool waits in 60-second intervals by default, so a stop request or duration expiry can take up to approximately one interval to take effect. Use `--interval 5s`, for example, for a shorter response time.

### Command-line options

| Option | Description | Default |
| --- | --- | --- |
| `-h`, `--help` | Show help and exit | — |
| `--duration TIME` | Stop after the specified duration | No time limit |
| `--interval TIME` | How often to refresh the wakefulness request | 60 seconds |
| `--no-display` | Prevent system sleep but allow the display to turn off | Disabled (also keeps the display on) |
| `--away-mode` | Also request Away Mode; mainly for desktop systems, with environment-dependent behavior | Disabled |
| `--once` | Call the API once, report success, clear the request, and exit | Disabled |

`TIME` accepts `s` (seconds), `m` (minutes), and `h` (hours). **Without a suffix, the value is interpreted as minutes, including for `--interval`.** For example, `--interval 5` means five minutes, not five seconds.

Decimal values are supported: `1.5h` means 90 minutes. Fractional seconds are truncated, and the resulting duration must be at least one second.

```powershell
python .\winactive.py --help
python .\winactive.py --once
```

`--once` is a basic API smoke test. It does not verify long-term sleep prevention or RDP connection persistence. Startup help and runtime messages are currently displayed in English.

### Tests

The `tests` directory contains tests written with the standard library's `unittest`. No additional packages are required.

```powershell
python -m unittest discover -s tests -v
```

### Build an executable

Run these commands on Windows from the project directory. This example installs build dependencies in a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pyinstaller
.\.venv\Scripts\python.exe -m PyInstaller --onefile --name winactive --distpath .\release .\winactive.py
```

The build creates `release\winactive.exe`. A prebuilt executable is not included in the source. The resulting executable can run on Windows without a separate Python installation.

```powershell
.\release\winactive.exe --duration 2h
```

Alternatively, build using the included configuration file:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --distpath .\release .\winactive.spec
```

### Automatic builds with GitHub Actions

Pushing to the `main` or `master` branch starts a Windows build in GitHub Actions. Pushing a tag such as `v1.0.0` also starts a build. To run it manually, open the repository's `Actions` tab, select `Build Windows executable`, and choose `Run workflow`.

After the workflow completes, download `winactive-windows` from `Artifacts` on the workflow run page. The artifact contains `winactive.exe`.

### Limitations, RDP, and Azure

The tool requests that Windows remain awake. It does not disable or bypass:

- RDP idle-session or disconnected-session time limits
- Azure Bastion, VPN, gateway, or other connection timeouts
- Automatic lock or disconnect rules enforced by organizational security policies
- Screen savers (excluded according to the [Microsoft API documentation](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate))

On Azure Windows VMs, the effect depends on OS power management settings and host-side controls. If RDP disconnects, check session limits and connection timeouts with your administrator.

For jobs that must continue independently of an RDP connection, consider Task Scheduler, a Windows service, or a batch-processing setup that does not depend on an interactive session.

### Project layout

| File | Purpose |
| --- | --- |
| `winactive.py` | CLI implementation |
| `winactive.spec` | PyInstaller build configuration |
| `tests/test_winactive.py` | Unit tests (unittest) |
| `.github/workflows/build-windows.yml` | GitHub Actions Windows build workflow |
| `README.md` | Japanese and English documentation |
| `LICENSE` | Full text of the MIT License |
| `.gitignore` | Build output and cache exclusions |

### Troubleshooting

- **`python` is not found:** Check your Python installation and PATH. If the Windows Python launcher is available, you can also use `py .\winactive.py`.
- **`release\winactive.exe` is missing:** Build it using the instructions above or run the Python source directly.
- **Ctrl+C does not stop the tool immediately:** The tool stops after the current wait interval. Use a shorter interval such as `--interval 5s`.
- **The screen locks or RDP disconnects:** These controls are separate from sleep prevention. Check the relevant policies and connection settings.
- **The API call fails:** Try `--once` to reproduce the issue, then check your Windows environment and the reported error.

### License

This project is released under the MIT License.
