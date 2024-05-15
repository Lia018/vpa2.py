import tkinter as tk
from tkinter import messagebox, simpledialog, OptionMenu
from sqlalchemy import create_engine,text
from PIL import Image, ImageTk
import pandas as pd
import random
import psycopg2

class FilmMatchmakerApp:

    def __init__(self, root):
        self.engine = create_engine('postgresql://postgres:admin@localhost:5432/postgres')

        self.root = root
        self.root.configure(bg='#5EC5D4')
        self.root.title("Movie Matchmaker")
        self.root.geometry('400x400')
        self.center_window(self.root)
        self.preferences_listbox = []

        self.menu_frame = tk.Frame(root, bg='#5EC5D4')
        self.menu_frame.pack(pady=10)

        self.login_button = tk.Button(self.menu_frame, text="Prihlásiť", bg='#A782EC', command=self.login)
        self.login_button.grid(row=0, column=0, padx=10)

        self.register_button = tk.Button(self.menu_frame, text="Registrovať", bg='#A782EC', command=self.register)
        self.register_button.grid(row=0, column=1, padx=10)

        #https://www.dlf.pt/ddetail/bJbxiJ_movie-night-vector-png-transparent-png/
        image1_path = "C:/Users/Lia/PycharmProjects/Match/venv/movie1.png"
        original_image1 = Image.open(image1_path)
        resized_image1 = original_image1.resize((150, 150))
        self.menu_image = ImageTk.PhotoImage(resized_image1)
        self.menu_image_label = tk.Label(self.menu_frame, image=self.menu_image, bg='#5EC5D4')
        self.menu_image_label.grid(row=1, column=0, columnspan=2, pady=70)

        self.match_frame = tk.Frame(root, bg='#5EC5D4')

        self.match_button = tk.Button(self.match_frame, text="Nájdi film", bg='#A782EC', command=self.find_match)
        self.match_button.pack(pady=10)

        #https://gist.github.com/tiangechen/b68782efa49a16edaf07dc2cdaa855ea#file-movies-csv
        genres = pd.read_sql_query('SELECT DISTINCT genre FROM vpa.genres', con=self.engine)
        movie_genres = genres['genre'].tolist()
        self.available_genres = sorted(movie_genres)

        self.genre_var = tk.StringVar()
        self.genre_var.set(self.available_genres[0])
        self.genre_menu = OptionMenu(self.match_frame, self.genre_var, *self.available_genres)
        self.genre_menu.pack(pady=10)
        self.genre_menu.configure(bg='#A782EC')
        self.genre_menu["highlightbackground"] = '#5EC5D4'

        self.available_films = self.get_available_films()

        self.edit_preferences_button = tk.Button(self.match_frame, text="Upraviť preferencie", bg='#A782EC', command=self.edit_preferences)
        self.edit_preferences_button.pack(pady=10)

        self.logout_button = tk.Button(self.match_frame, text="Odhlásiť sa", bg='#A782EC', command=self.logout)
        self.logout_button.pack(pady=10)

        #https://www.dlf.pt/ddetail/mbhbbx_lights-action-hollywood-clip-movie-lights-camera-action/
        #image2_path = "C:/Users/Lia/PycharmProjects/Match/venv/movie2.png"
        image2_path = "movie2.png"
        original_image2 = Image.open(image2_path)
        resized_image2 = original_image2.resize((150, 150))
        self.match_image = ImageTk.PhotoImage(resized_image2)
        image_label_match = tk.Label(self.match_frame, image=self.match_image, bg='#5EC5D4')
        image_label_match.pack(pady=20)

        self.film_var = tk.StringVar()

        self.logged_user_id = None
        self.register_window = None
        self.login_window = None

    def center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def get_available_films(self):
        selected_genre = self.genre_var.get()
        query = 'SELECT title FROM vpa.movies JOIN vpa.genres ON movies.movieid = genres.movieid WHERE genre = %s'
        films_in_genre = pd.read_sql_query(query, con=self.engine, params=[(selected_genre,)])
        all_titles = films_in_genre['title'].tolist()
        return sorted(all_titles)

    def login(self):
        self.root.withdraw()
        self.login_window = tk.Toplevel(self.root, bg='#5EC5D4')
        self.login_window.title("Prihlásenie")
        self.login_window.geometry('400x400')
        self.center_window(self.login_window)

        label_id = tk.Label(self.login_window, bg='#5EC5D4', text="Zadajte svoje ID:")
        label_id.pack(pady=10)

        entry_id = tk.Entry(self.login_window)
        entry_id.pack(pady=10)

        label_password = tk.Label(self.login_window, bg='#5EC5D4', text="Zadajte heslo:")
        label_password.pack(pady=10)

        entry_password = tk.Entry(self.login_window, show="*")
        entry_password.pack(pady=10)

        show_password_var = tk.BooleanVar()
        show_password_checkbox = tk.Checkbutton(self.login_window, bg='#5EC5D4', text="Zobraziť heslo", variable=show_password_var, command=lambda: self.toggle_password_visibility(entry_password, show_password_var.get()))
        show_password_checkbox.pack(pady=10)

        submit_button = tk.Button(self.login_window, bg='#A782EC', text="Prihlásiť", command=lambda: self.process_login(entry_id.get(), entry_password.get()))
        submit_button.pack(pady=10)

    def on_close(self):
        self.root.deiconify()

    def toggle_password_visibility(self, entry, show_password):
        if show_password:
            entry.config(show="")
        else:
            entry.config(show="*")

    def process_login(self, user_id, password):
        with self.engine.connect() as connection:
            query = text("SELECT name, pass FROM vpa.users WHERE userid = :userid")
            result = connection.execute(query.bindparams(userid=user_id)).fetchone()

        if result:
            stored_name, stored_password = result

            if password == stored_password:
                messagebox.showinfo("Úspech", f"Vitajte späť, {stored_name}!")
                self.logged_user_id = user_id

                if self.login_window:
                    self.login_window.destroy()
                self.show_match_frame()
                self.on_close()
            else:
                messagebox.showwarning("Chyba", "Neplatné ID alebo heslo")
        else:
            messagebox.showwarning("Chyba", "Neplatné ID alebo heslo")

    def register(self):
        self.root.withdraw()
        self.register_window = tk.Toplevel(self.root, bg='#5EC5D4')
        self.register_window.title("Registrácia")
        self.register_window.geometry('400x400')
        self.center_window(self.register_window)

        label_name = tk.Label(self.register_window, bg='#5EC5D4', text="Zadajte svoje meno:")
        label_name.pack(pady=10)

        entry_name = tk.Entry(self.register_window)
        entry_name.pack(pady=10)

        label_password = tk.Label(self.register_window, bg='#5EC5D4', text="Zadajte heslo:")
        label_password.pack(pady=10)

        entry_password = tk.Entry(self.register_window, show="*")
        entry_password.pack(pady=10)

        show_password_var = tk.BooleanVar()
        show_password_checkbox = tk.Checkbutton(self.register_window, bg='#5EC5D4', text="Zobraziť heslo", variable=show_password_var, command=lambda: self.toggle_password_visibility(entry_password, show_password_var.get()))
        show_password_checkbox.pack(pady=10)

        submit_button = tk.Button(self.register_window, bg='#A782EC', text="Registrovať", command=lambda: self.process_registration(entry_name.get(), entry_password.get()))
        submit_button.pack(pady=10)

    def process_registration(self, name, password):
        if len(name) < 3 or len(password) < 3:
            messagebox.showwarning("Chyba", "Meno a heslo musia mať aspoň 3 znaky")
            return

        #if len(name) < 3 or len(password) < 8 or not any(char.isupper() for char in password) or not any(
         #       char.isdigit() for char in password):
          #  messagebox.showwarning("Chyba",
           #                        "Meno musí mať aspoň 3 znaky a heslo musí mať aspoň 8 znakov s jedným veľkým písmenom a jednou číslicou.")
            #return

        if not self.is_unique_name(name):
            messagebox.showwarning("Chyba", "Používateľ s týmto menom už existuje. Zadajte unikátne meno")
            return

        user_id = self.generate_unique_id()

        with self.engine.connect() as connection:
            query = text("INSERT INTO vpa.users (userid, name, pass) VALUES (:userid, :name, :password)")
            result = connection.execute(query, {"userid": user_id, "name": name, "password": password})
            connection.commit()

        messagebox.showinfo("Registrácia", f"Váš účet bol úspešne registrovaný. Vaše ID: {user_id}")
        if self.register_window:
            self.register_window.destroy()
        self.show_menu_frame()
        self.on_close()

    def is_unique_name(self, name):
        with self.engine.connect() as connection:
            query = text("SELECT COUNT(*) FROM vpa.users WHERE name = :name")
            result = connection.execute(query, {"name": name})
            count = result.fetchone()[0]
            return count == 0
        return False

    def generate_unique_id(self):
        with self.engine.connect() as connection:
            while True:
                user_id = str(random.randint(100000, 999999))
                query = text("SELECT COUNT(*) FROM vpa.users WHERE userid = :user_id")
                result = connection.execute(query, {"user_id": user_id})
                count = result.fetchone()[0]

                if count == 0:
                    return user_id

    def show_match_frame(self):
        if not self.logged_user_id:
            return

        self.menu_frame.pack_forget()
        self.match_frame.pack(pady=10)

        self.load_user_preferences()

    def load_user_preferences(self):
        if self.logged_user_id:
            selected_genre = self.genre_var.get()

            with self.engine.connect() as connection:
                preferences_query = text(
                    """SELECT movies.title
                    FROM vpa.movies
                    JOIN vpa.genres ON movies.movieid = genres.movieid
                    JOIN vpa.preferences ON movies.movieid = preferences.movieid
                    WHERE preferences.userid = :user_id
                    AND genres.genre = :selected_genre"""
                )
                preferences_result = connection.execute(preferences_query, {"user_id": self.logged_user_id,
                                                                            "selected_genre": selected_genre})

                current_preferences = [row[0] for row in preferences_result]

                available_films = self.get_available_films()
                for film_var, film in zip(self.preferences_listbox, self.get_available_films()):
                    film_var.set(1 if film in current_preferences else 0)

    def edit_preferences(self):
        self.root.withdraw()
        edit_window = tk.Toplevel(self.root, bg='#5EC5D4')
        edit_window.title("Upraviť preferencie")
        edit_window.geometry('400x400')
        self.center_window(edit_window)

        label = tk.Label(edit_window, bg='#5EC5D4', text="Vyberte filmy:")
        label.pack(pady=10)

        checkboxes_frame = tk.Frame(edit_window)
        checkboxes_frame.pack(side=tk.TOP, pady=10)

        canvas = tk.Canvas(checkboxes_frame)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(checkboxes_frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        frame = tk.Frame(canvas)
        canvas.create_window((0, 0), window=frame, anchor=tk.NW)

        self.preferences_listbox = []

        for film in self.get_available_films():
            film_var = tk.IntVar(value=0)
            checkbox = tk.Checkbutton(frame, text=film, variable=film_var)
            checkbox.pack(anchor=tk.W)
            self.preferences_listbox.append(film_var)

        canvas.configure(yscrollcommand=scrollbar.set)

        frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        save_button_frame = tk.Frame(edit_window)
        save_button_frame.pack(side=tk.BOTTOM, pady=10)

        save_button = tk.Button(save_button_frame, bg='#A782EC', text="Uložiť",
                                command=lambda: self.save_preferences_and_close(edit_window))
        save_button.pack()

        self.load_user_preferences()

    def save_preferences_and_close(self, edit_window):
        self.save_preferences()
        edit_window.destroy()
        self.on_close()

    def save_preferences(self):

        selected_films_delete = [film for film_var, film in zip(self.preferences_listbox, self.get_available_films()) if
                                 film_var.get() == 0]

        selected_films_insert = [film for film_var, film in zip(self.preferences_listbox, self.get_available_films()) if
                                 film_var.get() == 1]

        with self.engine.connect() as connection:
            with connection.begin():
                delete_query = text(
                    """DELETE FROM vpa.preferences
                    WHERE userid = :user_id
                    AND movieid IN (
                        SELECT m.movieid
                        FROM vpa.movies m
                        JOIN vpa.genres g ON m.movieid = g.movieid
                        WHERE m.title = :title)"""
                )

                for film_title in selected_films_delete:
                    connection.execute(delete_query, {"user_id": self.logged_user_id, "title": film_title})

                insert_query = text(
                    """INSERT INTO vpa.preferences (userid, movieid)
                    SELECT :user_id, m.movieid
                    FROM vpa.movies m
                    JOIN vpa.genres g ON m.movieid = g.movieid
                    WHERE m.title = :title"""
                )
                for film_title in selected_films_insert:
                    connection.execute(insert_query, {"user_id": self.logged_user_id, "title": film_title})

        messagebox.showinfo("Uložené", "Vaše preferencie boli úspešne uložené")
        self.show_match_frame()

    def find_match(self):

        other_user_id = simpledialog.askstring("Hľadať zhodu", "Zadajte ID používateľa pre hľadanie zhody:")

        if other_user_id is None:
            return

        if  len(str(other_user_id)) != 6:
            messagebox.showwarning("Chyba", "Zadaj ID používateľa")
            return

        if other_user_id == self.logged_user_id:
            messagebox.showwarning("Chyba", "Nemôžete hľadať zhodu so sebou")
            return

        user_exists_query = text(
            "SELECT COUNT(*) FROM vpa.users WHERE userid = :other_user_id"
        )
        with self.engine.connect() as connection:
            user_exists_result = connection.execute(user_exists_query, {"other_user_id": other_user_id}).fetchone()

        if user_exists_result[0] == 0:
            messagebox.showwarning("Chyba", "Neplatné ID používateľa")
            return

        logged_user_preferences_query = text(
            """SELECT p.movieid
            FROM vpa.preferences p
            JOIN vpa.genres g ON p.movieid = g.movieid
            WHERE p.userid = :logged_user_id
            """
        )

        logged_user_preferences = set()
        with self.engine.connect() as connection:
            logged_user_preferences_result = connection.execute(logged_user_preferences_query,
                                                                {"logged_user_id": self.logged_user_id})
            for row in logged_user_preferences_result:
                logged_user_preferences.add(row[0])

        if not logged_user_preferences:
            messagebox.showwarning("Chyba", "Vyberte filmy, ktoré si chcete pozrieť")
            return

        other_user_preferences_query = text(
            """SELECT p.movieid
            FROM vpa.preferences p
            JOIN vpa.genres g ON p.movieid = g.movieid
            WHERE p.userid = :other_user_id
            """
        )

        other_user_preferences = set()
        with self.engine.connect() as connection:
            other_user_preferences_result = connection.execute(other_user_preferences_query,
                                                               {"other_user_id": other_user_id})
            for row in other_user_preferences_result:
                other_user_preferences.add(row[0])

        if not other_user_preferences:
            messagebox.showwarning("Chyba", f"Používateľ {other_user_id} nemá žiadne filmy v preferenciách")
            return

        common_films = logged_user_preferences & other_user_preferences

        if common_films:
            common_films_titles_query = text(
                "SELECT title FROM vpa.movies WHERE movieid IN :common_films"
            )
            common_films_titles = []
            with self.engine.connect() as connection:
                common_films_titles_result = connection.execute(common_films_titles_query,
                                                                {"common_films": tuple(common_films)})
                for row in common_films_titles_result:
                    common_films_titles.append(row[0])

            sorted_common_films = sorted(common_films_titles)
            messagebox.showinfo("Vaša zhoda je",
                                f"Spoločné filmy s používateľom {other_user_id}: {', '.join(sorted_common_films)}")
        else:
            messagebox.showinfo("Žiadna zhoda", f"Nenašiel sa spoločný film s používateľom {other_user_id}")

    def logout(self):
        self.logged_user_id = None
        self.show_menu_frame()
        self.genre_var.set(self.available_genres[0])

    def show_menu_frame(self):
        self.match_frame.pack_forget()
        self.menu_frame.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = FilmMatchmakerApp(root)
    root.mainloop()
