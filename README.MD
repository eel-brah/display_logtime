# 🕒 Logtime Tracker

A Python application to display user logtime statistics. Supports both terminal and GUI displays.

## 🚀 Features

* Fetch user logtime data between custom or auto-calculated date ranges
* Terminal mode with rich progress bar
* GUI mode 
* Auto-refreshing GUI to keep logtime up-to-date

## 🖼️ GUI Preview

> GUI dynamically shows:
>
> * Date range
> * Total hours logged
> * Percentage towards a configurable goal
> * Time remaining until the 28th of the month

## 📦 Requirements

* [ttkbootstrap](https://ttkbootstrap.readthedocs.io/)
* [requests-oauthlib](https://requests-oauthlib.readthedocs.io/)
* [rich](https://rich.readthedocs.io/)

## 📦 Setup

```bash
cd ~/.local/bin
git clone git@github.com:eel-brah/display_logtime.git
cd display_logtime
python3 -m venv mvenv
source mvenv/bin/activate
pip install -r requirements.txt
```

### 🔧 Configuration

Edit `conf.py` file with the following variables:

```python
UID = "YOUR_UID_HERE"
SECRET = "YOUR_SECRET_HERE"
```

To get your UID and SECRET, go to (42 Intra OAuth Applications)[https://profile.intra.42.fr/oauth/applications] and click "Register a new application".

Fill in the Name and Redirect URI with any valid values, then submit.
Copy the generated UID and SECRET and paste them into conf.py.

For a more convenient experience, consider adding a custom shortcut.
Go to your system settings and add a shortcut that runs:

```bash
~/.local/bin/display_logtime/mvenv/bin/activate/python3  ~/.local/bin/display_logtime/logtime.py YOUR_LOGIN -g
```


## 📝 Usage

### Terminal Mode (Default)

```bash
python3 main.py <login> [begin_date] [end_date]
```

* `login`: required username/login
* `begin_date` and `end_date`: optional dates in `YYYY-MM-DD` format

Example:

```bash
python logtime.py jdoe 2024-04-01 2024-04-30
```

### GUI Mode

Add the `-g` flag to launch the GUI:

```bash
python3 logtime.py jdoe -g
```

If `begin_date` or `end_date` is omitted, defaults to current and previous month's 28th.

## 🤖 CLI Help

```bash
python main.py --help

usage: main.py <login> [begin_date] [end_date] [-g]
Fetch and display log time for a user

positional arguments:
  login         User login (required)
  begin_date    Start date in YYYY-MM-DD format (optional)
  end_date      End date in YYYY-MM-DD format (optional)

options:
  -g            Display logtime in GUI
```

