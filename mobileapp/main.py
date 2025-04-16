from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivy.uix.scrollview import ScrollView
from kivymd.uix.screenmanager import MDScreenManager
from urllib.parse import urlparse
import mysql.connector

db_url = "mysql://root:cytxyYnjPyYDjsfkyKLEhPHsNyxumpkT@metro.proxy.rlwy.net:10106/railway"
parsed_url = urlparse(db_url)
DB_CONFIG = {
    'host': parsed_url.hostname,
    'user': parsed_url.username,
    'password': parsed_url.password,
    'database': parsed_url.path[1:],
    'port': parsed_url.port
}

KV = '''
MDScreenManager:
    LoginScreen:
    LocationScreen:
    AddLocationScreen:

<LoginScreen>:
    name: 'login'
    MDBoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 10

        MDLabel:
            text: "CityMap"
            halign: "center"
            font_style: "H4"
            theme_text_color: "Custom"
            text_color: 0, 0.6, 1, 1

        MDTextField:
            id: username
            hint_text: "Имя пользователя"
            mode: "rectangle"

        MDTextField:
            id: password
            hint_text: "Пароль"
            mode: "rectangle"
            password: True

        MDRaisedButton:
            text: "Войти"
            pos_hint: {"center_x": 0.5}
            on_press: app.login()

        MDRaisedButton:
            text: "Зарегистрироваться"
            pos_hint: {"center_x": 0.5}
            on_press: app.register()

        MDLabel:
            id: status_label
            text: ""
            halign: "center"
            theme_text_color: "Hint"

<LocationScreen>:
    name: 'locations'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)

        MDBoxLayout:
            orientation: 'horizontal'
            spacing: dp(10)
            size_hint_y: None
            height: dp(50)

            MDDropDownItem:
                id: sort_dropdown
                text: "Сортировка"
                on_release: app.open_sort_menu()

            MDDropDownItem:
                id: filter_dropdown
                text: "Тип локации"
                on_release: app.open_filter_menu()

            MDRaisedButton:
                text: "Добавить локацию"
                on_release: app.change_screen('add_location')

        ScrollView:
            MDGridLayout:
                id: location_list
                cols: 1
                adaptive_height: True
                spacing: dp(10)

<AddLocationScreen>:
    name: 'add_location'
    MDBoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 15

        MDLabel:
            text: "Добавить локацию"
            halign: "center"
            font_style: "H5"

        MDTextField:
            id: name
            hint_text: "Название"
            mode: "rectangle"

        MDTextField:
            id: description
            hint_text: "Описание"
            mode: "rectangle"

        MDTextField:
            id: address
            hint_text: "Адрес"
            mode: "rectangle"

        MDTextField:
            id: type
            hint_text: "Тип (например, Парк, Музей)"
            mode: "rectangle"

        MDRaisedButton:
            text: "Сохранить"
            on_press: app.save_location()

        MDRaisedButton:
            text: "Назад"
            on_press: app.change_screen('locations')
'''

class LoginScreen(MDScreen): pass
class LocationScreen(MDScreen): pass
class AddLocationScreen(MDScreen): pass

class CityMapApp(MDApp):
    sort_by = 'newest'
    filter_type = None

    def build(self):
        self.sort_menu = None
        self.filter_menu = None
        return Builder.load_string(KV)

    def change_screen(self, name):
        self.root.current = name
        if name == 'locations':
            self.update_location_list()

    def login(self):
        screen = self.root.get_screen('login')
        username = screen.ids.username.text.strip()
        password = screen.ids.password.text.strip()
        status = screen.ids.status_label

        if not username or not password:
            status.text = "Заполните все поля"
            return

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            self.change_screen('locations')
        else:
            status.text = "Неверное имя или пароль"

    def register(self):
        screen = self.root.get_screen('login')
        username = screen.ids.username.text.strip()
        password = screen.ids.password.text.strip()
        status = screen.ids.status_label

        if not username or not password:
            status.text = "Заполните все поля"
            return

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE name=%s", (username,))
        if cursor.fetchone():
            status.text = "Пользователь уже существует"
            conn.close()
            return

        cursor.execute("INSERT INTO users (name, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        conn.close()

        self.change_screen('locations')

    def update_location_list(self):
        screen = self.root.get_screen('locations')
        container = screen.ids.location_list
        container.clear_widgets()

        query = "SELECT * FROM locations"
        conditions = []
        values = []

        if self.filter_type:
            conditions.append("type = %s")
            values.append(self.filter_type)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at ASC" if self.sort_by == 'oldest' else " ORDER BY created_at DESC"

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, tuple(values))
        locations = cursor.fetchall()
        conn.close()

        for location in locations:
            card = MDCard(orientation='vertical', padding=15, size_hint=(1, None), height='200dp', elevation=6)
            box = BoxLayout(orientation='vertical', spacing=8)

            box.add_widget(MDLabel(text=location['name'], font_style="H6", theme_text_color="Primary"))
            box.add_widget(MDLabel(text=location['description'], theme_text_color="Secondary"))
            box.add_widget(MDLabel(text=f"Адрес: {location['address']}", theme_text_color="Hint"))
            box.add_widget(MDLabel(text=f"Дата: {location['created_at'].strftime('%Y-%m-%d')}", theme_text_color="Hint"))

            card.add_widget(box)
            container.add_widget(card)

    def save_location(self):
        screen = self.root.get_screen('add_location')
        name = screen.ids.name.text.strip()
        description = screen.ids.description.text.strip()
        address = screen.ids.address.text.strip()
        type_ = screen.ids.type.text.strip()

        if not all([name, description, address, type_]):
            return

        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO locations (name, description, address, type, created_at) VALUES (%s, %s, %s, %s, NOW())",
            (name, description, address, type_)
        )
        conn.commit()
        conn.close()

        self.change_screen('locations')

    def open_sort_menu(self):
        if not self.sort_menu:
            self.sort_menu = MDDropdownMenu(
                caller=self.root.get_screen('locations').ids.sort_dropdown,
                items=[
                    {"text": "По новизне", "on_release": lambda x='newest': self.set_sort(x)},
                    {"text": "По старизне", "on_release": lambda x='oldest': self.set_sort(x)},
                ],
                width_mult=4
            )
        self.sort_menu.open()

    def open_filter_menu(self):
        if not self.filter_menu:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT type FROM locations")
            types = cursor.fetchall()
            conn.close()

            self.filter_menu = MDDropdownMenu(
                caller=self.root.get_screen('locations').ids.filter_dropdown,
                items=[
                    {"text": "Все", "on_release": lambda x=None: self.set_filter(x)}
                ] + [
                    {"text": t[0], "on_release": lambda x=t[0]: self.set_filter(x)} for t in types
                ],
                width_mult=4
            )
        self.filter_menu.open()

    def set_sort(self, sort):
        self.sort_by = sort
        label = "По новизне" if sort == 'newest' else "По старизне"
        self.root.get_screen('locations').ids.sort_dropdown.set_item(label)
        self.sort_menu.dismiss()
        self.update_location_list()

    def set_filter(self, filter_type):
        self.filter_type = filter_type
        label = filter_type if filter_type else "Все"
        self.root.get_screen('locations').ids.filter_dropdown.set_item(label)
        self.filter_menu.dismiss()
        self.update_location_list()

if __name__ == '__main__':
    CityMapApp().run()
