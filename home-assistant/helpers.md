# Required Home Assistant Helpers

Create these from:

```text
Settings -> Devices & services -> Helpers
```

## 1. Direction selector

Type: **Dropdown / Input select**

Name:

```text
TYMetro Direction
```

Entity ID:

```text
input_select.tymetro_direction
```

Options must match exactly:

```text
← 往 A1 台北
往 A9 林口 →
```

## 2. Live Mode

Type: **Toggle / Input boolean**

Name:

```text
TYMetro Live Mode
```

Entity ID:

```text
input_boolean.tymetro_live_mode
```

Behavior:

- OFF = schedule simulation only
- ON = request TDX LiveBoard and attempt realtime correction

## 3. Live Session timer

Type: **Timer**

Name:

```text
TYMetro Live Session
```

Entity ID:

```text
timer.tymetro_live_session
```

Duration:

```text
00:15:00
```

Recommended: do not restore the timer across Home Assistant restarts. A Live session should be user-initiated and temporary.
