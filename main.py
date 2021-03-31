from datetime import datetime
from flask import Flask, render_template, redirect
from data import db_session
from data.our_users import User
from data.news import News
from forms.user import RegisterForm
from forms.login import LoginForm
from flask_login import login_user

from flask_login import LoginManager, logout_user, login_required

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

# новенькие функции
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    news = db_sess.query(News).filter(News.is_private != True)
    return render_template("index.html", news=news)


@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data,
            about=form.about.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login_for_news.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login_for_news.html', title='Авторизация', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


def main():
    db_session.global_init("db/blogs.db")
    db_sess = db_session.create_session()

    # добавление пользователей
    # user = User()
    # user.name = "Пользователь 1"
    # user.about = "биография пользователя 1"
    # user.email = "email@gmail.com"
    # db_sess.add(user)
    #
    # user = User()
    # user.name = "Пользователь 2"
    # user.about = "биография пользователя 2"
    # user.email = "email@mail.ru"
    # db_sess.add(user)
    #
    # user = User()
    # user.name = "Пользователь 3"
    # user.about = "биография пользователя 3"
    # user.email = "email@yandex.ru"
    #
    # db_sess.commit()

    # вывод всех пользователей
    for user in db_sess.query(User).all():
        print(user)

    print()

    # фильтруем данные: ',' - аналог AND,  '|' - аналог ИЛИ, скобки частей - обязательны
    for user in db_sess.query(User).filter((User.id > 1), (User.email.notilike("%yandex%"))):
        print(user)

    print()

    # изменение данных: ищем - меняем - коммитим
    user = db_sess.query(User).filter(User.id == 1).first()
    print(user)
    user.name = "Измененное имя пользователя12"
    user.created_date = datetime.now()
    db_sess.commit()
    print(user)

    # удаление всех по фильтру
    # db_sess.query(User).filter(User.id >= 3).delete()
    # db_sess.commit()
    # # или кого-то конкретного
    # user = db_sess.query(User).filter(User.id == 2).first()
    # db_sess.delete(user)
    # db_sess.commit()

    # добавление новости объекту USER
    user = db_sess.query(User).filter(User.id == 1).first()
    news = News(title="Первая новость", content="УРАААААА!!!!!",
                user=user, is_private=False)
    db_sess.add(news)
    db_sess.commit()

    # взаимодействие со списоком новостей
    user = db_sess.query(User).filter(User.id == 1).first()
    news = News(title="Личная запись #1", content="Эта запись личная",
                is_private=True)
    user.news.append(news)
    db_sess.commit()

    user = db_sess.query(User).filter(User.id == 2).first()
    news = News(title="Личная запись #33", content="Эта запись пользователя №2, вот так то",
                is_private=False)
    user.news.append(news)
    db_sess.commit()

    print()
    for news in user.news:
        print(news)

    app.run(debug=True)


if __name__ == '__main__':
    main()
