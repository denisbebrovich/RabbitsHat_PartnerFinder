import requests
import json
import time

def test_api_structure():
    """Тестируем структуру данных API HH.ru"""
    
    # 1. Тестируем краткий список вакансий
    print("=== ТЕСТ КРАТКОГО СПИСКА ВАКАНСИЙ ===")
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": "Python разработчик", 
        "area": 3,  # Екатеринбург
        "per_page": 3
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        for i, vacancy in enumerate(data['items']):
            print(f"\n--- Вакансия {i+1} ---")
            print(f"ID: {vacancy.get('id')}")
            print(f"Название: {vacancy.get('name')}")
            print(f"Компания: {vacancy['employer'].get('name')}")
            print(f"key_skills в кратком формате: {vacancy.get('key_skills')}")
            print(f"Есть ли key_skills: {'key_skills' in vacancy}")
            
            # 2. Тестируем полную информацию о вакансии
            print("\n=== ТЕСТ ПОЛНОЙ ИНФОРМАЦИИ О ВАКАНСИИ ===")
            vacancy_id = vacancy['id']
            detail_url = f"https://api.hh.ru/vacancies/{vacancy_id}"
            detail_response = requests.get(detail_url)
            
            if detail_response.status_code == 200:
                detail_data = detail_response.json()
                print(f"key_skills в полном формате: {detail_data.get('key_skills')}")
                
                if detail_data.get('key_skills'):
                    skills_list = [skill['name'] for skill in detail_data['key_skills']]
                    print(f"Извлеченные навыки: {skills_list}")
                else:
                    print("Нет навыков в полной информации")
            else:
                print(f"Ошибка запроса деталей: {detail_response.status_code}")
            
            print("-" * 50)
            time.sleep(0.5)  # Пауза между запросами
            
    else:
        print(f"Ошибка API: {response.status_code}")

def test_employer_api():
    """Тестируем API работодателей"""
    print("\n=== ТЕСТ API РАБОТОДАТЕЛЕЙ ===")
    
    # Берем ID компании из предыдущего теста
    employer_id = "664709"  # К Телеком,ООО
    url = f"https://api.hh.ru/employers/{employer_id}"
    
    response = requests.get(url)
    if response.status_code == 200:
        employer_data = response.json()
        print(f"Компания: {employer_data.get('name')}")
        print(f"Отрасли: {employer_data.get('industries')}")
        print(f"Регион: {employer_data.get('area', {}).get('name')}")
        print(f"Описание: {employer_data.get('description', '')[:100]}...")
    else:
        print(f"Ошибка API employers: {response.status_code}")

if __name__ == "__main__":
    test_api_structure()
    test_employer_api()