import random
import smtplib
import textwrap
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from home_menu.models import Customer

from functools import wraps
from home_menu.models import Dish


def show_index(request):
	card_items = Dish.objects.all()
	return render(request, 'index.html', context={
		'card_items': card_items
	})


def show_registration(request):
	return render(request, 'registration.html')


def show_auth(request):
	return render(request, 'auth.html')


def show_recovery(request):
	return render(request, 'recovery.html')


@login_required
def show_lk(request, context={}):
	user_id = request.user.id
	customer = Customer.objects.get(user=user_id)
	context['first_name'] = request.user.first_name
	context['email'] = request.user.email
	return render(request, 'lk.html', context)


def show_card(request, card_id):
	card_item = Dish.objects.filter(id=card_id)
	total_calories = sum([product.weight for dish in card_item for product in dish.product.all()])
	return render(request, 'card.html', context={
		'card_item': card_item,
		'total_calories': total_calories
	})


def show_order(request):
	return render(request, 'order.html')


def show_privacy_policy(request):
	return render(request, 'privacy.html')


def show_terms_of_use(request):
	return render(request, 'terms.html')


@login_required
def pay(request):
	return render(request, 'pay.html')


def sign_up(request, context={}):
	if request.method == 'POST':
		name = request.POST['name']
		email = request.POST['email']
		password = request.POST['password']
		password_confirm = request.POST['PasswordConfirm']

		if User.objects.filter(email=email).exists():
			context['error'] = """Такой пользователь уже зарегистрирован.
			Если вы не помните свой пароль,
			сделайте, пожалуйста, запрос на восстановление."""
			return render(request, 'registration.html', context)
		elif password == password_confirm:
			user = User.objects.create_user(
				first_name=name,
				username=email,
				email=email,
				password=password,
			)
			Customer.objects.create(
				user=user,
			)
			login(request, user)
			return redirect('lk')
		else:
			context['error'] = """Пароли не совпадают.
			Пожалуйста, попробуйте снова."""
			return render(request, 'registration.html', context)
	else:
		context['error'] = 'Ошибка: неверный тип запроса.'
		return render(request, 'registration.html', context)


def sign_in(request, context={}):
	if request.method == 'POST':
		email = request.POST.get('email')
		password = request.POST.get('password')

		user = auth.authenticate(username=email, password=password)

		if user is not None:
			auth.login(request, user)
			return redirect('lk')
		else:
			context['error'] = 'Неверный логин или пароль'
			return render(request, 'auth.html', context)
	else:
		context['error'] = 'Ошибка: неверный тип запроса.'
		return render(request, 'auth.html', context)


def sign_out(request):
	logout(request)
	return redirect('main_page')


def recover_password(request, context={}):
	if request.method == 'POST':
		receiver_email = request.POST.get('email')

		try:
			user = User.objects.get(username=receiver_email)
		except User.DoesNotExist:
			context['error'] = 'Данный email не зарегистрирован в системе.'
			return render(request, 'recovery.html', context)

		new_password = random.randint(100000, 999999)
		user.set_password(f"{new_password}")
		user.save()
		text = f"""Здравствуйте! Ваш новый пароль: {new_password}.
			Пожалуйста, поменяйте его на более надёжный как можно скорее."""
		formatted_text = textwrap.fill(text, 48)

		try:
			send_email(receiver_email, "Восстановление пароля FoodPlan", formatted_text)
			context['message'] = 'Новый пароль отправлен на указанный email.'
		except Exception as error:
			print('Ошибка при отправке почты:', str(error))

		return render(request, 'auth.html', context)

	else:
		context['error'] = 'Ошибка: неверный тип запроса.'
		return render(request, 'recovery.html', context)


def send_email(receiver_email, subject, text):
	sender_email = settings.SENDER_EMAIL
	sender_password = settings.SENDER_PASSWORD

	smtp_server = 'smtp.yandex.ru'
	smtp_port = 587

	message = MIMEMultipart()
	message['From'] = sender_email
	message['To'] = receiver_email
	message['Subject'] = subject

	message.attach(MIMEText(text, 'plain'))

	server = smtplib.SMTP(smtp_server, smtp_port)
	server.starttls()
	server.login(sender_email, sender_password)
	server.sendmail(sender_email, receiver_email, message.as_string())
	server.quit()


def change_info(request, context={}):
	if request.method == 'POST':
		new_name = request.POST.get('name')
		new_email = request.POST.get('email')
		new_password = request.POST.get('password')
		new_password_confirm = request.POST.get('PasswordConfirm')

		user = request.user

		if user.first_name != new_name:
			user.first_name = new_name
		if user.email != new_email:
			user.email = new_email
		if new_password and new_password == new_password_confirm:
			user.set_password(new_password)

		user.save()
		login(request, user)
		return redirect('lk')
	else:
		context['error'] = 'Ошибка: неверный тип запроса.'
		return render(request, 'lk.html', context)
