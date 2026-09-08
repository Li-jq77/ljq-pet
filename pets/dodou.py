"""豆豆智能体：宠物问诊与遛狗天气的本地服务。

问诊支持可选的 OpenAI 兼容大模型，未配置 Key 时会使用内置的
宠物护理知识给出初步观察建议。天气数据来自无需 Key 的 Open-Meteo。
"""

import json
import os
import ipaddress
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta


DEFAULT_CITY = "广州"
DEFAULT_LAT = 23.1291
DEFAULT_LON = 113.2644

SYSTEM_PROMPT = (
    "你是宠物门店里的智能体豆豆。全程以“豆豆”的第三人称与用户交流，"
    "绝不使用“我”自称，提到自己时只说“豆豆”。"
    "你擅长宠物常见症状的初步居家观察、护理和就医时机建议，"
    "但你不做疾病诊断，也不替代兽医；遇到危急信号要明确建议尽快就医。"
    "回答简洁、温柔、口语化，先说观察重点，再给可执行建议。"
)


def _http_json(url, timeout=10):
    request = urllib.request.Request(url, headers={"User-Agent": "PetAgentDodou/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def is_weather_intent(message):
    return any(
        keyword in message
        for keyword in (
            "天气",
            "下雨",
            "遛狗",
            "遛弯",
            "适合遛",
            "出去遛",
            "适合散步",
            "出去散步",
            "散步天气",
            "出门遛",
            "风力",
            "气温",
            "预报",
            "要不要带伞",
        )
    )


def extract_city(message):
    """尝试从一句中文里找出用户想查的城市。"""
    clean = message.replace(" ", "").replace("，", ",").replace("。", ",").replace("？", ",").replace("?", ",")
    patterns = [
        (
            r"(?:帮我查一下|帮我看看|帮我看下|帮我查|查一下|想知道|看看|去|到|在|查|看|^)"
            r"([\u4e00-\u9fa5]{2,8}?)"
            r"(?=今天|明天|后天|现在|天气|气温|适不适合遛狗|适合遛狗|遛狗天气)"
        ),
        r"([\u4e00-\u9fa5]{2,8}(?:省|市|区|县|州))",
    ]
    for pattern in patterns:
        match = re.search(pattern, clean)
        if match:
            city = match.group(1).strip()
            city = re.sub(r"^(?:帮我查|查一下|看看|去|到|在)", "", city)
            time_words = ("今天", "明天", "后天", "现在", "昨晚", "刚才", "宠物", "狗狗", "小猫", "猫咪")
            if city and city not in time_words:
                return city
    return ""


def _geocode_city(city):
    clean_city = city.strip().replace("市", "").replace("省", "").replace("区", "").replace("县", "")
    url = "https://geocoding-api.open-meteo.com/v1/search?" + urllib.parse.urlencode(
        {
            "name": clean_city,
            "count": 1,
            "language": "zh",
            "format": "json",
        }
    )
    data = _http_json(url)
    results = data.get("results") or []
    if not results:
        raise ValueError(f"找不到城市：{city}")
    first = results[0]
    return first.get("name") or city, first["latitude"], first["longitude"]


def resolve_location(city="", lat=None, lon=None):
    """返回 (展示名, lat, lon)。优先使用坐标，否则解析城市名，最后用默认店址。"""
    if lat is not None and lon is not None:
        return city or "当前位置", float(lat), float(lon)
    if city:
        return _geocode_city(city)
    return DEFAULT_CITY, DEFAULT_LAT, DEFAULT_LON


def _weather_code(weather_code):
    table = {
        0: ("☀️", "晴朗"),
        1: ("🌤️", "大致晴朗"),
        2: ("⛅", "多云"),
        3: ("☁️", "阴天"),
        45: ("🌫️", "有雾"),
        48: ("🌫️", "雾凇"),
        51: ("🌦️", "毛毛雨"),
        53: ("🌦️", "小雨"),
        55: ("🌧️", "中雨"),
        56: ("🌧️", "冻毛毛雨"),
        57: ("🌧️", "冻雨"),
        61: ("🌧️", "小雨"),
        63: ("🌧️", "中雨"),
        65: ("🌧️", "大雨"),
        66: ("🌧️", "冻雨"),
        67: ("🌧️", "强冻雨"),
        71: ("🌨️", "小雪"),
        73: ("🌨️", "中雪"),
        75: ("❄️", "大雪"),
        77: ("❄️", "雪粒"),
        80: ("🌦️", "阵雨"),
        81: ("🌧️", "强阵雨"),
        82: ("⛈️", "暴雨"),
        85: ("🌨️", "阵雪"),
        86: ("❄️", "强阵雪"),
        95: ("⛈️", "雷雨"),
        96: ("⛈️", "雷雨伴冰雹"),
        99: ("⛈️", "强雷雨"),
    }
    return table.get(weather_code, ("🌡️", "天气变化"))


def _temperature_score(temp, feels=None):
    if temp is None and feels is None:
        return 0
    if feels is not None:
        if feels >= 35:
            return -5
        if feels >= 33:
            return -2
        if feels <= -10:
            return -4
    effective = temp if temp is not None else feels
    if effective is None:
        return 0
    if 10 <= effective <= 28:
        return 2
    if 0 <= effective < 10 or 28 < effective <= 33:
        return 0
    return -4


def _weather_score(current_code, temp, wind, rain, feels=None):
    score = _temperature_score(temp, feels)
    if current_code in (0, 1):
        score += 2
    elif current_code in (2, 3, 45, 48):
        score += 1
    elif current_code >= 71 or current_code in (80, 81, 82, 95, 96, 99):
        score -= 3
    elif current_code in (55, 56, 57, 63, 65, 66, 67):
        score -= 2
    if wind is not None and wind >= 35:
        score -= 2
    elif wind is not None and wind >= 22:
        score -= 1
    if rain is not None and rain > 0:
        score -= 1
    return score


def _openmeteo_weather_reply(city="", lat=None, lon=None):
    """返回一段以豆豆口吻描述的遛狗天气建议。"""
    try:
        label, resolved_lat, resolved_lon = resolve_location(city, lat, lon)
    except Exception:
        return {
            "ok": False,
            "text": (
                f"豆豆暂时没在天气服务里找到{city}的位置，"
                "可以确认一下城市名，或者直接让豆豆查广州的遛狗天气。"
            ),
        }
    try:
        params = {
            "latitude": resolved_lat,
            "longitude": resolved_lon,
            "current": (
                "temperature_2m,apparent_temperature,relative_humidity_2m,"
                "precipitation,weather_code,wind_speed_10m,is_day"
            ),
            "hourly": (
                "temperature_2m,precipitation_probability,precipitation,"
                "weather_code,wind_speed_10m,apparent_temperature"
            ),
            "forecast_days": 2,
            "timezone": "Asia/Shanghai",
        }
        url = "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)
        data = _http_json(url, timeout=9)
    except Exception:
        return {
            "ok": False,
            "text": (
                "豆豆现在连不上天气服务，可能是网络暂时不稳定。"
                "稍后再问豆豆一次，或者先按温度加减衣服、避开暴雨时段。"
            ),
        }

    current = data.get("current", {})
    temp = current.get("temperature_2m")
    feels = current.get("apparent_temperature")
    humidity = current.get("relative_humidity_2m")
    wind = current.get("wind_speed_10m")
    rain = current.get("precipitation")
    icon, desc = _weather_code(current.get("weather_code", 0))

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    now_text = current.get("time") or (times[0] if times else "")
    now_dt = None
    try:
        now_dt = datetime.fromisoformat(now_text.replace("Z", "+00:00"))
    except Exception:
        now_dt = datetime.now()
    if now_dt.tzinfo is not None:
        now_dt = now_dt.replace(tzinfo=None)
    start_hour = now_dt + timedelta(hours=1)
    next_scores = []
    next_desc = ""
    next_has_precip = False
    next_windy = False
    next_hot = False
    for i, time_text in enumerate(times):
        try:
            slot = datetime.fromisoformat(time_text.replace("Z", "+00:00"))
        except Exception:
            continue
        if slot.tzinfo is not None:
            slot = slot.replace(tzinfo=None)
        if start_hour <= slot <= now_dt + timedelta(hours=4):
            h_temp = hourly.get("temperature_2m", [None] * len(times))[i]
            h_wind = hourly.get("wind_speed_10m", [None] * len(times))[i]
            h_rain = hourly.get("precipitation", [None] * len(times))[i]
            h_code = hourly.get("weather_code", [0] * len(times))[i]
            h_feels = hourly.get("apparent_temperature", [None] * len(times))[i]
            next_scores.append(
                _weather_score(h_code, h_temp, h_wind, h_rain, h_feels)
            )
            precip_codes = (
                51, 53, 55, 56, 57, 61, 63, 65, 66, 67,
                71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99,
            )
            if (h_rain and h_rain > 0) or h_code in precip_codes:
                next_has_precip = True
            if h_wind is not None and h_wind >= 35:
                next_windy = True
            if (h_temp is not None and h_temp >= 33) or (
                h_feels is not None and h_feels >= 33
            ):
                next_hot = True
            if not next_desc:
                next_desc = _weather_code(h_code)[0] + _weather_code(h_code)[1]

    if next_scores:
        next_ok = sum(1 for score in next_scores if score >= 1)
        next_bad = sum(1 for score in next_scores if score <= -2)
        if next_bad >= 2:
            if next_hot:
                trend = "接下来 3 小时体感偏热，不太适合长时间遛狗。"
            elif next_windy:
                trend = "接下来 3 小时风力偏大，不太适合长时间遛狗。"
            elif next_has_precip:
                trend = "接下来 3 小时有雨雪，不太适合长时间遛狗。"
            else:
                trend = "接下来 3 小时天气条件一般，遛狗建议再等等。"
        elif next_ok >= 2:
            trend = "接下来 3 小时整体平稳，适合安排一次遛狗。"
        else:
            trend = "接下来 3 小时天气一般，可以短时遛一遛，随时观察天色。"
    else:
        trend = "接下来几小时天气变化不大，注意给毛孩子补水和防晒。"

    score = _weather_score(
        current.get("weather_code", 0),
        temp,
        wind,
        rain,
        feels,
    )
    if score <= -2:
        advice = "豆豆建议先不要遛狗，改用室内嗅闻或小游戏消耗精力。"
    elif score < 2:
        advice = "豆豆建议缩短散步时间，选在风小一点的时候出门。"
    else:
        advice = "豆豆觉得现在很适合遛狗，记得牵好绳子、带好水。"

    def number_text(value, suffix=""):
        return "" if value is None else f"{value:g}{suffix}"

    text_lines = [
        f"豆豆查看了{label}的遛狗天气：",
        f"{icon} 当前：{desc}，气温 {number_text(temp, '℃')}，体感 {number_text(feels, '℃')}",
    ]
    extras = []
    if humidity is not None:
        extras.append(f"湿度 {humidity:g}%")
    if wind is not None:
        extras.append(f"风力 {wind:g} km/h")
    if extras:
        text_lines.append("｜".join(extras))
    if next_desc:
        text_lines.append(f"接下来：{next_desc}")
    text_lines.extend([trend, advice])
    return {
        "ok": True,
        "kind": "weather",
        "text": "\n".join(text_lines),
        "city": label,
        "temperature": temp,
        "weather_code": current.get("weather_code", 0),
    }


def _is_private_ip(ip):
    if not ip or ip.lower() in ("localhost", "::1", "0.0.0.0", "127.0.0.1"):
        return True
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return True


def _amap_request(path, params, timeout=9):
    api_key = os.environ.get("AMAP_WEB_API_KEY", "").strip()
    if not api_key:
        raise ValueError("AMAP_WEB_API_KEY 未配置")
    request_params = dict(params)
    request_params.update({"key": api_key, "output": "json"})
    url = "https://restapi.amap.com/v3/" + path + "?" + urllib.parse.urlencode(request_params)
    data = _http_json(url, timeout=timeout)
    if str(data.get("status")) != "1":
        raise ValueError(str(data.get("info", "高德接口返回异常")))
    return data


def _amap_city_name(province, city, district=""):
    if city:
        return city
    if district and province and district != province:
        return province + district
    if province:
        return province
    return "当前位置"


def _amap_geocode(city):
    data = _amap_request("geocode/geo", {"address": city, "city": city})
    results = data.get("geocodes") or []
    if not results:
        raise ValueError(f"找不到城市：{city}")
    first = results[0]
    adcode = first.get("adcode", "")
    location = first.get("location", "")
    if "," in location:
        lon, lat = location.split(",", 1)
    else:
        lat = lon = ""
    display = _amap_city_name(
        first.get("province", ""),
        first.get("city", ""),
        first.get("district", ""),
    )
    return {
        "adcode": adcode,
        "lat": lat,
        "lon": lon,
        "display": display or city,
    }


def _amap_regeo(lat, lon):
    data = _amap_request(
        "geocode/regeo",
        {"location": f"{lon},{lat}", "extensions": "base"},
    )
    component = (data.get("regeocode") or {}).get("addressComponent") or {}
    adcode = component.get("adcode", "")
    display = _amap_city_name(
        component.get("province", ""),
        component.get("city", ""),
        component.get("district", ""),
    )
    return {
        "adcode": adcode,
        "display": display or "当前位置",
    }


def _amap_ip_location(remote_ip):
    if not remote_ip or _is_private_ip(remote_ip):
        return None
    data = _amap_request("ip", {"ip": remote_ip})
    adcode = data.get("adcode", "")
    if not adcode:
        return None
    display = _amap_city_name(
        data.get("province", ""),
        data.get("city", ""),
    )
    return {
        "adcode": adcode,
        "display": display or "当前位置",
    }


def _wind_high(wind_power):
    match = re.search(r"(\d+)", str(wind_power or ""))
    return bool(match and int(match.group(1)) >= 5)


def _amap_weather_score(weather_text, temp, wind_power):
    score = 0
    bad_weather = ("雨", "雪", "雷", "冰雹", "雾", "霾", "沙尘")
    if any(word in str(weather_text or "") for word in bad_weather):
        score -= 3
    if _wind_high(wind_power):
        score -= 2
    try:
        temperature = float(temp)
        if 10 <= temperature <= 28:
            score += 2
        elif 0 <= temperature < 10 or 28 < temperature <= 33:
            score += 0
        else:
            score -= 4
    except (TypeError, ValueError):
        pass
    return score


def _amap_weather_reply(city="", lat=None, lon=None, remote_ip=None):
    """使用高德 Web 服务查询天气，支持城市、经纬度和 IP 定位。"""
    location = None
    if lat is not None and lon is not None:
        location = _amap_regeo(lat, lon)
    elif city:
        location = _amap_geocode(city)
    else:
        location = _amap_ip_location(remote_ip)
    if not location:
        location = _amap_geocode(DEFAULT_CITY)
    if not location.get("adcode"):
        raise ValueError("高德没有返回城市编码")

    data = _amap_request(
        "weather/weatherInfo",
        {"city": location["adcode"], "extensions": "all"},
    )
    forecast = (data.get("forecasts") or [{}])[0]
    casts = forecast.get("casts") or []
    if not casts:
        raise ValueError("高德没有返回天气预报")

    today = casts[0]
    tomorrow = casts[1] if len(casts) > 1 else None
    display = location.get("display") or forecast.get("city") or "当前位置"

    day_score = _amap_weather_score(
        today.get("dayweather", ""),
        today.get("daytemp", ""),
        today.get("daypower", ""),
    )
    night_score = _amap_weather_score(
        today.get("nightweather", ""),
        today.get("nighttemp", ""),
        today.get("nightpower", ""),
    )
    current_hour = datetime.now().hour
    score = day_score if 6 <= current_hour < 19 else night_score
    if score <= -2:
        if day_score <= -2 and 6 <= current_hour < 19:
            advice = "豆豆建议白天先不要遛狗，高温或天气不适合时改成室内嗅闻或小游戏。"
        else:
            advice = "豆豆建议今天先不要遛狗，改为室内嗅闻或小游戏。"
    elif score < 1:
        advice = "豆豆建议缩短遛狗时间，避开雨雪大风或温差大的时段。"
    else:
        advice = "豆豆觉得今天适合遛狗，记得避开正午高温并带好水。"

    date_text = today.get("date", "")
    lines = [f"豆豆查看了{display}的高德天气："]
    if date_text:
        lines.append(f"今日 {date_text}")
    lines.extend(
        [
            f"白天：{today.get('dayweather', '')}，{today.get('daytemp', '')}℃，"
            f"{today.get('daywind', '')}{today.get('daypower', '')}级",
            f"夜间：{today.get('nightweather', '')}，{today.get('nighttemp', '')}℃，"
            f"{today.get('nightwind', '')}{today.get('nightpower', '')}级",
        ]
    )
    if tomorrow:
        lines.append(
            f"明天：白天 {tomorrow.get('dayweather', '')} "
            f"{tomorrow.get('daytemp', '')}℃ / 夜间 {tomorrow.get('nightweather', '')} "
            f"{tomorrow.get('nighttemp', '')}℃"
        )
    lines.append(advice)
    return {
        "ok": True,
        "kind": "weather",
        "text": "\n".join(lines),
        "city": display,
        "provider": "amap",
    }


def weather_reply(city="", lat=None, lon=None, remote_ip=None):
    """高德优先；未配置高德 Key 或高德失败时回退到 Open-Meteo。"""
    if os.environ.get("AMAP_WEB_API_KEY", "").strip():
        try:
            return _amap_weather_reply(city=city, lat=lat, lon=lon, remote_ip=remote_ip)
        except Exception:
            pass
    return _openmeteo_weather_reply(city=city, lat=lat, lon=lon)


def llm_reply(message, history):
    """调用 OpenAI 兼容接口；没有 Key 或调用失败时返回 None。"""
    api_key = os.environ.get("DODOU_AI_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.environ.get("DODOU_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("DODOU_AI_MODEL", "gpt-4o-mini").strip()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-8:])
    messages.append({"role": "user", "content": message})
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.6,
        "max_tokens": 900,
    }
    try:
        request = urllib.request.Request(
            f"{base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"].strip()
        return content or None
    except Exception:
        return None


def diagnosis_reply(message):
    """内置宠物护理知识回复，作为未配置大模型时的兜底。"""
    critical = (
        "抽搐",
        "休克",
        "昏迷",
        "呼吸困难",
        "喘不上气",
        "窒息",
        "误食",
        "中毒",
        "大出血",
        "便血",
        "拉血",
        "呕吐不止",
        "不停呕吐",
        "站不起来",
        "被撞",
        "摔伤",
    )
    if any(word in message for word in critical):
        return (
            "豆豆注意到这些可能是需要尽快就医的危急信号：抽搐、呼吸困难、误食中毒、"
            "持续呕吐、便血或外伤。豆豆建议现在立刻联系附近宠物医院，途中尽量让宠物保持安静、"
            "不要强行喂水或喂食，并把发病经过、吃过什么和最近接种情况告诉医生。"
        )

    if any(word in message for word in ("拉肚子", "腹泻", "软便", "便便稀")):
        return (
            "先别太紧张，豆豆建议先观察三件事：次数、状态和有没有血。\n"
            "1. 成年犬猫可以先停食 4-6 小时但保持饮水；幼龄宠物不要长时间禁食，尽快咨询兽医。\n"
            "2. 可以喂少量易消化的熟鸡胸肉或处方罐头，少量多次。\n"
            "3. 如果超过 24 小时没好转，或出现便血、反复呕吐、没精神，需要尽快带去医院。\n"
            "豆豆还想知道，你家毛孩子是狗狗还是猫咪，大概几岁，最近有没有换粮或吃陌生人食物？"
        )

    if any(word in message for word in ("呕吐", "吐了", "反酸", "吐白沫", "吐黄水")):
        return (
            "偶尔吐一次不用太慌张，但豆豆需要你继续观察频率和精神状态。\n"
            "可以先停食 4-6 小时，让肠胃休息；期间少量饮水。恢复后给一点好消化的食物。\n"
            "如果 24 小时内呕吐超过 3 次，或伴随没精神、拒食、腹痛、吐出血或异物，"
            "豆豆建议尽快去医院检查。"
        )

    if any(word in message for word in ("不吃", "没食欲", "不吃饭", "食欲不好", "没胃口")):
        return (
            "没精神加不吃饭通常是身体在发信号，豆豆建议先量一下体温：狗狗正常约 38-39.2℃，"
            "猫咪约 38-39.5℃。再检查有没有呕吐、拉肚子、呼吸急促或牙龈颜色发白。\n"
            "如果只是轻微没胃口且精神状态尚可，可以先温水泡软口粮试一下；"
            "如果持续超过 24 小时不吃不喝、嗜睡或发热，就要尽快就医。"
        )

    if any(word in message for word in ("咳嗽", "打喷嚏", "流鼻涕", "鼻涕", "干咳")):
        return (
            "豆豆帮你梳理一下观察重点：分泌物是清水样还是脓性、有没有发烧、"
            "精神和食欲是否正常。\n"
            "保持环境干净通风，别让宠物吹到冷风，也不要在家随意用药。\n"
            "如果咳嗽持续两天以上，或出现喘、嘴唇发紫、不吃不喝，请尽快去医院排查呼吸道感染。"
        )

    if any(word in message for word in ("抓耳朵", "耳朵臭", "甩头", "耳螨", "耳朵红")):
        return (
            "频繁抓耳朵、耳朵臭或甩头，常见原因是耳道潮湿、耳螨或外耳炎。\n"
            "豆豆建议先用宠物洗耳液轻轻清洁外耳，避免用棉签往深处掏；"
            "如果耳廓内侧红肿、有黑色碎屑或褐色分泌物，最好让医生做个耳道检查并针对性用药。\n"
            "洗澡和游泳后记得把耳朵擦干。"
        )

    if any(word in message for word in ("掉毛", "抓痒", "红疹", "皮屑", "真菌", "皮肤病", "一块块")):
        return (
            "掉毛、起红疹或皮肤发痒的原因不少，可能是寄生虫、真菌或过敏。\n"
            "豆豆建议先戴伊丽莎白圈防止抓破，检查体表和耳背有没有跳蚤或虫卵；"
            "可以温和梳理并拍照记录范围。若出现圆形脱毛、破损流液或范围扩大，"
            "建议去医院做皮肤刮片，不要自行买人用药膏涂抹。"
        )

    if any(word in message for word in ("眼睛", "流泪", "眼屎", "红眼", "眯眼")):
        return (
            "眼睛问题要认真对待，豆豆建议先观察分泌物是清水还是黄绿色、是否频繁眯眼或抓挠。\n"
            "可以用宠物专用湿巾或生理盐水从内眼角向外轻轻擦拭，不要让宠物抓眼睛。\n"
            "如果角膜看着发白、眼睑红肿或分泌物明显增多，请尽快就医，避免拖延损伤视力。"
        )

    if any(word in message for word in ("瘸", "跛行", "腿疼", "不敢走", "一瘸一拐", "骨折")):
        return (
            "出现跛行或不敢着地，先让宠物休息，别继续跑跳或爬楼梯。\n"
            "豆豆建议轻轻检查脚垫有没有异物或伤口；如果明显肿胀、按压时抗拒、"
            "关节变形或超过 24 小时未缓解，需要拍 X 光确认。"
        )

    if any(word in message for word in ("疫苗", "打疫苗", "接种", "狂犬", "猫三联", "犬四联")):
        return (
            "疫苗问题最好参考宠物档案里的接种记录。豆豆的一般建议是：\n"
            "幼犬幼猫按医生计划完成基础免疫，成年后每年定期复查抗体并补打相应疫苗；"
            "接种前后一周尽量不洗澡、不剧烈运动、不换粮，打完留在医院观察 20-30 分钟。\n"
            "如果最近准备出门寄养或洗澡，可以先和医生确认疫苗是否在有效保护期内。"
        )

    if any(word in message for word in ("驱虫", "虫子", "跳蚤", "蜱虫")):
        return (
            "预防性驱虫建议按体重和药品说明进行，体内驱虫通常每 1-3 个月一次，"
            "体外驱虫看环境和外出频率。\n"
            "发现跳蚤或蜱虫时不要直接硬拔蜱虫，可用专用工具夹住头部拔出并消毒，"
            "同时清理家里角落。若宠物很小、生病或刚到家，先让医生确认再用药。"
        )

    if any(word in message for word in ("你好", "您好", "嗨", "hello", "hi", "在吗")):
        return (
            "你好呀，豆豆在的。宠物有什么小状况，或者想查遛狗天气，"
            "都可以直接告诉豆豆：狗狗还是猫咪、什么症状、持续多久了？"
        )

    if any(word in message for word in ("谢谢", "感谢", "辛苦了")):
        return "不客气，豆豆会一直陪在毛孩子身边。照顾好它，有新的情况随时再来找豆豆。"

    return (
        "豆豆收到啦。为了给你更准确的观察建议，可以先说说：\n"
        "1. 是狗狗还是猫咪，大概几岁、多重？\n"
        "2. 主要出现什么症状，持续多久了？\n"
        "3. 吃喝、精神和大小便还正常吗？\n"
        "也可以直接输入“北京遛狗天气”之类的问题，豆豆帮你查天气。"
    )
