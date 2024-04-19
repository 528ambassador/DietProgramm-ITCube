import csv
import sqlite3
import sys
from datetime import datetime

from ui import Ui_Form
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem

# Для экранов с высоким разрешением (из учебника):
if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)


# ------------------------------------------------------------------------------------------------------------------- #

"""
    ПРОГРАММА "Диетический ежедневник"
    Что делает:
        Программа направлена на запись всей съеденной еды за день, показ статистики и показ советов для решения 
        возможных проблем. Кажадя запись создаёт данные, которые сохраняются для использования программы.
        Проект направлен на решение проблем в сегодняшнем обществе, как: неправильное питание,
        недостаток / черезмнрность питания, недостаток разнообразия и т.д.

    Что использует:
        Планы окон, сделанные в QT Designer; ДБ, созданная в SQLiteStudio; txt и csv файлы для сохранения данных,
        окно BASE со всем кодом для работы программы

    Как работает:
        У программы есть всего 6 основных окон, 5 которых можно открыть из главного меню. Их состав: Окно заполнения;
        статистика; советы; список полезной еды; список еды, распозноваемой программой. Каждый выполняет свою
        заданную роль. Окно заполнения - основное окно программы, оно генерирует все данные для программы, как: дата
        последнего заполнения, статистику по всем аспектам питания, советы по этой статистике. Окно статистика 
        использует подневную статистику и рисует графики. Окно советы печатает содержимое файла с советами.
        Список еды, распозноваемой программой берет ДБ всех блю и выводит первые два столбца. Это ДБ используется для
        создания статистики. Окно со списком полезной еды является сплошным тестом без логики.
        
    Проблемы:
        Прогрмма использует условные значения качества блюд и вывода результатов, поэтому вероятна погрешность в самом
        выводе. Окно со списком блюд основного окна привязана к самому основному окну, а не у главному. Из-за этого 
        это окно не является окном, которое можно вызвать из главного меню, из-за чего это окно не закрывается при
        закрытии главного меню и возможно наличие сразу двух таких окон сразу. ДБ хоть и имеет много блюд, всё равно
        ограничена и не сможет понять многие необычные блюда.
"""

# ------------------------------------------------------------------------------------------------------------------- #


class START(QMainWindow):
    # Внесение данных из qt designer
    def __init__(self):
        super().__init__()
        uic.loadUi('MainMenu.ui', self)

        '''
            Все переменные в главном меню:
            line_2 по line_6 - декоративные линии
            mainL - заголовок
            secondL - подзаголовок
            timeL и timeL1 - надписи для переменных времён
            timeLastCHANGE - надпись для вывода когда был произведено последнее изменение в программе
            timeNowCHANGE - надпись, показывающая сегодняшнюю дату
            toFoodL, toGuideL, toMainL, toStatL, toListL - надписи над своими кнопками
            toFoodBTN, toGuideBTN, toStatBTN, toListBTN - кнопки, открывающие свои нужные окна
            toMainBTN - кнопка, открывающая окно ввода данных, также имеет надпись какие данные ещё не заполненны
        '''

        # Список вызываемых окон для удобства и для корректности закрытия при закрытии основного окна
        self.blank1 = MAIN()
        self.blank2 = STAT()
        self.blank3 = FOOD()
        self.blank4 = GUIDE()
        self.blank5 = LIST()
        self.blank6 = ERROR()

        # Вывод ошибки при повторном открытии основного окна
        self.errorcheck = False

        # Соединение всех кнопок к открытиям окон
        self.toMainBTN.clicked.connect(self.toMAIN)
        self.toStatBTN.clicked.connect(self.toSTAT)
        self.toFoodBTN.clicked.connect(self.toFOOD)
        self.toGuideBTN.clicked.connect(self.toGUIDE)
        self.toListBTN.clicked.connect(self.toLIST)

        # Меняем сегодняшнюю дату (timeNowCHANGE) в основном меню
        self.timeNow = '.'.join(str(datetime.now().date()).split('-')[::-1])
        self.timeNowCHANGE.setText(self.timeNow)

        # Меняем надпись последнего внесения:
        date1 = datetime.strptime(str(self.timeNow), '%d.%m.%Y')
        try:
            date2 = datetime.strptime(str(self.timeThen), '%d.%m.%Y')
        except ValueError:
            self.timeLastCHANGE.setText('Начните сегодня!')
        else:
            self.numDays = abs((date2 - date1).days)

            # Согласовываем надпись
            if self.numDays == 0:
                self.timeLastCHANGE.setText('Сегодня!')
            elif self.numDays == 1:
                self.timeLastCHANGE.setText('Вчера')
            elif self.numDays % 10 == 1:
                self.timeLastCHANGE.setText(str(self.numDays) + ' дней назад')
            elif int(str(self.numDays)[-1]) in (2, 3, 4) and self.numDays % 10 != 1:
                self.timeLastCHANGE.setText(str(self.numDays) + ' дня назад')
            elif int(str(self.numDays)[-1]) in (5, 6, 7, 8, 9, 0) and self.numDays % 10 != 1:
                self.timeLastCHANGE.setText(str(self.numDays) + ' дней назад')
            elif str(self.numDays)[-1] == '1' and self.numDays % 10 != 1:
                self.timeLastCHANGE.setText(str(self.numDays) + ' день назад')

    def timeThen(self):
        # Берём дату последнего внесения из файла
        datefile = open('dates.txt', 'r', encoding='utf-8')
        self.timeThen = ''.join(datefile.readlines())
        datefile.close()
        if self.timeThen == self.timeNow and self.errorcheck is False:
            return True
        return False

    # Функции открытия окон
    def toMAIN(self):
        # При заполнении более одного раза за день открывает окно ERROR
        if START.timeThen(self):
            self.blank6.show()
            self.errorcheck = True
        else:
            self.blank1.show()
            self.blank4.hide()
            self.blank2.hide()

    def toSTAT(self):
        self.blank2.show()

    def toFOOD(self):
        self.blank3.show()

    def toGUIDE(self):
        self.blank4.show()

    def toLIST(self):
        self.blank5.show()

    def toERROR(self):
        self.blank6.show()

    # Все окна закрываются вместе с главным
    def closeEvent(self, event):
        self.blank1.hide()
        self.blank2.hide()
        self.blank3.hide()
        self.blank4.hide()
        self.blank5.hide()


# ------------------------------------------------------------------------------------------------------------------- #


class MAIN(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Main.ui', self)
        # uic.loadUi('error.ui', self)
        # Запускает окно "Внесение данных"

        '''
            Все переменные в ведении данных:
            line_1 по line_8 - декоративные линии
            n1L по n12L - обычные надписи
            mainL, tipL - заголовок и подзаголовок
            filing11 по filing42 - поля ввода
            Hunger1BTN по Hunger4BTN - кнопки ввода сытости
            Check1BTN по Check4BTN - кнопки для проверки корректности ввода
            Checking1L по Checking4L - надписи к проверкам
            AnswerBTN - кнопка подачи данных и завершения введения
            ListBTN - кнопка, переносящая в класс toList
        '''

        # Получаем огромную кучу переменных
        self.userInputFood1 = None
        self.userInputFood2 = None
        self.userInputFood3 = None
        self.userInputFood4 = None
        self.allFoodTemp = []
        self.allFoodStats = []
        self.doneBELKI = 0
        self.doneFATS = 0
        self.doneUGLEVOD = 0
        self.doneGRADE = 0
        self.doneVARIETY = 0
        self.globalVARIETY = 0
        self.doneHUNGER = 0
        self.doneOVERALL = 0
        self.hunger1 = 0
        self.hunger2 = 0
        self.hunger3 = 0
        self.hunger4 = 0
        self.toclosecheck = False
        self.warning = None

        # Создание словаря со всеми переменными датабазы (кроме типа еды)
        con = sqlite3.connect("Foods.sqlite")
        cur = con.cursor()
        result = cur.execute("""SELECT Еда, Белков, Жиров, Углеводов, Оценка, Разнообразие FROM Foods""").fetchall()
        con.close()
        library = {}
        for elem in result:
            library[elem[0]] = elem[1:]
        self.library = library

        # Крутым супер неэфективным способом настраиваем кнопку на показ окна LIST
        self.lwindow = LIST()
        self.ListBTN.clicked.connect(self.showList)

        # Подключение кнопок проверки
        self.Check1BTN.clicked.connect(self.getVALUES1)
        self.Check2BTN.clicked.connect(self.getVALUES2)
        self.Check3BTN.clicked.connect(self.getVALUES3)
        self.Check4BTN.clicked.connect(self.getVALUES4)

        # Проверки для корректоности ответа пользователя
        self.maincheck1 = False
        self.maincheck2 = False
        self.maincheck3 = False
        self.maincheck4 = False

        # Кнопка, отправляющая на финальный подсчет баллов
        self.AnswerBTN.clicked.connect(self.finish)

    # Функции, обрабатывающие пользовательские данные в данные датабазы
    def getVALUES1(self):
        self.maincheck1 = False
        try:
            self.userInputFood1 = (self.filing11.text().rstrip(',').split(', ') +
                                   self.filing12.text().rstrip(',').split(', '))
        except Exception:
            self.Checking1L.setText('Что-то пошло не так')
        MAIN.getGRADES(self, self.userInputFood1, int(self.Hunger1BTN.text()), 1)

    def getVALUES2(self):
        self.maincheck2 = False
        try:
            self.userInputFood2 = (self.filing21.text().rstrip(',').split(', ') +
                                   self.filing22.text().rstrip(',').split(', '))
        except Exception:
            self.Checking2L.setText('Что-то пошло не так')
        MAIN.getGRADES(self, self.userInputFood2, int(self.Hunger2BTN.text()), 2)

    def getVALUES3(self):
        self.maincheck3 = False
        try:
            self.userInputFood3 = (self.filing31.text().rstrip(',').split(', ') +
                                   self.filing32.text().rstrip(',').split(', '))
        except Exception:
            self.Checking3L.setText('Что-то пошло не так')
        MAIN.getGRADES(self, self.userInputFood3, int(self.Hunger3BTN.text()), 3)

    def getVALUES4(self):
        self.maincheck4 = False
        try:
            self.userInputFood4 = (self.filing41.text().rstrip(',').split(', ') +
                                   self.filing42.text().rstrip(',').split(', '))
        except Exception:
            self.Checking4L.setText('Что-то пошло не так')
        MAIN.getGRADES(self, self.userInputFood4, int(self.Hunger4BTN.text()), 4)

    # Функция, проверяющая корректность данных и возвращает баллы
    def getGRADES(self, values, hunger, num):
        print('Значения с проверки:', values)
        temp = []
        if values == ['', ''] or hunger == 0:
            # Если сытость не заполнена, выводит уникальную надпись и вся статистика становится нулем
            if num == 1:
                self.maincheck1 = True
                self.userInputFood1 = []
                self.hunger1 = 0
                self.Checking1L.setText('Всё готово, ничего не ели!')
            elif num == 2:
                self.maincheck2 = True
                self.userInputFood2 = []
                self.hunger2 = 0
                self.Checking2L.setText('Всё готово, ничего не ели!')
            elif num == 3:
                self.maincheck3 = True
                self.userInputFood3 = []
                self.hunger3 = 0
                self.Checking3L.setText('Всё готово, ничего не ели!')
            elif num == 4:
                self.maincheck4 = True
                self.userInputFood4 = []
                self.hunger4 = 0
                self.Checking4L.setText('Всё готово, ничего не ели!')
        for value in values:
            if value != '':
                # При неправильном заполнении выводит ошибку
                try:
                    self.library[value.lower()]
                except KeyError:
                    if num == 1:
                        self.Checking1L.setText(f'Ошибка: {value}!')
                    elif num == 2:
                        self.Checking2L.setText(f'Ошибка: {value}!')
                    elif num == 3:
                        self.Checking3L.setText(f'Ошибка: {value}!')
                    elif num == 4:
                        self.Checking4L.setText(f'Ошибка: {value}!')
                    return
                temp.append(self.library[value.lower()])
                if num == 1:
                    self.maincheck1 = True
                    self.userInputFood1 = temp.copy()
                    self.hunger1 = hunger
                    self.Checking1L.setText('Всё готово!')
                elif num == 2:
                    self.maincheck2 = True
                    self.userInputFood2 = temp.copy()
                    self.hunger2 = hunger
                    self.Checking2L.setText('Всё готово!')
                elif num == 3:
                    self.maincheck3 = True
                    self.userInputFood3 = temp.copy()
                    self.hunger3 = hunger
                    self.Checking3L.setText('Всё готово!')
                elif num == 4:
                    self.maincheck4 = True
                    self.userInputFood4 = temp.copy()
                    self.hunger4 = hunger
                    self.Checking4L.setText('Всё готово!')

    # Производит подсчёт всех баллов
    def finish(self):
        # Проверка на заполнение данных, если что-то не доделано, ничего не происходит
        if self.maincheck1 == self.maincheck2 == self.maincheck3 == self.maincheck4 is True:
            self.warning = WARNING()
            self.warning.show()

            self.allFoodStats = []
            # Удаление пустых строк из списка
            self.allFoodTemp = self.userInputFood1 + self.userInputFood2 + self.userInputFood3 + self.userInputFood4
            for line in self.allFoodTemp:
                if line != '':
                    self.allFoodStats.append(line)
            print('Весь список еды:', self.allFoodStats)
            self.doneHUNGER = (self.hunger1 + self.hunger2 + self.hunger3 + self.hunger4) / 4

            # Назначение всех переменных
            if self.allFoodStats:
                self.doneBELKI = sum([int(n[0]) for n in self.allFoodStats]) / len(self.allFoodStats)
                self.doneFATS = sum([int(n[1]) for n in self.allFoodStats]) / len(self.allFoodStats)
                self.doneUGLEVOD = sum([int(n[2]) for n in self.allFoodStats]) / len(self.allFoodStats)
                self.doneGRADE = sum([int(n[3]) for n in self.allFoodStats]) / len(self.allFoodStats)
                # Засчитывает именно значения блюд а не сами блюда, может избежать проблему с блюдами с нескольками
                # названиями, но в редких случаях может неправильно изменить результат
                self.globalVARIETY = len(set(self.allFoodStats))
                if self.globalVARIETY >= 6:
                    self.globalVARIETY = 6
                self.doneVARIETY = (sum([int(n[4]) for n in self.allFoodStats]) / len(self.allFoodStats)
                                    * self.globalVARIETY / 6)
                self.doneOVERALL = (((self.doneBELKI * 1.3) + (self.doneFATS / 1.5) + (self.doneUGLEVOD * 1.2)) *
                                    (self.doneGRADE / 3) * (self.doneVARIETY / 1.7) * (self.doneHUNGER / 3)) * 0.9
                if self.doneOVERALL > 10:
                    self.doneOVERALL = 10
            else:
                # Если всё по нолям, все переменные сразу равняются нолям, чтобы избежать деления на 0
                self.doneBELKI = 1
                self.doneFATS = 1
                self.doneUGLEVOD = 1
                self.doneGRADE = 1
                self.doneVARIETY = 0
                self.doneOVERALL = 1

        self.toclosecheck = True

    def getCSV(self):
        # Копирует содержание, чтобы не потерять данные
        readinstance = open('userinfo.csv', encoding="utf8")
        filecopy = csv.DictReader(readinstance, delimiter=',', quotechar='"')
        filecopied = list(filecopy)

        writeinstance = open('userinfo.csv', 'w', newline='')
        fieldnames = ['date', 'belki', 'fats', 'uglevod', 'grade', 'variety', 'overall']
        writing = csv.DictWriter(writeinstance, fieldnames=fieldnames)
        writing.writeheader()

        # Записывает все данные обратно вместе с новыми
        for row in filecopied:
            writing.writerow(dict(row))
        timenow = '.'.join(str(datetime.now().date()).split('-')[::-1])
        writing.writerow({'date': timenow, 'belki': round(self.doneBELKI, 2), 'fats': round(self.doneFATS, 2),
                          'uglevod': round(self.doneUGLEVOD, 2), 'grade': round(self.doneGRADE, 2),
                          'variety': round(self.doneVARIETY, 2), 'overall': round(self.doneOVERALL, 2)})

    def getGuideText(self):
        # В зависимости от данных пишет советы
        layout1 = ''
        layout2 = ''
        layout3 = ''
        layout4 = ''
        layout5 = ''
        layout6 = ''
        if self.doneBELKI < 2:
            layout1 = ('* Мало белков! Без белков будут проблемы с мышцами и ростом.\n'
                       '  Добавьте в свой рацион больше молочных продуктов\n')
            self.doneOVERALL *= 0.9

        elif 2 <= self.doneBELKI <= 4:
            layout1 = '* Количество белков в норме!\n'

        elif self.doneBELKI > 4:
            layout1 = ('* Переизбыток белков! Возможны рост нагрузки на почки и повышение холестерина.\n'
                       '  Разнообразьте свой рацион фруктами и овощами\n')
            self.doneOVERALL *= 0.9

        if self.doneFATS < 2:
            layout2 = ('* Мало жиров! При нехватке жиров появляется сухость кожи и неусвоение витаминов.\n'
                       '  Потребляйте больше соусов, орехов и масла.\n')
            self.doneOVERALL *= 0.9

        elif 2 <= self.doneFATS <= 4:
            layout2 = '* Количество жиров в норме!\n'

        elif self.doneFATS > 4:
            layout2 = ('* Переизбыток жиров! Может привести к ожирению и проблемам с печенью.\n'
                       '  Потребляйте меньше вредной еды, больше рыбы и напитков\n')
            self.doneOVERALL *= 0.9

            self.doneOVERALL *= 0.9
        if self.doneUGLEVOD < 2:
            layout3 = ('* Мало углеводов! Приводит к энергетическому дефициту и проблеме с концентрацией.\n'
                       '  Не злоуптребляйте закусками!\n')
            self.doneOVERALL *= 0.8

        elif 2 <= self.doneUGLEVOD <= 4:
            layout3 = '* Количество углеводов в норме!\n'

        elif self.doneUGLEVOD > 4:
            layout3 = ('* Переизбыток углеводов! Может привести к увеличению веса и риску развития диабета.\n'
                       '  Разнообразьте питание напитками, орехами и морепродуктами!\n')
            self.doneOVERALL *= 0.9

        if self.doneGRADE < 2:
            layout4 = '* Качество еды меньше нужного!\n'
            self.doneOVERALL *= 0.8

        elif 2 <= self.doneGRADE <= 3:
            layout4 = '* Качество еды чуть меньше нормы!\n'
            self.doneOVERALL *= 0.95
        elif self.doneGRADE >= 3:
            layout4 = '* Качество еды в порядке!\n'

        if self.doneVARIETY < 0.3:
            layout5 = '* Разнообразие питания на минимуме. Однотипное питание серьезно ухудшает здоровье.\n'

        if 0.3 <= self.doneVARIETY < 1:
            layout5 = '* Разнообразия питания слишком мало. Включите больше продуктов в свой рацион.\n'

        elif 1 <= self.doneVARIETY < 2:
            layout5 = '* Разнообоазьте питание! Включите больше продуктов в свой рацион.\n'

        elif 2 <= self.doneVARIETY <= 3.3:
            layout5 = '* С Разнообразием всё хорошо!\n'

        elif self.doneHUNGER > 3.3:
            layout5 = '* Разнообразие еды превосходно! Так держать!'

        if self.doneHUNGER < 2:
            layout6 = ('* Нужно больше есть!\n'
                       '  Дефицит питания приводит к физическому и психологическому ухудшению организма.\n')
            self.doneOVERALL *= 0.5

        elif 2 <= self.doneHUNGER <= 4:
            layout6 = '* С количеством питания всё хорошо!\n'

        elif self.doneHUNGER > 4:
            layout6 = '* Постарайтесь немного сократить питание!\n'
            self.doneOVERALL *= 0.9

        print('Совет:')
        print(layout1 + layout2 + layout3 + layout4 + layout5 + layout6)
        if self.doneOVERALL < 1:
            self.doneOVERALL = 1
        print(self.doneOVERALL)

        # Открывается текстовый документ, чтобы записать все советы
        guidetxt = open('tip.txt', 'w', encoding='utf-8')
        guidetxt.write(layout1)
        guidetxt.write(layout2)
        guidetxt.write(layout3)
        guidetxt.write(layout4)
        guidetxt.write(layout5)
        guidetxt.write(layout6)
        guidetxt.write(str(round(self.doneOVERALL, 2)))
        guidetxt.close()

        print('Все табличные значения:', self.doneBELKI, self.doneFATS, self.doneUGLEVOD, self.doneGRADE,
              self.doneVARIETY, self.doneHUNGER, self.doneOVERALL)

    def cleanup(self):
        # Очищает все данные после использования
        self.userInputFood1 = None
        self.userInputFood2 = None
        self.userInputFood3 = None
        self.userInputFood4 = None
        self.allFoodTemp = []
        self.allFoodStats = []
        self.doneBELKI = 0
        self.doneFATS = 0
        self.doneUGLEVOD = 0
        self.doneGRADE = 0
        self.doneVARIETY = 0
        self.doneHUNGER = 0
        self.doneOVERALL = 0
        self.globalVARIETY = 0
        self.hunger1 = 0
        self.hunger2 = 0
        self.hunger3 = 0
        self.hunger4 = 0
        self.maincheck1 = False
        self.maincheck2 = False
        self.maincheck3 = False
        self.maincheck4 = False
        self.toclosecheck = False
        self.filing11.setText('')
        self.filing12.setText('')
        self.filing21.setText('')
        self.filing22.setText('')
        self.filing31.setText('')
        self.filing32.setText('')
        self.filing41.setText('')
        self.filing42.setText('')
        self.Hunger1BTN.setValue(0)
        self.Hunger2BTN.setValue(0)
        self.Hunger3BTN.setValue(0)
        self.Hunger4BTN.setValue(0)
        self.Checking1L.setText('Комментарии к проверке')
        self.Checking2L.setText('Комментарии к проверке')
        self.Checking3L.setText('Комментарии к проверке')
        self.Checking4L.setText('Комментарии к проверке')

    # Закрывает окно LIST при закрытии
    def closeEvent(self, event):
        if self.toclosecheck is True:
            MAIN.getGuideText(self)
            MAIN.getCSV(self)
            writedate = open('dates.txt', 'w', encoding='utf-8')
            today = '.'.join(str(datetime.now().date()).split('-')[::-1])
            writedate.write(today)
            writedate.close()

            MAIN.cleanup(self)
        self.lwindow.hide()

    # Открывет то же окно со списком блюд, однако это окно независимо от того, что открывается из главного меню
    def showList(self):
        self.lwindow.show()


# ------------------------------------------------------------------------------------------------------------------- #


class STAT(QMainWindow, Ui_Form):
    def __init__(self):
        super().__init__()
        uic.loadUi('Stats.ui', self)
        # Открывает окно "Статистика"

        self.forstats = []
        self.filecopied = []
        self.check = False
        self.last = 5
        self.names = ('белкам', 'жирам', 'углеводам', 'качеству', 'разнообразию', 'по общей оценке')
        self.lastmaxn = 3
        self.lastdesired = 2
        self.lastminn = 1

        # Запускает функции
        STAT.updatel(self)
        STAT.code1(self)

        # Придаём функциональность к кнопкам
        self.byOVERALL.clicked.connect(self.code1)
        self.byBELKI.clicked.connect(self.code2)
        self.byFATS.clicked.connect(self.code3)
        self.byUGLEVOD.clicked.connect(self.code4)
        self.byGRADE.clicked.connect(self.code5)
        self.byVARIETY.clicked.connect(self.code6)
        self.updateBTN.clicked.connect(self.updatel)
        self.deleteBTN.clicked.connect(self.statdeletion)

    # Получаем нам нужные данные для графиков, можно перезапустить
    def updatel(self):
        readinstance = open('userinfo.csv', encoding="utf8")
        filecopy = csv.DictReader(readinstance, delimiter=',', quotechar='"')
        self.filecopied = list(filecopy)

        self.forstats = []
        for n in range(len(self.filecopied)):
            try:
                self.forstats.append(list(self.filecopied[n].values())[1:])
            except Exception:
                pass
            STAT.StatShow(self, num=self.last, color='aqua', desired=self.lastdesired, maxn=self.lastmaxn,
                          minn=self.lastminn)

    # Каждая кнопка посылает свои данные
    def code1(self):
        STAT.StatShow(self, num=5, desired=7, maxn=10)

    def code2(self):
        STAT.StatShow(self, num=0, desired=3, maxn=5)

    def code3(self):
        STAT.StatShow(self, num=1, desired=3, maxn=5)

    def code4(self):
        STAT.StatShow(self, num=2, desired=3, maxn=5)

    def code5(self):
        STAT.StatShow(self, num=3, desired=3, maxn=5)

    def code6(self):
        STAT.StatShow(self, num=4, desired=2, maxn=3, minn=0)

    # Собирает данные и рисует функцию
    def StatShow(self, num=0, color='white', desired=0, maxn=3, minn=1):
        self.graph.clear()

        offset = 1
        if len(self.forstats) == 0:
            offset = 2

        # Рисуем границы графиков
        self.graph.plot(y=[maxn] * 2, x=[1, len(self.forstats) + offset], pen='lime')
        self.graph.plot(y=[minn] * 2, x=[1, len(self.forstats) + offset], pen='red')

        # Рисуем линию с желаемым результатом
        self.graph.plot(y=[desired] * 2, x=[1, len(self.forstats) + offset], pen='orange')

        # Рисуем сам график
        try:
            self.graph.plot(y=[desired] + [float(m[num]) for m in self.forstats],
                            x=[m + 1 for m in range(len(self.forstats) + 1)], pen=color)
        except Exception:
            print('Неправильные данные для графика')
        # Ставим последние переменные значений положений линий для обновления данных
        self.last = num
        self.lastmaxn = maxn
        self.lastminn = minn
        self.lastdesired = desired

        # Меняем текст в зависимости от выбраного грфика
        self.changebleL.setText(f'Статистика по {self.names[num]}')
        self.minmaxL.setText('Мин/макс значения: ' + str(minn) + ' / ' + str(maxn))

    def statdeletion(self):
        with open('tip.txt', 'w', encoding='utf-8') as del1:
            del1.write('')
            del1.close()
        with open('dates.txt', 'w', encoding='utf-8') as del2:
            del2.write('')
            del2.close()
        with open('userinfo.csv', 'w', newline='') as del3:
            writing = csv.DictWriter(del3, fieldnames='')
            del3.close()
        print('Вся статистика программы удалена, перезайдите для применения изменений')


# ------------------------------------------------------------------------------------------------------------------- #


class FOOD(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Food.ui', self)
    # Запускает окно "Лучшие блюда". Там сплошной текст


# ------------------------------------------------------------------------------------------------------------------- #


class GUIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Guide.ui', self)
        # Запускает окно "Советы"

        self.lines = None
        self.alllines = None

        # Нажатие кнопки обновления выводит на экран новейший совет
        self.refreshBTN.clicked.connect(self.refresh)

    def refresh(self):
        # Берёт txt файл tip и выводит его
        fromfile = open('tip.txt', 'r', encoding='utf-8')
        self.lines = fromfile.readlines()
        fromfile.close()

        self.alllines = ''.join(self.lines[:len(self.lines) - 1])
        self.text.setText(self.alllines)
        try:
            self.grade.setText('Общая оценка: ' + str(self.lines[-1]) + '/10')
        except IndexError:
            print('Советы отсутсвуют')



# ------------------------------------------------------------------------------------------------------------------- #


class LIST(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('List.ui', self)
        # Запускает окно "Список еды"

        # Взятие данных из датабазы
        con = sqlite3.connect("Foods.sqlite")
        cur = con.cursor()
        result = cur.execute("""SELECT Тип, Еда FROM Foods Order by Тип asc""").fetchall()

        # Установка таблицы
        self.table.setColumnCount(2)
        self.table.setRowCount(len(result))

        # Постановление всех данных в таблицу
        for column in range(len(result)):
            for row in range(2):
                self.table.setItem(column, row, QTableWidgetItem(str(result[column][row]).capitalize()))


# ------------------------------------------------------------------------------------------------------------------- #


# Окна предупреждений
class ERROR(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('error.ui', self)


class WARNING(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('warning.ui', self)


# ------------------------------------------------------------------------------------------------------------------- #


# Запуск программы
if __name__ == '__main__':
    app = QApplication(sys.argv)
    starter = START()
    starter.show()
    sys.exit(app.exec_())
