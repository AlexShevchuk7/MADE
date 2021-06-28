import pickle
import json
from flask import Flask, request, render_template

app = Flask(__name__)

def hot_encode(values):
    encoded_values = {col: 0 for col in values.keys()}
    for column in values.keys():
        with open(column + '.json') as json_file:
            encoder = json.load(json_file)
            encoded_values[column] = encoder[values[column]]
    return encoded_values

def process_values(brand_code, color_code):
    colors = {'0': "Черный", '1': "Голубой", '2': "Коричневый", '3': "Зеленый", '4': "Серый", '5': "Оранжевый",
              '7': "Красный", '8': "Серебристый", '9': "Фиолетовый", '10': "Белый", '11': "Желтый", '6': "Другой"}
    with open('manufacturer_name.json') as json_file:
        brands = json.load(json_file)

    brand = [key for key, value in brands.items() if int(value) == int(brand_code)][0]

    return brand, colors[str(color_code)]

def extract_columns(immutable_dict):
    ordered_columns = ['manufacturer_name', 'model_name', 'transmission', 'color', 'odometer',
                       'year_produced', 'engine_fuel', 'engine_type', 'engine_capacity', 'body_type',
                       'warranty', 'state', 'drivetrain', 'exchangable']
    mutable_dict = {key: value for key, value in immutable_dict.items()}
    #print(mutable_dict)

    ordered_dict = {key: mutable_dict[key] for key in ordered_columns}

    return ordered_dict

def render_form(mutable_dict):
    empty_fields = []

    for key in mutable_dict.keys():
        if mutable_dict[key] == '':
            empty_fields.append(f'Вы не указали {key}')

    try:
        odometer = float(mutable_dict['Пробег'])
    except ValueError:
        odometer = 'Пожалуйста, введите пробег в формате число.число'
        empty_fields.append(odometer)

    try:
        engine_capacity = float(mutable_dict['Объем двигателя'])
    except ValueError:
        engine_capacity = 'Пожалуйста, введите объем двигателя в формате число.число'
        empty_fields.append(engine_capacity)

    try:
        year_produced = int(mutable_dict['Год выпуска'])
    except ValueError:
        year_produced = 'Пожалуйста, введите год выпуска в формате целого числа'
        empty_fields.append(year_produced)

    return empty_fields


def get_prediction(vector):
    with open('model.pickle', 'rb') as fin:
        rfr = pickle.load(fin)
    predicted = rfr.predict([vector])

    return predicted

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/info')
def info():
    return render_template('info.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/result', methods=['POST'])
def result():
    data = request.form
    mutable_data = extract_columns(data)

    mapping = {'manufacturer_name': 'Марка',
               'model_name': 'Модель',
               'engine_type': 'Тип двигателя',
               'engine_fuel': 'Тип топлива',
               'engine_capacity': 'Объем двигателя',
               'transmission': 'Коробка передач',
               'drivetrain': 'Привод',
               'body_type': 'Тип кузова',
               'color': 'Цвет',
               'state': 'Состояние',
               'warranty': 'На гарантии',
               'exchangable': 'Возможен обмен',
               'odometer': 'Пробег',
               'year_produced': 'Год выпуска',}

    report = {mapping[k]: v for k, v in mutable_data.items()}
    brand_name, text_color = process_values(mutable_data['manufacturer_name'], mutable_data['color'])
    report['Марка'] = brand_name
    report['Цвет'] = text_color

    errors = render_form(report)

    if errors:
        #print(errors)
        report = {key: '' for key in errors}
        recommendation = 'Форма заполнена с ошибками'
    else:
        encodable_columns = ['model_name', 'engine_type', 'engine_fuel',
                             'transmission', 'body_type', 'drivetrain']
        encodable_dict = {k: v for k, v in mutable_data.items() if k in encodable_columns}
        encoded_dict = hot_encode(encodable_dict)

        for col in encodable_columns:
            mutable_data[col] = encoded_dict[col]

        for col in ['warranty', 'exchangable']:
            if mutable_data[col] == 'Да':
                mutable_data[col] = 1
            else:
                mutable_data[col] = 0

        if mutable_data['state'] == 'Аварийная':
            mutable_data['state'] = 0
        elif mutable_data['state'] == 'Новая':
            mutable_data['state'] = 1
        else:
            mutable_data['state'] = 2

        vector = [float(mutable_data[col]) for col in mutable_data.keys()]

        recommendation = ' '.join(['USD', str(int(get_prediction(vector)[0]))])

    return render_template('result.html', data=report, recommendation=recommendation)

if __name__ == '__main__':
    app.run(debug=True)