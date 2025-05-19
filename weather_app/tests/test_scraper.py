import unittest
from unittest.mock import patch, Mock
import datetime
import sys
import os

# Путь к модулям, которые мы тестируем
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app')))

# Импорт модулей для тестирования
import scraper
from backend.app.models import WeatherData, WeatherForecast

class TestWeatherScraper(unittest.TestCase):
    
    def setUp(self):
        """Настройка для каждого теста"""
        self.test_city = "Москва"
        self.today = datetime.date.today()
        self.yesterday = self.today - datetime.timedelta(days=1)
        
    def test_get_weather_condition(self):
        """Тест функции получения текстового описания погоды по коду"""
        # Проверяем различные коды погоды
        self.assertEqual(scraper.get_weather_condition(800), "Ясно")
        self.assertEqual(scraper.get_weather_condition(801), "Облачно")
        self.assertEqual(scraper.get_weather_condition(701), "Туман")
        self.assertEqual(scraper.get_weather_condition(601), "Снег")
        self.assertEqual(scraper.get_weather_condition(501), "Дождь")
        self.assertEqual(scraper.get_weather_condition(301), "Дождь")
        self.assertEqual(scraper.get_weather_condition(201), "Гроза")
        self.assertEqual(scraper.get_weather_condition(100), "Неизвестно")
    
    def test_generate_weather_data(self):
        """Тест функции генерации случайных данных о погоде"""
        # Проверяем генерацию для разных городов и разных сезонов
        winter_date = datetime.date(2023, 1, 15)
        summer_date = datetime.date(2023, 7, 15)
        
        # Тестируем для зимы
        winter_data = scraper.generate_weather_data(self.test_city, winter_date)
        self.assertIsInstance(winter_data, dict)
        self.assertIn("temperature", winter_data)
        self.assertIn("humidity", winter_data)
        self.assertIn("pressure", winter_data)
        self.assertIn("wind_speed", winter_data)
        self.assertIn("precipitation", winter_data)
        self.assertIn("weather_condition", winter_data)
        
        # Тестируем для лета
        summer_data = scraper.generate_weather_data(self.test_city, summer_date)
        self.assertIsInstance(summer_data, dict)
        
        # Проверяем, что летняя температура выше зимней в среднем
        # Запускаем несколько раз для снижения вероятности случайной ошибки
        winter_temps = []
        summer_temps = []
        for _ in range(10):
            winter_temps.append(scraper.generate_weather_data(self.test_city, winter_date)["temperature"])
            summer_temps.append(scraper.generate_weather_data(self.test_city, summer_date)["temperature"])
        
        self.assertGreater(sum(summer_temps)/len(summer_temps), sum(winter_temps)/len(winter_temps))
    
    @patch('scraper.requests.get')
    def test_get_weather_from_api_success(self, mock_get):
        """Тест успешного получения данных о погоде через API"""
        # Мокаем ответ от API для геокоординат
        mock_geo_response = Mock()
        mock_geo_response.raise_for_status = Mock()
        mock_geo_response.json.return_value = [{"lat": 55.7558, "lon": 37.6173}]
        
        # Мокаем ответ от API для погоды
        mock_weather_response = Mock()
        mock_weather_response.raise_for_status = Mock()
        mock_weather_response.json.return_value = {
            "main": {
                "temp": 10.5,
                "humidity": 70,
                "pressure": 1015
            },
            "wind": {
                "speed": 5.2
            },
            "weather": [
                {"id": 800}
            ]
        }
        
        # Настраиваем мок для разных вызовов requests.get
        mock_get.side_effect = [mock_geo_response, mock_weather_response]
        
        # Вызываем функцию
        result = scraper.get_weather_from_api(self.test_city, self.today)
        
        # Проверяем результат
        self.assertIsNotNone(result)
        self.assertEqual(result["temperature"], 10.5)
        self.assertEqual(result["humidity"], 70)
        self.assertEqual(result["pressure"], 1015)
        self.assertEqual(result["wind_speed"], 5.2)
        self.assertEqual(result["precipitation"], 0)
        self.assertEqual(result["weather_condition"], "Ясно")
    
    @patch('scraper.requests.get')
    def test_get_weather_from_api_city_not_found(self, mock_get):
        """Тест получения данных о погоде для несуществующего города"""
        # Мокаем ответ от API для геокоординат - пустой список
        mock_geo_response = Mock()
        mock_geo_response.raise_for_status = Mock()
        mock_geo_response.json.return_value = []
        
        mock_get.return_value = mock_geo_response
        
        # Вызываем функцию
        result = scraper.get_weather_from_api("НесуществующийГород", self.today)
        
        # Проверяем, что результат None для несуществующего города
        self.assertIsNone(result)
    
    @patch('scraper.requests.get')
    def test_get_weather_from_api_with_rain(self, mock_get):
        """Тест получения данных о погоде с дождем"""
        # Мокаем ответ от API для геокоординат
        mock_geo_response = Mock()
        mock_geo_response.raise_for_status = Mock()
        mock_geo_response.json.return_value = [{"lat": 55.7558, "lon": 37.6173}]
        
        # Мокаем ответ от API для погоды с дождем
        mock_weather_response = Mock()
        mock_weather_response.raise_for_status = Mock()
        mock_weather_response.json.return_value = {
            "main": {
                "temp": 8.5,
                "humidity": 85,
                "pressure": 1010
            },
            "wind": {
                "speed": 7.5
            },
            "weather": [
                {"id": 501}
            ],
            "rain": {
                "1h": 3.5
            }
        }
        
        # Настраиваем мок для разных вызовов requests.get
        mock_get.side_effect = [mock_geo_response, mock_weather_response]
        
        # Вызываем функцию
        result = scraper.get_weather_from_api(self.test_city, self.today)
        
        # Проверяем результат
        self.assertIsNotNone(result)
        self.assertEqual(result["precipitation"], 3.5)
        self.assertEqual(result["weather_condition"], "Дождь")
    
    @patch('scraper.get_weather_from_api')
    def test_scrape_weather_data(self, mock_get_weather):
        """Тест функции сбора данных о погоде за период"""
        # Мокаем функцию get_weather_from_api
        mock_get_weather.side_effect = lambda city, date: scraper.generate_weather_data(city, date)
        
        # Задаем параметры для тестирования
        start_date = self.today - datetime.timedelta(days=5)
        end_date = self.today
        
        # Вызываем функцию
        result = scraper.scrape_weather_data(self.test_city, start_date, end_date)
        
        # Проверяем результат
        self.assertEqual(len(result), 6)  # 6 дней включая сегодня
        self.assertIsInstance(result[0], WeatherData)
        self.assertEqual(result[0].city, self.test_city)
        self.assertEqual(result[0].date, start_date)
        self.assertEqual(result[-1].date, end_date)
        
    def test_scrape_weather_data_invalid_dates(self):
        """Тест с некорректными датами"""
        start_date = self.today + datetime.timedelta(days=5)  # Будущая дата
        end_date = self.today
        
        # Проверяем, что вызывается исключение
        with self.assertRaises(ValueError):
            scraper.scrape_weather_data(self.test_city, start_date, end_date)
    
    def test_scrape_weather_data_default_dates(self):
        """Тест с датами по умолчанию"""
        result = scraper.scrape_weather_data(self.test_city)
        
        # По умолчанию должно быть 10 дней до текущей даты
        self.assertEqual(len(result), 10)
        self.assertEqual(result[-1].date, self.today)
        self.assertEqual(result[0].date, self.today - datetime.timedelta(days=9))

if __name__ == '__main__':
    unittest.main()