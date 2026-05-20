# Wake-and-Refresh Setup — AI Student Dashboard

Goal: make the 7am news refresh reliable even when your PC is asleep overnight.

The Cowork scheduled task (`ai-dashboard-daily-refresh`) needs the Cowork app running to fire. So this guide does two things:

1. Lets Windows **wake your PC from sleep** at 6:55am.
2. Makes sure **Cowork is already running** when the PC wakes, so the 7am task fires immediately.

This works for sleep and hibernate. It does **not** work if the PC is fully powered off (shutdown) — wake timers need at least sleep/hibernate to function.

---

## Part 1 — Auto-start Cowork with Windows

So Cowork is in memory whenever the PC is on.

1. Open **Settings** (Win + I).
2. Go to **Apps → Startup**.
3. Find **Cowork** in the list and toggle it **On**.

If Cowork isn't in that list:
1. Open **Task Manager** (Ctrl + Shift + Esc).
2. Click the **Startup apps** tab.
3. Find Cowork, right-click → **Enable**.

If it's still missing: open File Explorer, type `shell:startup` in the address bar, hit Enter. Drop a shortcut to Cowork into the folder that opens.

---

## Part 2 — Allow wake timers in your power plan

Windows disables wake timers by default on many laptops. Turn them on.

1. Open **Settings → System → Power & battery → Power mode**.
2. Click **Additional power settings** (right side, or scroll down).
3. Next to your active plan, click **Change plan settings → Change advanced power settings**.
4. In the dialog, expand **Sleep → Allow wake timers**.
5. Set **On battery: Enable** and **Plugged in: Enable**.
6. Click **Apply → OK**.

Quick check while you're there: also make sure **Sleep → Hibernate after** isn't set to an aggressive value that powers the PC off entirely. Sleep is fine; full shutdown breaks this.

---

## Part 3 — Create the wake task

This is the entry that actually wakes the PC at 6:55am.

1. Press **Win + R**, type `taskschd.msc`, hit Enter. Task Scheduler opens.
2. In the right pane, click **Create Task...** (not "Create Basic Task" — we need the advanced options).

**General tab**
- Name: `Wake for AI Dashboard`
- Description: `Wakes the PC at 6:55am so the Cowork dashboard's 7am news refresh runs reliably.`
- Tick **Run whether user is logged on or not** — or leave on the default "Run only when user is logged on" if you usually stay logged in.
- Tick **Run with highest privileges**.

**Triggers tab → New...**
- Begin the task: **On a schedule**
- Settings: **Daily**
- Start: today's date, time **06:55:00**
- Recur every: 1 day
- Tick **Enabled** at the bottom.
- Click **OK**.

**Actions tab → New...**
- Action: **Start a program**
- Program/script: `cmd.exe`
- Add arguments: `/c exit`
- (This is a no-op — the *trigger* is what wakes the PC, the action just needs to exist.)
- Click **OK**.

**Conditions tab** (this is the important one)
- Untick **Start the task only if the computer is on AC power** (unless you only care about plugged-in days).
- Tick **Wake the computer to run this task**.

**Settings tab**
- Tick **Allow task to be run on demand**.
- Tick **Run task as soon as possible after a scheduled start is missed**.
- Leave the rest at defaults.

Click **OK** to save. If Windows asks for your password, give it.

---

## Part 4 — (Optional) Launch Cowork right after wake

If Part 1 worked (Cowork auto-starts at login), this is usually unnecessary — Cowork is already running because you're already logged in.

But if you sometimes close Cowork manually, add a second task to relaunch it at 6:56am:

1. Task Scheduler → **Create Task...**
2. Name: `Launch Cowork at 06:56`
3. Triggers: **Daily at 06:56:00**
4. Actions: **Start a program** → browse to Cowork's executable (usually under `C:\Users\<you>\AppData\Local\Programs\Cowork\Cowork.exe` or similar — check your existing Cowork shortcut to confirm).
5. Conditions: same as above (untick AC requirement, tick wake the computer).
6. OK.

---

## Part 5 — Verify it actually works

Two ways to test, in order of cheapness:

**Quick test (no overnight wait)**
1. Edit your `Wake for AI Dashboard` task → Triggers → change the time to 3 minutes from now.
2. Put your PC to sleep (Start → Power → Sleep).
3. Wait. The PC should wake at the scheduled minute and stay awake briefly. Cowork should be visible in the taskbar.
4. After the test, set the trigger back to 06:55.

**Real test (overnight)**
1. Tonight: leave Cowork open, let the PC sleep normally.
2. Tomorrow morning, open the dashboard. The news section should show today's date in the "Updated …" line and fresh headlines.
3. If it doesn't, check the Cowork **Scheduled** sidebar — the task's last run timestamp will tell you whether it fired.

---

## Troubleshooting

**The PC wakes but Cowork didn't refresh.**
Open Cowork's Scheduled section, click into `ai-dashboard-daily-refresh`, hit **Run now** once. Future runs will use any tool approvals from that first manual run, so this is also a good thing to do once after creating the task.

**The PC didn't wake at all.**
Open Command Prompt and run `powercfg -waketimers`. If it says wake timers are disabled by group policy or the BIOS, you may need to enable them in BIOS (look for "Wake on RTC" or "Wake from S3"). On some laptops, **Modern Standby (S0)** doesn't honour wake timers the way classic sleep (S3) does — check `powercfg -a` to see which sleep states your PC supports.

**The task ran but Cowork was locked behind the Windows login screen.**
Cowork still runs in the background even at the lock screen. The refresh will happen; you'll see it next time you unlock.

**Laptop on battery, didn't wake.**
You probably left "Start the task only if the computer is on AC power" ticked in Conditions. Untick it.

---

## What this doesn't solve

- PC fully powered off (shutdown). Use sleep or hibernate instead.
- Cowork uninstalled or signed out.
- No internet at 7am (the news fetch needs WebSearch).

If any of those happen, the task will just retry on next launch — your dashboard won't break, it'll just show yesterday's news until the next successful run.

---

*Setup time: about 10 minutes. One-time configuration.*
