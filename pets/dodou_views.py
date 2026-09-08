import json

from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from . import dodou


def _read_json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _parse_coordinates(data):
    location = data.get("location") if isinstance(data, dict) else None
    if not isinstance(location, dict):
        return None, None
    try:
        lat = float(location.get("lat"))
        lon = float(location.get("lon"))
    except (TypeError, ValueError):
        return None, None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None, None
    return lat, lon


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


@ensure_csrf_cookie
@require_POST
def dodou_chat_view(request):
    data = _read_json_body(request)
    message = str(data.get("message", "")).strip()
    if not message:
        return JsonResponse(
            {"ok": False, "text": "豆豆没听清问题，再输入一次吧。"},
            status=400,
        )

    history = data.get("history") or []
    if not isinstance(history, list):
        history = []
    history = [
        item
        for item in history[-8:]
        if isinstance(item, dict)
        and item.get("role") in ("user", "assistant")
        and item.get("content")
    ]

    if dodou.is_weather_intent(message):
        lat, lon = _parse_coordinates(data)
        city = dodou.extract_city(message)
        result = dodou.weather_reply(
            city=city,
            lat=None if city else lat,
            lon=None if city else lon,
            remote_ip=_client_ip(request),
        )
        return JsonResponse(
            {
                "ok": True,
                "kind": "weather",
                "text": result["text"],
            }
        )

    text = dodou.llm_reply(message, history)
    if text is None:
        text = dodou.diagnosis_reply(message)
    return JsonResponse(
        {
            "ok": True,
            "kind": "ai",
            "text": text,
        }
    )


@require_GET
def dodou_weather_view(request):
    city = request.GET.get("city", "").strip()
    try:
        lat = float(request.GET.get("lat"))
        lon = float(request.GET.get("lon"))
    except (TypeError, ValueError):
        lat, lon = None, None
    result = dodou.weather_reply(
        city=city,
        lat=lat,
        lon=lon,
        remote_ip=_client_ip(request),
    )
    return JsonResponse(result)
