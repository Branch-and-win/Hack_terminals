
# Реализованная функциональность
<ul>
    <li> Прогнозирование прироста денег в терминалах на каждый день горизонта планирования</li>
    <li> Выбор оптимальных маршрутов для броневиков на каждый день горизонта планирования </li>
    <li> Оптимизационная модель для оценки минимального количества броневиков</li>
    <li> Гибкая настройка параметров расчета </li>
</ul> 

# Прогнозная модель

В ipython-notebook файле ``Income_prognosis.ipynb`` описан процесс получения прогнозов.

Для предсказания пополнений мы используем модель [**N-BEATS**](https://unit8co.github.io/darts/generated_api/darts.models.forecasting.nbeats.html?highlight=nbeats#darts.models.forecasting.nbeats.NBEATSModel) из библиотеки [**Darts**](https://unit8co.github.io/darts/) свою для каждого терминала:
1. При предсказании мы используем значения пополнений 14-ти предыдущих дней
2. Кроме пополнений самого терминала мы используем в качестве фичи усредненные значения 5-ти ближайших терминалов (не заглядывая в будущее) - это улучшает MAE на 10-15%
3. Мы обучаем модель на первых 70% значений всего ряда
4. Обучение занимает достаточно много времени(около 3ех часов) - поэтому мы сложили модели в файл term_models.pickle - далее в коде есть код загрузки предобученных моделей. term_models - это словарь вида id терминала: модель
5. Для каждого терминала строится отдельная модель

Для дат 1-14 сентября нашей модели недостаточно данных(она использует 14 предыдущих дней для предсказания следующих значений) - поэтому здесь мы используем более простую модель: предсказание на каждый день в будущем - это среднее по всем известным предыдущим пополнениям для конкретного терминала. Отдельный кейс 1 сентября - на этот момент мы ничего не знаем про пополнение, поэтому чтобы получить хоть какой-то адекватный прогноз - просто берем среднее за весь указанный период по терминалу(1 сентября - 30 ноября). Таким образом, мы используем неизвестные на данный моменты данные, но в реальности у нас есть какая-то известная история на этот момент и скорее всего выборочное среднее будет не сильно отличаться от того значения, что мы используем

Прогнозы для исторических данных записываются в директорию ``/predictions``

1. В файле ``term_models.pickle`` хранится словарь обученных моделей для каждого терминала. Перед применением модели для ряда также обязательно использовать Scaler - как это показано в ноутбук-фалйе
2. В файле ``prognosis_full_new.pickle`` хранятся все предсказания для исторических данных (для каждого дня с 31 августа по 30 ноября на 15 дней вперед)

Ссылка на статью, на которой основана имплементация модели: https://openreview.net/forum?id=r1ecqn4YwB

Ссылка на документацию библиотеки Darts - для обучения и предсказаний используется версия 0.24.0: https://unit8co.github.io/darts/

# Оптимизационная модель

В файле ``create_data.py`` реализованы 2 функции:  

1. ``create_data`` читает входные данные на первый день горизонта планирования  
2. ``update_data`` обновляет данные на каждый день горизонта планирования с учетом решения предыдущего дня
  
Кроме того, для каждого терминала в этих функциях вычисляется параметр *DaysLeft*, который показывает, через сколько дней посещение терминала станет обязательным (истечет период непосещения 14 дней или прогнозируется объем наличных в терминале, превышающий 1000000 рублей). 

В файле ``routes_generation.py`` реализован алгоритм генерации фиксированного количества потенциальных маршрутов на текущий день расчета:

1. Первая точка маршрута выбирается случайным образом, но вероятность выпадения терминала увеличивается при меньшем параметре *DaysLeft*.
2. Последующие точки выбираются также случайным образом, но на вероятность выпадения терминала влияет параметр *DaysLeft* и *EdgeTime* (время проезда между предыдущей точкой маршрута и потенциальным кандидатом). Чем ниже показатели *DaysLeft* и *EdgeTime*, тем выше вероятность выпадения терминала.
3. При генерации последующих потенциальных точек маршрута исключаются все предыдущие терминалы, а также терминалы, до которых невозможно доехать до конца рабочей смены.
4. Маршрут генерируется до тех пор, пока множество потенциальных следующих точек не окажется пустым.

В файле ``model.py`` с помощью библиотеки **Pyomo** описана модель линейного целочисленного программирования:

**Переменные**

*route_use[r]* - бинарные переменные, показывающие, выбрали ли мы сгенерированный маршрут r в текущий день. 
   
**Ограничения**

1. Обязательно объехать терминалы с *DaysLeft* = 0
2. Не посещать терминал более 1 раза за день
3. Количество выбранных *route_use* должно не превышать заданное количество броневиков
   
**Целевая функция**

Суммарное количество баллов за посещение терминалов с *DaysLeft* > 0. Чем меньше *DaysLeft* терминала, тем больше баллов в целевую функцию пойдет за его посещение. Такой выбор целевой функции позволяет нам заблаговременно посещать некоторые терминалы, что позволит избежать неразрешимости задачи по объезду терминалов с *DaysLeft* = 0 в последующие дни.

Файл ``output.py`` собирает результаты работы оптимизационной модели текущего дня в нужном формате.

Файл ``main.py`` запускает цикл по всему горизонту планирования, в котором:

1. Обновляются данные с учетом предыдущего дня
2. Генерируются потенциальные маршруты
3. Решается оптимизационная задача по выбору маршрутов с помощью open-source солвера HIGHS
4. Резльутат добавляется в выходной отчет

Также в этом файле определяются гиперпараметры расчета:

1. params['balance_percent'] - величина % в годовых, которую банк платит за неинкассированную сумму денег в терминале
2. params['maintenance_percent'] - величина % от суммы инкассации за обслуживание терминала
3. params['car_cost'] - стоимость одного броневика за день
4. params['max_cash'] - максимально допустимая сумма денег в терминале
5. params['max_days'] - максимально допустимое время, в течение которого терминал можно не обслуживать
6. params['maintenance_minutes'] - время на обсулживание одного терминала
7. params['start_hour'] - время началы смены
8. params['end_hour'] - время конца смены
9. params['start_date'] - первая дата горизонта планирования
10. params['end_date'] - последняя дата горизонта планирования
11. params['num_cars'] - размер парка броневиков. Данный параметр передается как ограничение на каждый запуск оптимизации. Если в один из дней горизонта планирования статус оптимизации окажется "нет решения", значит выбранного размера парка не хватает. На предоставленных данных был подобран минимальный параметр params['num_cars'] = 8, при котором удавалось построить допустимое расписание на 3 месяца.
 
### Запуск решения
1. Запустить код ``create_opt_data.py`` - подготовка данных
2. Запустить код ``create_dat_file.py`` - передача данных в оптмизацию
3. Запустить основной код ``main_call.py`` - запуск оптимизационной задачи
