from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient
from datetime import datetime, timedelta
import sys
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
import time

UID = "u-s4t2ud-29991113c05adf4f3bfcccaeec2ee454c26836788f9f0a2a3e84329627c4a496"
SECRET = "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"

TIMEZONE = "Africa/Casablanca"
API_BASE_URL = "https://api.intra.42.fr/v2"
MAX_HOURS = 120

def fetch_logtime(login, begin_at, end_at):
    client = BackendApplicationClient(client_id=UID)
    oauth = OAuth2Session(client=client)
    token = oauth.fetch_token(
        token_url=f"{API_BASE_URL}/oauth/token",
        client_id=UID,
        client_secret=SECRET
    )

    begin_str = begin_at.isoformat() + "Z"
    end_str = end_at.isoformat() + "Z"

    user_url = f"https://api.intra.42.fr/v2/users/{login}"
    user_resp = oauth.get(user_url)
    if user_resp.status_code != 200:
        print(f"Invalid user {login}")
        sys.exit(1)

    try:
        stats_url = f"{API_BASE_URL}/users/{login}/locations_stats"
        params = {
            "begin_at": begin_str,
            "end_at": end_str,
            "time_zone": TIMEZONE
        }
        stats_resp = oauth.get(stats_url, params=params)
        return stats_resp.json()
    except Exception as e:
        print(f"API request failed: {str(e)}")
        sys.exit(1)

def get_date(begin , end):
    try:
        now = datetime.utcnow()
        if not begin:
            prev_month = now.month - 1 if now.month > 1 else 12
            prev_year = now.year if now.month > 1 else now.year - 1
            begin = datetime(prev_year, prev_month, 28)
        else:
            begin = datetime.fromisoformat(begin)

        if not end:
            end= now + timedelta(days=1)
        else:
            end= datetime.fromisoformat(end)
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

    if end <= begin:
        print("Error: End date must be after begin date")
        sys.exit(1)

    return begin, end

def display_progress( time_data, begin, end):
    console = Console()
    console.print(f"[bold cyan]From: {begin.strftime('%Y-%m-%d')}  -  To: {end.strftime('%Y-%m-%d')}[/]")

    total_time = timedelta()

    for time_str in time_data.values():
        h, m, s = time_str.split(":")
        sec, micro = s.split(".")
        duration = timedelta(
            hours=int(h),
            minutes=int(m),
            seconds=int(sec),
            microseconds=int(micro)
        )
        total_time += duration

    total_hours = total_time.total_seconds() / 3600

    with Progress(
        TextColumn("[bold cyan]Total Hours:[/]"),
        BarColumn(bar_width=40),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn(f"[bold green]{total_hours:.2f}h"),
        transient=False,
        console=console
    ) as progress:
        task = progress.add_task("[green]Progress toward 120h...", total=MAX_HOURS)
        step = 0.5
        current = 0.0
        while current < total_hours and current < MAX_HOURS:
            progress.update(task, advance=step)
            current += step
            time.sleep(0.01)

def main():
    args_len = len(sys.argv)
    if args_len < 2:
        print("Error: User login is required")
        print(f"Usage: python {sys.argv[0]} <login> [begin_date] [end_date]")
        sys.exit(1)

    login = sys.argv[1]
    begin, end = get_date(sys.argv[2] if args_len >= 3 else None, sys.argv[3] if args_len >= 4 else None)

    time_data = fetch_logtime(login, begin, end)
    display_progress(time_data, begin, end)

if __name__ == "__main__":
    main()
