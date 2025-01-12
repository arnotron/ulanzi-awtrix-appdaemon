import json
from ulanzi import UlanziApp

ICON_MAP = {
    'rainy': '72',
    'clear-night': '2285',
    # 'cloudy': '2283',
    'cloudy': '53384',
    'fog': '12196',
    'hail': '2441',
    'lightning': '10341',
    'lightning-rainy': '49299',
    'partlycloudy': 'partly_cloudy',
    'pouring': '72',
    'snowy': '2289',
    'snowy-rainy': '49301',
    'sunny': '11201',
    'windy': '55032',
    'windy-variant': '55032',
    'exceptional': '45123',
}


class UlanziWeather(UlanziApp):

    def initialize(self):
        super().initialize()
        try:
            self.weather_entity = self.args['weather_entity']
            self.current_temp_sensor = self.args.get('current_temp_sensor')
        except KeyError as err:
            self.error("Failed getting configuration {}".format(err.args[0]))
            return
        
        self.run_every(self.update_app, 'now', 60)
        if self.current_temp_sensor:
            self.listen_state(self.update_app_custom, self.current_temp_sensor)

    def update_app_custom(self, *args, **kwargs):
        if not self.enabled:
            return

        # Get current state and temperature
        current = self.get_state(self.weather_entity, attribute='all')
        current_icon = ICON_MAP.get(current['state'], ICON_MAP['exceptional'])
        if self.current_temp_sensor and (t := self.get_state(self.current_temp_sensor)) != 'unknown':
            current_temp = round(float(t), 1)
        else:
            current_temp = round(float(current['attributes']['temperature']), 1)

        # for debug purposes dump current data:
        # self.log(f"Current: {current}")

        # Get forecast for tomorrow
        # data = {'type': 'daily'}
        # target = {'entity_id': self.weather_entity}
        # forecast = self.call_service('weather/get_forecast', target=target, data=data, return_result=True)
        # unclear why above is commented out, and why make difference be
        if self.now_is_between('00:00:00', '18:00:00'):
            forecast = current['attributes']['forecast'][6]
        else:
            forecast = current['attributes']['forecast'][7]
        # temp_tomorrow_low = forecast['templow']
        # temp_tomorrow_hight = forecast['temperature']
        # temp_tomorrow = f"{int(round(temp_tomorrow_low))} - {int(round(temp_tomorrow_hight))}"
        # if temp_tomorrow_hight < 0:
        #     temp_tomorrow = f"{int(round(temp_tomorrow_low))} | {int(round(temp_tomorrow_hight))}"
        # if len(temp_tomorrow) > 7:
        #     temp_tomorrow = temp_tomorrow.replace(' ', '')

        # for debug purposes dump forecast data:
        # self.log(f"Forecast: {forecast}")
        temp_tomorrow = forecast['temperature']
        icon_tomorrow = ICON_MAP.get(forecast['condition'], ICON_MAP['exceptional'])
        preci_tomorrow = forecast['precipitation_probability']

        payload = [
            {
                'icon': current_icon,
                'text': f"{current_temp}°",
            },
            {
                'icon': icon_tomorrow,
                'text': f"{temp_tomorrow}°",
                'progress': int(preci_tomorrow),
                'progressC': '#2562c4',
                'progressBC': '#373a40',
            },
        ]
        self.call_service('mqtt/publish', topic=self.mqtt_app_topic, payload=json.dumps(payload))

        # for debug purposes dump payload data:
        self.log(f"Updated display: {payload}")

    def update_app(self, *args, **kwargs):
        self.update_app_custom()

    def get_app_text(self):
        raise NotImplementedError
