# ============================================================
# TYMetro A1-A9 Tracker Core - V2
#
# Schedule engine + conservative TDX LiveBoard correction.
#
# Data sources already present in Home Assistant:
#   sensor.tymetro_static_model_raw
#   sensor.tymetro_liveboard_raw
#   input_select.tymetro_direction
#   input_boolean.tymetro_live_mode
#
# Output entities:
#   sensor.tymetro_tracker
#   sensor.tymetro_led_frame_a
#   sensor.tymetro_led_frame_b
#
# Live matching strategy:
# - Schedule remains the trajectory backbone.
# - LiveBoard ETA is converted to an absolute service-day time.
# - ETA events are matched against scheduled stop events.
# - Each matched train receives a delay/early offset.
# - The offset shifts the whole train trajectory smoothly.
# - Old correction is retained briefly after the train passes its
#   last useful LiveBoard calibration station.
# - If LiveBoard is stale or matching is uncertain, fall back to
#   schedule instead of pretending the position is live.
# ============================================================


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def clock_to_service_seconds(text):
    if not text:
        return None

    parts = text.split(":")
    if len(parts) < 2:
        return None

    try:
        hour = int(parts[0])
        minute = int(parts[1])
        second = int(parts[2]) if len(parts) > 2 else 0
    except Exception:
        return None

    value = hour * 3600 + minute * 60 + second

    # Airport MRT service shortly after midnight belongs to the
    # previous operating day.
    if hour < 3:
        value += 86400

    return value


def iso_to_service_seconds(text):
    # TDX example:
    # 2026-08-22T21:39:04+08:00
    if not text or len(text) < 19:
        return None

    try:
        hour = int(text[11:13])
        minute = int(text[14:16])
        second = int(text[17:19])
    except Exception:
        return None

    value = hour * 3600 + minute * 60 + second

    if hour < 3:
        value += 86400

    return value


def destination_id(obj):
    return obj.get(
        "DestinationStationID",
        obj.get("DestinationStaionID", ""),
    )


def correction_key(prefix, anchor, destination, train_type, pattern):
    return "{}|{}|{}|{}|{}".format(
        prefix,
        anchor,
        destination,
        train_type,
        pattern,
    )


def median_int(values):
    if not values:
        return 0

    ordered = sorted(values)
    count = len(ordered)
    middle = count // 2

    if count % 2 == 1:
        return int(ordered[middle])

    return int((ordered[middle - 1] + ordered[middle]) / 2)


# ------------------------------------------------------------
# Read Home Assistant entities
# ------------------------------------------------------------

static_state = hass.states.get("sensor.tymetro_static_model_raw")
direction_state = hass.states.get("input_select.tymetro_direction")
live_mode_state = hass.states.get("input_boolean.tymetro_live_mode")
liveboard_state = hass.states.get("sensor.tymetro_liveboard_raw")
previous_tracker = hass.states.get("sensor.tymetro_tracker")


# ------------------------------------------------------------
# Basic validation
# ------------------------------------------------------------

if static_state is None or static_state.state != "ready":

    hass.states.set(
        "sensor.tymetro_tracker",
        "unavailable",
        {
            "friendly_name": "TYMetro Tracker",
            "reason": "Static model is not ready",
            "frame_a": 0,
            "frame_b": 0,
            "train_count": 0,
            "live_correction_active": False,
        },
    )

    hass.states.set(
        "sensor.tymetro_led_frame_a",
        0,
        {"friendly_name": "TYMetro LED Frame A"},
    )

    hass.states.set(
        "sensor.tymetro_led_frame_b",
        0,
        {"friendly_name": "TYMetro LED Frame B"},
    )

else:

    attrs = static_state.attributes

    s2s = attrs.get("s2s", [])
    timetable_a1 = attrs.get("timetable_a1", [])
    timetable_a8 = attrs.get("timetable_a8", [])

    direction_text = ""
    if direction_state is not None:
        direction_text = direction_state.state

    live_requested = (
        live_mode_state is not None
        and live_mode_state.state == "on"
    )


    # --------------------------------------------------------
    # Direction
    # --------------------------------------------------------

    if "A1" in direction_text:
        direction = "to_a1"
        direction_label = "← 往 A1 台北"
    else:
        direction = "to_a9"
        direction_label = "往 A9 林口 →"


    # --------------------------------------------------------
    # Current operating/service day
    # --------------------------------------------------------

    now_dt = dt_util.now()

    if now_dt.hour < 3:
        service_dt = now_dt - datetime.timedelta(days=1)
        now_seconds = (
            now_dt.hour * 3600
            + now_dt.minute * 60
            + now_dt.second
            + 86400
        )
    else:
        service_dt = now_dt
        now_seconds = (
            now_dt.hour * 3600
            + now_dt.minute * 60
            + now_dt.second
        )

    weekday_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    service_day_key = weekday_names[service_dt.weekday()]


    # --------------------------------------------------------
    # Build S2S lookup
    # --------------------------------------------------------

    runtime_local = {}
    runtime_express = {}

    for model in s2s:
        train_type = int(model.get("TrainType", 0))

        for travel in model.get("TravelTimes", []):
            from_station = travel.get("FromStationID", "")
            to_station = travel.get("ToStationID", "")
            run_time = int(travel.get("RunTime", 0))

            key = from_station + ">" + to_station

            if train_type == 1:
                runtime_local[key] = run_time
            elif train_type == 2:
                runtime_express[key] = run_time


    # --------------------------------------------------------
    # Model arrays
    # index 1 = A1 ... index 9 = A9
    # --------------------------------------------------------

    local_south_arr = [0] * 10
    local_south_dep = [0] * 10

    local_north_arr = [0] * 10
    local_north_dep = [0] * 10


    # --------------------------------------------------------
    # LOCAL southbound A1 -> A9
    # --------------------------------------------------------

    local_south_arr[1] = 0
    local_south_dep[1] = 0

    for station_number in range(2, 10):
        key = "A1>A{}".format(station_number)
        local_south_arr[station_number] = int(
            runtime_local.get(key, 0)
        )

    for station_number in range(1, 9):
        from_station = "A{}".format(station_number)
        to_station = "A{}".format(station_number + 1)

        direct_run = int(
            runtime_local.get(
                from_station + ">" + to_station,
                0,
            )
        )

        dwell = (
            local_south_arr[station_number + 1]
            - local_south_arr[station_number]
            - direct_run
        )

        if dwell < 0:
            dwell = 0

        local_south_dep[station_number] = (
            local_south_arr[station_number] + dwell
        )

    local_south_dep[9] = local_south_arr[9] + 60


    # --------------------------------------------------------
    # LOCAL northbound A8 -> A1
    # Values are relative to A8 departure.
    # --------------------------------------------------------

    local_north_arr[8] = 0
    local_north_dep[8] = 0

    for station_number in range(7, 0, -1):
        key = "A8>A{}".format(station_number)
        local_north_arr[station_number] = int(
            runtime_local.get(key, 0)
        )

    for station_number in range(7, 1, -1):
        current_station = "A{}".format(station_number)
        next_station = "A{}".format(station_number - 1)

        direct_run = int(
            runtime_local.get(
                current_station + ">" + next_station,
                0,
            )
        )

        dwell = (
            local_north_arr[station_number - 1]
            - local_north_arr[station_number]
            - direct_run
        )

        if dwell < 0:
            dwell = 0

        local_north_dep[station_number] = (
            local_north_arr[station_number] + dwell
        )

    local_north_dep[1] = local_north_arr[1] + 60


    # --------------------------------------------------------
    # EXPRESS southbound synthetic pass-times
    # Actual stops in A1-A9: A1, A3, A8
    # --------------------------------------------------------

    express_south_arr = [0] * 10
    express_south_dep = [0] * 10

    express_south_arr[1] = 0
    express_south_dep[1] = 0

    a1_a3_express = int(
        runtime_express.get("A1>A3", 480)
    )

    a1_a2_local = int(runtime_local.get("A1>A2", 300))
    a2_a3_local = int(runtime_local.get("A2>A3", 180))

    section_weight = a1_a2_local + a2_a3_local
    if section_weight <= 0:
        section_weight = 480

    express_south_arr[2] = int(
        a1_a3_express * a1_a2_local / section_weight
    )
    express_south_dep[2] = express_south_arr[2]
    express_south_arr[3] = a1_a3_express

    a1_a8_express = int(
        runtime_express.get("A1>A8", 1260)
    )
    a3_a8_express = int(
        runtime_express.get("A3>A8", 660)
    )

    dwell_a3 = (
        a1_a8_express
        - a1_a3_express
        - a3_a8_express
    )
    if dwell_a3 < 0:
        dwell_a3 = 0

    express_south_dep[3] = (
        express_south_arr[3] + dwell_a3
    )

    express_section_start = express_south_dep[3]
    express_section_run = a3_a8_express

    segment_starts = [3, 4, 5, 6, 7]
    local_weight = 0

    for station_number in segment_starts:
        local_weight += int(
            runtime_local.get(
                "A{}>A{}".format(
                    station_number,
                    station_number + 1,
                ),
                0,
            )
        )

    if local_weight <= 0:
        local_weight = 1

    accumulated = 0

    for station_number in segment_starts:
        segment_run = int(
            runtime_local.get(
                "A{}>A{}".format(
                    station_number,
                    station_number + 1,
                ),
                0,
            )
        )

        accumulated += segment_run
        next_station = station_number + 1

        express_south_arr[next_station] = int(
            express_section_start
            + express_section_run * accumulated / local_weight
        )
        express_south_dep[next_station] = (
            express_south_arr[next_station]
        )

    express_south_arr[8] = a1_a8_express

    a1_a12_express = int(
        runtime_express.get("A1>A12", 2160)
    )
    a8_a12_express = int(
        runtime_express.get("A8>A12", 840)
    )

    dwell_a8 = (
        a1_a12_express
        - a1_a8_express
        - a8_a12_express
    )
    if dwell_a8 < 0:
        dwell_a8 = 0

    express_south_dep[8] = (
        express_south_arr[8] + dwell_a8
    )

    local_a8_a9 = int(runtime_local.get("A8>A9", 180))
    local_a8_a12 = int(runtime_local.get("A8>A12", 1080))

    if local_a8_a12 <= 0:
        local_a8_a12 = 1080

    express_a8_a9 = int(
        a8_a12_express * local_a8_a9 / local_a8_a12
    )
    if express_a8_a9 <= 0:
        express_a8_a9 = 150

    express_south_arr[9] = (
        express_south_dep[8] + express_a8_a9
    )
    express_south_dep[9] = express_south_arr[9]


    # --------------------------------------------------------
    # EXPRESS northbound A8 -> A1
    # --------------------------------------------------------

    express_north_arr = [0] * 10
    express_north_dep = [0] * 10

    express_north_arr[8] = 0
    express_north_dep[8] = 0

    a8_a3_express = int(
        runtime_express.get("A8>A3", 780)
    )
    a8_a1_express = int(
        runtime_express.get("A8>A1", 1380)
    )
    a3_a1_express = int(
        runtime_express.get("A3>A1", 480)
    )

    reverse_segments = [8, 7, 6, 5, 4]
    reverse_weight = 0

    for station_number in reverse_segments:
        reverse_weight += int(
            runtime_local.get(
                "A{}>A{}".format(
                    station_number,
                    station_number - 1,
                ),
                0,
            )
        )

    if reverse_weight <= 0:
        reverse_weight = 1

    accumulated = 0

    for station_number in reverse_segments:
        segment_run = int(
            runtime_local.get(
                "A{}>A{}".format(
                    station_number,
                    station_number - 1,
                ),
                0,
            )
        )

        accumulated += segment_run
        next_station = station_number - 1

        express_north_arr[next_station] = int(
            a8_a3_express * accumulated / reverse_weight
        )
        express_north_dep[next_station] = (
            express_north_arr[next_station]
        )

    express_north_arr[3] = a8_a3_express

    dwell_a3_north = (
        a8_a1_express
        - a8_a3_express
        - a3_a1_express
    )
    if dwell_a3_north < 0:
        dwell_a3_north = 0

    express_north_dep[3] = (
        express_north_arr[3] + dwell_a3_north
    )

    a3_a2_local = int(runtime_local.get("A3>A2", 180))
    a2_a1_local = int(runtime_local.get("A2>A1", 300))

    local_weight = a3_a2_local + a2_a1_local
    if local_weight <= 0:
        local_weight = 480

    express_north_arr[2] = int(
        express_north_dep[3]
        + a3_a1_express * a3_a2_local / local_weight
    )
    express_north_dep[2] = express_north_arr[2]

    express_north_arr[1] = a8_a1_express
    express_north_dep[1] = express_north_arr[1] + 60


    # ========================================================
    # LIVEBOARD CORRECTION MODEL
    # ========================================================

    live_records = []
    if liveboard_state is not None:
        # Home Assistant python_script sandbox does not expose
        # list/dict as normal Python type objects, so avoid
        # isinstance(..., list/dict) here. The template sensor
        # publishes records as a native list.
        raw_records = liveboard_state.attributes.get("records", [])
        if raw_records:
            live_records = raw_records

    live_source_seconds = None
    live_source_text = ""

    if live_requested:
        for record in live_records:
            if int(record.get("ServiceStatus", 0)) != 0:
                continue

            src_text = record.get("SrcUpdateTime", "")
            src_seconds = iso_to_service_seconds(src_text)

            if src_seconds is None:
                continue

            if (
                live_source_seconds is None
                or src_seconds > live_source_seconds
            ):
                live_source_seconds = src_seconds
                live_source_text = src_text

    live_source_age_seconds = None
    live_fresh = False

    if live_requested and live_source_seconds is not None:
        live_source_age_seconds = now_seconds - live_source_seconds

        # TDX source data in the observed payload can itself be
        # roughly 1-2 minutes old. Allow up to 5 minutes, but do
        # not label older data as live.
        if (
            live_source_age_seconds >= -30
            and live_source_age_seconds <= 300
        ):
            live_fresh = True


    # --------------------------------------------------------
    # Retain recent per-train correction from the previous run.
    # This matters after a train has passed the last useful
    # LiveBoard calibration stop (e.g. express after A3/A8).
    # --------------------------------------------------------

    live_corrections = {}

    if live_requested and previous_tracker is not None:
        previous_corrections = previous_tracker.attributes.get(
            "live_corrections",
            {},
        )

        if previous_corrections:
            for key in previous_corrections:
                item = previous_corrections.get(key, {})

                try:
                    updated_service_seconds = int(
                        item.get("updated_service_seconds", 0)
                    )
                except Exception:
                    updated_service_seconds = 0

                age = now_seconds - updated_service_seconds

                if age >= 0 and age <= 1800:
                    live_corrections[key] = item


    # --------------------------------------------------------
    # Build scheduled stop events eligible for matching.
    # --------------------------------------------------------

    schedule_events = []

    if live_requested and live_fresh:

        if direction == "to_a9":

            for block in timetable_a1:
                if int(block.get("Direction", -1)) != 0:
                    continue

                service_day = block.get("ServiceDay", {})
                if not service_day.get(service_day_key, False):
                    continue

                destination = destination_id(block)

                for timetable in block.get("Timetables", []):
                    departure_text = timetable.get(
                        "DepartureTime",
                        "",
                    )
                    departure_seconds = clock_to_service_seconds(
                        departure_text
                    )

                    if departure_seconds is None:
                        continue

                    train_type = int(timetable.get("TrainType", 1))
                    pattern = timetable.get("StoppingPatternID", "")

                    key = correction_key(
                        "S",
                        departure_text,
                        destination,
                        train_type,
                        pattern,
                    )

                    if train_type == 2:
                        arr = express_south_arr
                        stop_numbers = [1, 3, 8]
                    else:
                        arr = local_south_arr
                        stop_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9]

                    for station_number in stop_numbers:
                        scheduled_sec = (
                            departure_seconds + arr[station_number]
                        )

                        if (
                            scheduled_sec < live_source_seconds - 900
                            or scheduled_sec > live_source_seconds + 4500
                        ):
                            continue

                        schedule_events.append(
                            {
                                "train_key": key,
                                "station": "A{}".format(station_number),
                                "destination": destination,
                                "scheduled_sec": scheduled_sec,
                            }
                        )

        else:

            for block in timetable_a8:
                if int(block.get("Direction", -1)) != 1:
                    continue

                service_day = block.get("ServiceDay", {})
                if not service_day.get(service_day_key, False):
                    continue

                destination = destination_id(block)

                for timetable in block.get("Timetables", []):
                    arrival_text = timetable.get("ArrivalTime", "")
                    departure_text = timetable.get("DepartureTime", "")

                    arrival_a8 = clock_to_service_seconds(arrival_text)
                    departure_a8 = clock_to_service_seconds(departure_text)

                    if arrival_a8 is None or departure_a8 is None:
                        continue

                    train_type = int(timetable.get("TrainType", 1))
                    pattern = timetable.get("StoppingPatternID", "")

                    key = correction_key(
                        "N",
                        arrival_text,
                        destination,
                        train_type,
                        pattern,
                    )

                    if train_type == 2:
                        arr = express_north_arr
                        stop_numbers = [8, 3]
                    else:
                        arr = local_north_arr
                        stop_numbers = [8, 7, 6, 5, 4, 3, 2]

                    for station_number in stop_numbers:
                        if station_number == 8:
                            scheduled_sec = arrival_a8
                        else:
                            scheduled_sec = (
                                departure_a8 + arr[station_number]
                            )

                        if (
                            scheduled_sec < live_source_seconds - 900
                            or scheduled_sec > live_source_seconds + 4500
                        ):
                            continue

                        schedule_events.append(
                            {
                                "train_key": key,
                                "station": "A{}".format(station_number),
                                "destination": destination,
                                "scheduled_sec": scheduled_sec,
                            }
                        )


    # --------------------------------------------------------
    # Convert LiveBoard ETA records into absolute service-day
    # stop events.
    # --------------------------------------------------------

    live_events = []

    if live_requested and live_fresh:
        for record in live_records:
            if int(record.get("ServiceStatus", 0)) != 0:
                continue

            station = record.get("StationID", "")
            if station not in [
                "A1", "A2", "A3", "A4", "A5",
                "A6", "A7", "A8", "A9",
            ]:
                continue

            destination = destination_id(record)

            if direction == "to_a1":
                if destination != "A1":
                    continue
            else:
                if destination == "A1":
                    continue

            try:
                estimate_minutes = int(record.get("EstimateTime", -1))
            except Exception:
                estimate_minutes = -1

            if estimate_minutes < 0:
                continue

            src_seconds = iso_to_service_seconds(
                record.get("SrcUpdateTime", "")
            )
            if src_seconds is None:
                continue

            live_events.append(
                {
                    "station": station,
                    "destination": destination,
                    "live_sec": src_seconds + estimate_minutes * 60,
                }
            )


    # --------------------------------------------------------
    # Conservative event matching.
    #
    # Southbound destinations separate A13/A22 traffic well, so
    # a larger tolerance is acceptable.
    # Northbound all trains end at A1 and local/express are mixed,
    # so use a tighter tolerance to avoid matching the wrong train.
    # --------------------------------------------------------

    delay_samples = {}
    matched_event_count = 0

    if live_requested and live_fresh:
        max_diff = 720 if direction == "to_a9" else 240

        pairs = []

        for schedule_index in range(0, len(schedule_events)):
            schedule_event = schedule_events[schedule_index]

            for live_index in range(0, len(live_events)):
                live_event = live_events[live_index]

                if (
                    schedule_event.get("station")
                    != live_event.get("station")
                ):
                    continue

                schedule_destination = schedule_event.get(
                    "destination",
                    "",
                )
                live_destination = live_event.get(
                    "destination",
                    "",
                )

                if (
                    schedule_destination
                    and live_destination
                    and schedule_destination != live_destination
                ):
                    continue

                diff = abs(
                    int(live_event.get("live_sec", 0))
                    - int(schedule_event.get("scheduled_sec", 0))
                )

                if diff <= max_diff:
                    pairs.append((diff, schedule_index, live_index))

        pairs.sort()

        used_schedule_events = []
        used_live_events = []

        for pair in pairs:
            schedule_index = pair[1]
            live_index = pair[2]

            if schedule_index in used_schedule_events:
                continue
            if live_index in used_live_events:
                continue

            schedule_event = schedule_events[schedule_index]
            live_event = live_events[live_index]

            train_key = schedule_event.get("train_key", "")

            delay = (
                int(live_event.get("live_sec", 0))
                - int(schedule_event.get("scheduled_sec", 0))
            )

            if train_key not in delay_samples:
                delay_samples[train_key] = []

            delay_samples[train_key].append(delay)
            matched_event_count += 1

            used_schedule_events.append(schedule_index)
            used_live_events.append(live_index)


        # One train can be visible in several station LiveBoards.
        # Median reduces damage from a single incorrect event match.
        for train_key in delay_samples:
            samples = delay_samples.get(train_key, [])
            delay_seconds = median_int(samples)

            live_corrections[train_key] = {
                "delay_seconds": delay_seconds,
                "sample_count": len(samples),
                "updated_service_seconds": now_seconds,
                "source_update": live_source_text,
            }


    live_match_count = len(delay_samples)
    live_correction_active = (
        live_requested
        and live_fresh
        and len(live_corrections) > 0
    )


    # --------------------------------------------------------
    # Prepare output
    # --------------------------------------------------------

    frame_a = 0
    frame_b = 0
    trains = []
    train_count = 0
    corrected_train_count = 0


    # ========================================================
    # SOUTHBOUND / toward A9
    # ========================================================

    if direction == "to_a9":

        for block in timetable_a1:
            if int(block.get("Direction", -1)) != 0:
                continue

            service_day = block.get("ServiceDay", {})
            if not service_day.get(service_day_key, False):
                continue

            destination = destination_id(block)

            for timetable in block.get("Timetables", []):
                departure_text = timetable.get("DepartureTime", "")
                departure_seconds = clock_to_service_seconds(
                    departure_text
                )

                if departure_seconds is None:
                    continue

                train_type = int(timetable.get("TrainType", 1))
                stopping_pattern = timetable.get(
                    "StoppingPatternID",
                    "",
                )

                train_key = correction_key(
                    "S",
                    departure_text,
                    destination,
                    train_type,
                    stopping_pattern,
                )

                correction = live_corrections.get(train_key, {})
                delay_seconds = 0
                corrected = False

                if live_correction_active and correction:
                    delay_seconds = int(
                        correction.get("delay_seconds", 0)
                    )
                    corrected = True

                effective_departure_seconds = (
                    departure_seconds + delay_seconds
                )
                elapsed = now_seconds - effective_departure_seconds

                if train_type == 2:
                    arr = express_south_arr
                    dep = express_south_dep
                    train_type_name = "express"
                else:
                    arr = local_south_arr
                    dep = local_south_dep
                    train_type_name = "local"

                if elapsed < 0:
                    continue
                if elapsed > dep[9] + 30:
                    continue

                for station_number in range(1, 10):

                    # At station
                    if (
                        elapsed >= arr[station_number]
                        and elapsed <= dep[station_number]
                    ):
                        bit = 1 << (station_number - 1)
                        frame_a = frame_a | bit
                        frame_b = frame_b | bit

                        trains.append(
                            {
                                "key": train_key,
                                "type": train_type_name,
                                "train_type": train_type,
                                "pattern": stopping_pattern,
                                "destination": destination,
                                "state": "station",
                                "station": "A{}".format(station_number),
                                "from": "A{}".format(station_number),
                                "to": "A{}".format(station_number),
                                "progress": 0.0,
                                "anchor": departure_text,
                                "live_corrected": corrected,
                                "delay_seconds": delay_seconds,
                                "delay_minutes": round(delay_seconds / 60.0, 1),
                            }
                        )

                        train_count += 1
                        if corrected:
                            corrected_train_count += 1
                        break

                    # Between stations
                    if station_number < 9:
                        segment_start = dep[station_number]
                        segment_end = arr[station_number + 1]

                        if (
                            elapsed > segment_start
                            and elapsed < segment_end
                        ):
                            segment_duration = (
                                segment_end - segment_start
                            )

                            if segment_duration <= 0:
                                progress = 0.5
                            else:
                                progress = (
                                    elapsed - segment_start
                                ) / segment_duration

                            from_bit = 1 << (station_number - 1)
                            to_bit = 1 << station_number

                            if progress < 0.333:
                                frame_a = frame_a | from_bit
                                frame_b = frame_b | from_bit
                            elif progress < 0.667:
                                frame_a = frame_a | from_bit
                                frame_b = frame_b | to_bit
                            else:
                                frame_a = frame_a | to_bit
                                frame_b = frame_b | to_bit

                            trains.append(
                                {
                                    "key": train_key,
                                    "type": train_type_name,
                                    "train_type": train_type,
                                    "pattern": stopping_pattern,
                                    "destination": destination,
                                    "state": "between",
                                    "station": "",
                                    "from": "A{}".format(station_number),
                                    "to": "A{}".format(station_number + 1),
                                    "progress": round(progress, 3),
                                    "anchor": departure_text,
                                    "live_corrected": corrected,
                                    "delay_seconds": delay_seconds,
                                    "delay_minutes": round(delay_seconds / 60.0, 1),
                                }
                            )

                            train_count += 1
                            if corrected:
                                corrected_train_count += 1
                            break


    # ========================================================
    # NORTHBOUND / toward A1
    # ========================================================

    else:

        for block in timetable_a8:
            if int(block.get("Direction", -1)) != 1:
                continue

            service_day = block.get("ServiceDay", {})
            if not service_day.get(service_day_key, False):
                continue

            destination = destination_id(block)

            for timetable in block.get("Timetables", []):
                arrival_text = timetable.get("ArrivalTime", "")
                departure_text = timetable.get("DepartureTime", "")

                arrival_a8 = clock_to_service_seconds(arrival_text)
                departure_a8 = clock_to_service_seconds(departure_text)

                if arrival_a8 is None or departure_a8 is None:
                    continue

                train_type = int(timetable.get("TrainType", 1))
                stopping_pattern = timetable.get(
                    "StoppingPatternID",
                    "",
                )

                train_key = correction_key(
                    "N",
                    arrival_text,
                    destination,
                    train_type,
                    stopping_pattern,
                )

                correction = live_corrections.get(train_key, {})
                delay_seconds = 0
                corrected = False

                if live_correction_active and correction:
                    delay_seconds = int(
                        correction.get("delay_seconds", 0)
                    )
                    corrected = True

                arrival_a8 = arrival_a8 + delay_seconds
                departure_a8 = departure_a8 + delay_seconds

                if train_type == 2:
                    arr = express_north_arr
                    dep = express_north_dep
                    train_type_name = "express"
                    pre_a8_runtime = express_a8_a9
                else:
                    arr = local_north_arr
                    dep = local_north_dep
                    train_type_name = "local"
                    pre_a8_runtime = int(
                        runtime_local.get("A9>A8", 180)
                    )

                # Before A8: show A9 -> A8 approach
                pre_start = arrival_a8 - pre_a8_runtime

                if (
                    now_seconds >= pre_start
                    and now_seconds < arrival_a8
                ):
                    duration = arrival_a8 - pre_start

                    if duration <= 0:
                        progress = 0.5
                    else:
                        progress = (
                            now_seconds - pre_start
                        ) / duration

                    a9_bit = 1 << 8
                    a8_bit = 1 << 7

                    if progress < 0.333:
                        frame_a = frame_a | a9_bit
                        frame_b = frame_b | a9_bit
                    elif progress < 0.667:
                        frame_a = frame_a | a9_bit
                        frame_b = frame_b | a8_bit
                    else:
                        frame_a = frame_a | a8_bit
                        frame_b = frame_b | a8_bit

                    trains.append(
                        {
                            "key": train_key,
                            "type": train_type_name,
                            "train_type": train_type,
                            "pattern": stopping_pattern,
                            "destination": destination,
                            "state": "between",
                            "station": "",
                            "from": "A9",
                            "to": "A8",
                            "progress": round(progress, 3),
                            "anchor": arrival_text,
                            "live_corrected": corrected,
                            "delay_seconds": delay_seconds,
                            "delay_minutes": round(delay_seconds / 60.0, 1),
                        }
                    )

                    train_count += 1
                    if corrected:
                        corrected_train_count += 1
                    continue

                # Dwelling at A8 using timetable arrival/departure
                if (
                    now_seconds >= arrival_a8
                    and now_seconds <= departure_a8
                ):
                    a8_bit = 1 << 7
                    frame_a = frame_a | a8_bit
                    frame_b = frame_b | a8_bit

                    trains.append(
                        {
                            "key": train_key,
                            "type": train_type_name,
                            "train_type": train_type,
                            "pattern": stopping_pattern,
                            "destination": destination,
                            "state": "station",
                            "station": "A8",
                            "from": "A8",
                            "to": "A8",
                            "progress": 0.0,
                            "anchor": departure_text,
                            "live_corrected": corrected,
                            "delay_seconds": delay_seconds,
                            "delay_minutes": round(delay_seconds / 60.0, 1),
                        }
                    )

                    train_count += 1
                    if corrected:
                        corrected_train_count += 1
                    continue

                # After A8 toward A1
                elapsed = now_seconds - departure_a8

                if elapsed < 0:
                    continue
                if elapsed > dep[1] + 30:
                    continue

                path = [8, 7, 6, 5, 4, 3, 2, 1]

                for index in range(0, len(path)):
                    station_number = path[index]

                    if station_number == 8:
                        station_arr = 0
                        station_dep = 0
                    else:
                        station_arr = arr[station_number]
                        station_dep = dep[station_number]

                    # At station
                    if (
                        elapsed >= station_arr
                        and elapsed <= station_dep
                    ):
                        bit = 1 << (station_number - 1)
                        frame_a = frame_a | bit
                        frame_b = frame_b | bit

                        trains.append(
                            {
                                "key": train_key,
                                "type": train_type_name,
                                "train_type": train_type,
                                "pattern": stopping_pattern,
                                "destination": destination,
                                "state": "station",
                                "station": "A{}".format(station_number),
                                "from": "A{}".format(station_number),
                                "to": "A{}".format(station_number),
                                "progress": 0.0,
                                "anchor": departure_text,
                                "live_corrected": corrected,
                                "delay_seconds": delay_seconds,
                                "delay_minutes": round(delay_seconds / 60.0, 1),
                            }
                        )

                        train_count += 1
                        if corrected:
                            corrected_train_count += 1
                        break

                    # Between stations
                    if index < len(path) - 1:
                        next_station = path[index + 1]

                        if station_number == 8:
                            segment_start = 0
                        else:
                            segment_start = dep[station_number]

                        segment_end = arr[next_station]

                        if (
                            elapsed > segment_start
                            and elapsed < segment_end
                        ):
                            duration = segment_end - segment_start

                            if duration <= 0:
                                progress = 0.5
                            else:
                                progress = (
                                    elapsed - segment_start
                                ) / duration

                            from_bit = 1 << (station_number - 1)
                            to_bit = 1 << (next_station - 1)

                            if progress < 0.333:
                                frame_a = frame_a | from_bit
                                frame_b = frame_b | from_bit
                            elif progress < 0.667:
                                frame_a = frame_a | from_bit
                                frame_b = frame_b | to_bit
                            else:
                                frame_a = frame_a | to_bit
                                frame_b = frame_b | to_bit

                            trains.append(
                                {
                                    "key": train_key,
                                    "type": train_type_name,
                                    "train_type": train_type,
                                    "pattern": stopping_pattern,
                                    "destination": destination,
                                    "state": "between",
                                    "station": "",
                                    "from": "A{}".format(station_number),
                                    "to": "A{}".format(next_station),
                                    "progress": round(progress, 3),
                                    "anchor": departure_text,
                                    "live_corrected": corrected,
                                    "delay_seconds": delay_seconds,
                                    "delay_minutes": round(delay_seconds / 60.0, 1),
                                }
                            )

                            train_count += 1
                            if corrected:
                                corrected_train_count += 1
                            break


    # --------------------------------------------------------
    # Publish HA states
    # --------------------------------------------------------

    if not live_requested:
        tracker_mode = "schedule"
    elif not live_fresh:
        tracker_mode = "schedule_live_stale"
    elif live_correction_active:
        tracker_mode = "live"
    else:
        tracker_mode = "schedule_live_pending"

    tracker_attributes = {
        "friendly_name": "TYMetro Tracker",
        "direction": direction,
        "direction_label": direction_label,
        "mode": tracker_mode,
        "live_requested": live_requested,
        "live_correction_active": live_correction_active,
        "live_source_update": live_source_text,
        "live_source_age_seconds": live_source_age_seconds,
        "live_match_count": live_match_count,
        "live_matched_event_count": matched_event_count,
        "corrected_train_count": corrected_train_count,
        "service_day": service_day_key,
        "updated_at": now_dt.isoformat(),
        "train_count": train_count,
        "frame_a": frame_a,
        "frame_b": frame_b,
        "trains": trains,
        "live_corrections": live_corrections,
    }

    hass.states.set(
        "sensor.tymetro_tracker",
        tracker_mode,
        tracker_attributes,
    )

    hass.states.set(
        "sensor.tymetro_led_frame_a",
        frame_a,
        {
            "friendly_name": "TYMetro LED Frame A",
            "direction": direction,
            "train_count": train_count,
            "mode": tracker_mode,
        },
    )

    hass.states.set(
        "sensor.tymetro_led_frame_b",
        frame_b,
        {
            "friendly_name": "TYMetro LED Frame B",
            "direction": direction,
            "train_count": train_count,
            "mode": tracker_mode,
        },
    )
