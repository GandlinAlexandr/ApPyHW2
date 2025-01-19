<a name="readme-top"></a>

[![MIT][license-shield]][license-url]
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
[!['Black'](https://img.shields.io/badge/code_style-black-black?style=for-the-badge)](https://github.com/psf/black)

  <h1 align="center">Фитнес-бот</h1>

  <p align="center">
    Телеграм бот в рамках домашней работы по дисциплине "Прикладное программирование на Python"
  </p>


<details>
  <summary>Содержание</summary>
  <ol>
    <li>
      <a href="#о-проекте">О проекте</a>
        <li><a href="#технологии">Технологии</a></li>
    </li>
    <li>
      <a href="#содержание-проекта">Содержание проекта</a>
    </li>
    <ul>
    <li><a href="#предоставляемые-функции">Предоставляемые функции</a></li>
    <li><a href="#команды">Команды</a></li></ul>
      <li><a href="#лицензия">Лицензия</a></li>
    <li><a href="#контакты">Контакты</a></li>
  </ol>
</details>



### О проекте

Представляет собой телеграм-бот, отслеживающий активность, потребление воды и калорий пользователем.

## Технологии

Для реализации проекта использовались следующие технологии:

* [![Python][Python.org]][Python-url]
  * [![Matplotlib][Matplotlib.org]][Matplotlib-url]
  * [![Pandas][Рandas.pydata.org]][Pandas-url]
  * [![Seaborn][Seaborn-badge]][Seaborn-url]


<p align="right">(<a href="#readme-top">Вернуться к началу</a>)</p>

## Содержание проекта

Содержит телеграм-бот, а также всё необходимое (за исключением кличей) для его развёртывания, включая Докер-файл для создания образа. Код разбит на несколько файлов:
* `API.py` - содержит код для взаимодействия с API
* `bot.py` - осноаа бота, содержащая диспетчер и функцию запуска
* `calculations.py` - код, содержащий вычисления показателей и построение графиков
* `config.py` - код, импортирующий ключи из `.env`
* `handlers.py` - основная часть бота, содержащая все хэндлеры. Сюда импортируются все остаольные файлы и функции из них
* `states.py` - небольшой файл, содержащий состояния. Необходим для конструирования форм для заполнения и для связывания некоторых функций и хэндлеров между собой

Данные пользователей хранит в памяти. Никакие базы данных пока не подключены.

<p align="right">(<a href="#readme-top">Вернуться к началу</a>)</p>


### Предоставляемые функции

Бот предоставляет пользователю возможность создать аккаунт, содержащий следующие параметры:
* Вес (кг)
* Рост (см)
* Возраст (лет)
* Активность в день (мин)
* Город
* Цель по калориям (ккал) - расчитывается автоматически или указывается пользователем
* Норма воды (л) - расчитывается автоматически
* Выпито воды (л) - логгирутся на основе отчёта пользователя
* Потреблено калорий (ккал) - логгирутся на основе отчёта пользователя
* Сожжено калорий (ккал) - логгирутся на основе отчёта пользователя

Соответсвенно, бот ведёт журнал посуточных активностей пользователя, если тот ведёт отчёт. Норму воды формирует на основе веса, активеости и температуры в городе проживвания, извлекаемой в реальном времени посредством [Weather API](https://openweathermap.org/api). 
Потребляемое и сжигаемое количество калорий расчитывается на основе указаний съеденой пищи и проведённых тренировок посредством запросов к [Nutritionix  API](https://www.nutritionix.com/). Для обработки русскоязычных запросов используется API Google Translate. Также выводит графики прогресса достиженния норм пот калориям и воде, графики по калориям и воде за последние 10 дней активности пользователя.

<p align="right">(<a href="#readme-top">Вернуться к началу</a>)</p>


### Команды

Команды, не требующие немедленного ввода параметров (представлены в меню быстрого доступа в чате):
* `/start` - Начало работы
* `/help` - Помощь
* `/set_profile` - Заполнение формы для создания профиля. При создании нового старый профиль удаляется
* `/my_propfile` - Посмотреть свой профиль
* `/check_progress` - Показывает, сколько воды и калорий потреблено, сожжено и сколько осталось до выполнения цели на текущие сутки. Выводит соотвествующие диаграммы
* `/recomend` - Выдаёт рекомендации на основе ИМТ
* `/global_progress` - Выводит график глобального прогресса за последние 10 дней активности в чате бота
* `/edit_profile` - Позволяет изменить параметры профиля, не удаляя его и сохраняя историю

Команды с параметрами:
* `/log_water` <количество воды в мл> - Добавляет количество выпитой воды в ваш профиль и рассчитывает количество воды до нормы
* `/log_food` <название продукта> - Рассчитывает количество поглощённых калорий по названию блюда и добавляет в профиль
* `/log_workout` <тип тренировки> <время (мин)> - Фиксирует сожжённые калории и учитывает расход воды на тренировке


<p align="right">(<a href="#readme-top">Вернуться к началу</a>)</p>

## Лицензия

Распространяется по лицензии MIT. Дополнительную информацию см. в файле `LICENSE`.

<p align="right">(<a href="#readme-top">Вернуться к началу</a>)</p>

## Контакты

Гандлин Александр - [Stepik](https://stepik.org/users/79694206/profile)

Ссылка на проект: [https://github.com/GandlinAlexandr/ApPyHW2](https://github.com/GandlinAlexandr/ApPyHW2)

<p align="right">(<a href="#readme-top">Вернуться к началу</a>)</p>


[license-shield]: https://img.shields.io/github/license/GandlinAlexandr/ApPyHW2.svg?style=for-the-badge
[license-url]: https://github.com/GandlinAlexandr/ApPyHW2/blob/main/LICENSE

[Python-url]: https://python.org/
[Python.org]: https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue

[Pandas-url]: https://pandas.pydata.org/
[Рandas.pydata.org]: https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white

[Matplotlib-url]: https://matplotlib.org/
[Matplotlib.org]: https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black

[Seaborn-url]: https://seaborn.pydata.org/
[Seaborn-badge]: https://img.shields.io/badge/Seaborn-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=blue
