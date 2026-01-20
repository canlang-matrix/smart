from app import create_app
from app.models import SensorData
from app.services.ai_service import get_current_weather
import os

app = create_app()

with app.app_context():
    latest = SensorData.query.order_by(SensorData.id.desc()).first()
    print('Latest SensorData:')
    if latest:
        print('  id:', latest.id)
        print('  timestamp:', latest.timestamp)
        print('  temperature:', latest.temperature)
        print('  humidity:', latest.humidity)
        print('  light:', latest.light)
    else:
        print('  (no sensor data found)')

    print('\nEnvironment vars:')
    print('  OPENWEATHER_API_KEY=', bool(os.environ.get('OPENWEATHER_API_KEY')))
    print('  OPENWEATHER_CITY=', os.environ.get('OPENWEATHER_CITY'))
    print('  OPENWEATHER_LAT=', os.environ.get('OPENWEATHER_LAT'))
    print('  OPENWEATHER_LON=', os.environ.get('OPENWEATHER_LON'))

    print('\nget_current_weather() result:')
    try:
        w = get_current_weather()
        print(w)
    except Exception as e:
        print('  error calling get_current_weather():', e)
