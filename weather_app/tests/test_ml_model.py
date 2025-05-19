import unittest
from unittest.mock import patch, Mock
import datetime
import numpy as np
import os
import sys
import tempfile
import joblib

# Путь к модулям, которые мы тестируем
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app')))

# Импорт модулей для тестирования
import ml_model
from backend.app.models import WeatherData, WeatherForecast

class TestMLModel(unittest.TestCase):
    
    def setUp(self):
        """Настройка для каждого теста"""
        self.test_city = "Москва"
        self.today = datetime.date.today()
        
        # Создаем временные пути для моделей и других файлов
        self.temp_dir = tempfile.TemporaryDirectory()
        # Заменяем константы в модуле на временные пути
        self.original_model_path = ml_model.MODEL_PATH
        self.original_scaler_path = ml_model.SCALER_PATH
        self.original_encoder_path = ml_model.ENCODER_PATH
        
        ml_model.MODEL_PATH = os.path.join(self.temp_dir.name, "weather_model.joblib")
        ml_model.SCALER_PATH = os.path.join(self.temp_dir.name, "weather_scaler.joblib")
        ml_model.ENCODER_PATH = os.path.join(self.temp_dir.name, "weather_encoder.joblib")
        
        # Создаем тестовые данные
        self.test_data = []
        for i in range(30):
            date = self.today - datetime.timedelta(days=i)
            self.test_data.append(WeatherData(
                city=self.test_city,
                date=date,
                temperature=20.0 - 0.1 * i,
                humidity=60.0 + 0.2 * i,
                pressure=1013.0 - 0.3 * i,
                wind_speed=5.0 + 0.1 * i,
                precipitation=0.5 + 0.05 * i,
                weather_condition="Ясно" if i % 3 == 0 else "Облачно" if i % 3 == 1 else "Дождь"
            ))
    
    def tearDown(self):
        """Очистка после каждого теста"""
        self.temp_dir.cleanup()
        # Восстанавливаем оригинальные пути
        ml_model.MODEL_PATH = self.original_model_path
        ml_model.SCALER_PATH = self.original_scaler_path
        ml_model.ENCODER_PATH = self.original_encoder_path
    
    def test_prepare_data(self):
        """Тест функции подготовки данных"""
        X, conditions, dates = ml_model.prepare_data(self.test_data)
        
        # Проверяем размерности
        self.assertEqual(X.shape[0], len(self.test_data))
        self.assertEqual(X.shape[1], 8)  # 8 признаков
        self.assertEqual(len(conditions), len(self.test_data))
        self.assertEqual(len(dates), len(self.test_data))
        
        # Проверяем типы данных
        self.assertIsInstance(X, np.ndarray)
        self.assertIsInstance(conditions, list)
        self.assertIsInstance(dates, list)
        
        # Проверяем содержимое
        self.assertEqual(conditions[0], self.test_data[0].weather_condition)
        self.assertEqual(dates[0], self.test_data[0].date)
    
    def test_train_model_insufficient_data(self):
        """Тест обучения модели с недостаточным количеством данных"""
        with self.assertRaises(ValueError):
            ml_model.train_model(self.test_data[:3])  # Пытаемся обучить на 3 записях
    
    def test_train_model(self):
        """Тест обучения модели"""
        metrics = ml_model.train_model(self.test_data)
        
        # Проверяем, что метрики возвращаются
        self.assertIn('temp_rmse', metrics)
        self.assertIn('temp_mae', metrics)
        self.assertIn('temp_r2', metrics)
        self.assertIn('humidity_rmse', metrics)
        self.assertIn('humidity_mae', metrics)
        self.assertIn('humidity_r2', metrics)
        self.assertIn('precip_rmse', metrics)
        self.assertIn('precip_mae', metrics)
        self.assertIn('precip_r2', metrics)
        
        # Проверяем, что файлы модели созданы
        self.assertTrue(os.path.exists(ml_model.MODEL_PATH))
        self.assertTrue(os.path.exists(ml_model.SCALER_PATH))
        self.assertTrue(os.path.exists(ml_model.ENCODER_PATH))
    
    @patch('joblib.load')
    @patch('joblib.dump')
    def test_make_forecast_no_model(self, mock_dump, mock_load):
        """Тест создания прогноза когда модели ещё нет"""
        # Настраиваем моки
        mock_model_temp = Mock()
        mock_model_temp.predict.return_value = np.array([15.0])
        
        mock_model_humidity = Mock()
        mock_model_humidity.predict.return_value = np.array([70.0])
        
        mock_model_precip = Mock()
        mock_model_precip.predict.return_value = np.array([0.5])
        
        mock_scaler = Mock()
        mock_scaler.transform.return_value = np.array([[1, 2, 3, 4, 5, 6, 7, 8]])
        
        mock_encoder = Mock()
        
        # Настраиваем возвращаемые значения для joblib.load
        mock_load.side_effect = [
            {
                'temperature': mock_model_temp,
                'humidity': mock_model_humidity,
                'precipitation': mock_model_precip,
                'conditions_encoder': mock_encoder
            },
            mock_scaler,
            mock_encoder
        ]
        
        # Настраиваем существование файлов
        with patch('os.path.exists', return_value=False):
            with patch('ml_model.train_model') as mock_train:
                mock_train.return_value = {}
                
                # Вызываем функцию
                forecasts = ml_model.make_forecast(self.test_data, days=3)
                
                # Проверяем, что модель была обучена
                mock_train.assert_called_once_with(self.test_data)
        
        # Проверяем результат прогноза
        self.assertEqual(len(forecasts), 3)
        self.assertIsInstance(forecasts[0], WeatherForecast)
        self.assertEqual(forecasts[0].city, self.test_city)
        self.assertEqual(forecasts[0].date, self.today + datetime.timedelta(days=1))
    
    def test_make_forecast_integration(self):
        """Интеграционный тест создания прогноза"""
        # Сначала обучаем модель
        ml_model.train_model(self.test_data)
        
        # Затем делаем прогноз
        forecasts = ml_model.make_forecast(self.test_data, days=5)
        
        # Проверяем результат
        self.assertEqual(len(forecasts), 5)
        self.assertIsInstance(forecasts[0], WeatherForecast)
        
        # Проверяем даты прогноза
        last_date = max(item.date for item in self.test_data)
        for i, forecast in enumerate(forecasts):
            self.assertEqual(forecast.date, last_date + datetime.timedelta(days=i+1))
            
        # Проверяем, что все необходимые поля заполнены
        for forecast in forecasts:
            self.assertEqual(forecast.city, self.test_city)
            self.assertIsInstance(forecast.temperature, float)
            self.assertIsInstance(forecast.humidity, float)
            self.assertIsInstance(forecast.precipitation, float)
            self.assertIsInstance(forecast.weather_condition, str)
            
    def test_make_forecast_conditions(self):
        """Тест определения условий погоды на основе прогнозируемых значений"""
        # Создаем набор тестовых записей с разными условиями
        conditions_test = [
            {'temp': 20.0, 'humidity': 50.0, 'precip': 0.0, 'expected': "Ясно"},
            {'temp': 18.0, 'humidity': 70.0, 'precip': 0.0, 'expected': "Облачно"},
            {'temp': 15.0, 'humidity': 85.0, 'precip': 0.0, 'expected': "Туман"},
            {'temp': 10.0, 'humidity': 60.0, 'precip': 2.0, 'expected': "Пасмурно"},
            {'temp': 10.0, 'humidity': 60.0, 'precip': 8.0, 'expected': "Дождь"},
            {'temp': 25.0, 'humidity': 80.0, 'precip': 10.0, 'expected': "Гроза"}
        ]
        
        # Создаем мок-функции
        with patch('joblib.load') as mock_load, \
             patch('os.path.exists', return_value=True):
            
            for test_case in conditions_test:
                mock_model_temp = Mock()
                mock_model_temp.predict.return_value = np.array([test_case['temp']])
                
                mock_model_humidity = Mock()
                mock_model_humidity.predict.return_value = np.array([test_case['humidity']])
                
                mock_model_precip = Mock()
                mock_model_precip.predict.return_value = np.array([test_case['precip']])
                
                mock_scaler = Mock()
                mock_scaler.transform.return_value = np.array([[1, 2, 3, 4, 5, 6, 7, 8]])
                
                mock_encoder = Mock()
                
                # Настраиваем возвращаемые значения для joblib.load
                mock_load.side_effect = [
                    {
                        'temperature': mock_model_temp,
                        'humidity': mock_model_humidity,
                        'precipitation': mock_model_precip,
                        'conditions_encoder': mock_encoder
                    },
                    mock_scaler,
                    mock_encoder
                ]
                
                # Вызываем функцию
                forecasts = ml_model.make_forecast(self.test_data, days=1)
                
                # Проверяем результат
                self.assertEqual(forecasts[0].weather_condition, test_case['expected'])
                mock_load.reset_mock()

if __name__ == '__main__':
    unittest.main()