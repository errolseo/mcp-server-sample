import requests
import json
from datetime import datetime

def get_current_datetime():
    """
    현재 시스템 시간을 반환합니다.

    Returns:
        dict: {"now": "YYYY-MM-DD HH:MM:SS"} 형식의 현재 한국 시간 문자열.
    """
    now = datetime.datetime.now()
    
    return {"now": now.strftime("%Y-%m-%d %H:%M:%S")}

def get_current_location():
    """
    공용 IP 주소를 기반으로 현재 위치(위도, 경도) 정보를 반환합니다.
    (ipinfo.io API 사용)

    Returns:
        dict or None: 위치 정보 딕셔너리 ({"city": "Seoul", "country": "KR"})
                      API 요청 실패 시 None 반환.
    """
    try:
        response = requests.get("https://ipinfo.io/json")
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        data = response.json()
        
        latitude, longitude = data.get("loc").split(",")
        
        return {"latitude": latitude, "longitude": longitude}
    except requests.exceptions.RequestException as e:
        print(f"위치 정보를 가져오는 중 오류 발생: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"위치 정보 JSON 디코딩 오류: {e}")
        return None
    
def get_current_weather(latitude, longitude):
    """
    Open-Meteo API를 사용하여 지정된 위도, 경도의 현재 날씨 정보를 반환합니다.

    Args:
        latitude: 위치의 위도.
        longitude: 위치의 경도.

    Returns:
        dict or None: 날씨 정보 딕셔너리 또는 None.
    """
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": "true",
        "timezone": "Asia/Seoul"
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        data = response.json()

        if "current_weather" in data:
            current_weather = data["current_weather"]
            weather_info = {
                "temperature": current_weather.get("temperature"),
                "wind_speed": current_weather.get("windspeed"),
                "wind_direction": current_weather.get("winddirection"),
                "is_day": current_weather.get("is_day"), # 0: 밤, 1: 낮
                "time": current_weather.get("time"),
                # weather_code를 실제 날씨 설명으로 변환하는 로직이 필요할 수 있습니다.
                # Open-Meteo 문서에서 WMO Weather interpretation codes 참조
                "weather_code": current_weather.get("weathercode")
            }
            return weather_info
        else:
            print("Open-Meteo에서 현재 날씨 정보를 찾을 수 없습니다.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Open-Meteo 날씨 정보를 가져오는 중 오류 발생: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Open-Meteo 날씨 정보 JSON 디코딩 오류: {e}")
        return None