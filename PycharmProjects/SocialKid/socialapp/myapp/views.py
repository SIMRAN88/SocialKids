from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from models import User, SessionToken, PostModel, LikeModel, CommentModel
from datetime import timedelta
from django.utils import timezone
import os

from clarifai import *
from clarifai.rest import ClarifaiApp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from imgurpython import ImgurClient

# for sending mail to user
from sendgrid.helpers.mail import *
import sendgrid
sendgrid_key = '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'

# Set up clarifai and define a model
app = ClarifaiApp(api_key='e9aa8985bec24eea80bc92cf07e72880')
model = app.models.get('general-v1.3')

from paralleldots import set_api_key, sentiment
PKEY = 'RSElfqhPZOqwmkYdqIq4SpRSMBHYDMeH7nzc0edlBz8'

# Create your views here.
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            # saving data to DB
            user = User(name=name, password=make_password(password), email=email, username=username)
            user.save()
            sg = sendgrid.SendGridAPIClient(apikey=sendgrid_key)
            from_email = Email("socialkids2017@gmail.com")
            to_email = Email(email)
            subject = "Social Kids"
            content = Content("text/plain", "you are successfully signed up!! Welcome on board")
            mail = Mail(from_email, subject, to_email, content)
            response = sg.client.mail.send.post(request_body=mail.get())

            return render(request, 'success.html')

            # return redirect('login/')
    else:
        form = SignUpForm()

    return render(request, 'index.html', {'form': form})


def login_view(request):
    dict = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            # SQL QUERY
            user = User.objects.filter(username=username).first()
            if user:
                # Check for the password
                if not check_password(password, user.password):
                    print 'incorrect password'
                    dict['message'] = 'Incorrect Password! Please try again!'
                else:
                    print 'Valid'
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('/post/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
            else:
                print 'User does not exist'
    else:
        form = LoginForm()

    dict['form'] = form
    return render(request, 'login.html', dict, {'userprint': username})
    return render(request, 'post.html',  {'userprint': username})
    return render(request, 'feed.html',  {'userprint': username})


def post_view(request):
    user = check_validation(request)

    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                caption = form.cleaned_data.get('caption')
                post = PostModel(user=user, image=image, caption=caption)
                post.save()

                path = str(BASE_DIR + '/' + post.image.url)

                client = ImgurClient('0e144dffb567600', '17ed6b09b6b16a35f32bfcd307e1b21cb132b21e')
                post.image_url = client.upload_from_path(path, anon=True)['link']

                # using calrifai
                response_image = model.predict_by_url(url=post.image_url)
                right = response_image['outputs'][0]['data']['concepts'][0]['value']

                # using paralleldots
                set_api_key(PKEY)
                response = sentiment(str(caption))
                sentiment_score = response["sentiment"]
                if sentiment_score >= 0.6 and right > 0.5:
                    post.save()
                    saved_message = 'Post can be submitted'
                    return render(request, 'error.html', {'context': saved_message})
                else:
                    error_message = 'Post cannot be submitted'
                    post.delete()
                    return render(request, 'error.html', {'context': error_message})

            return redirect('/post/')

        else:
            form = PostForm()
        return render(request, 'post.html', {'form': form})
    else:
        return redirect('/login/')


def feed_view(request):
    user = check_validation(request)
    if user:
        posts = PostModel.objects.all().order_by('-created_on')
        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts': posts})
    else:

        return redirect('/login/')


def like_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = LikeForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
            else:
                existing_like.delete()

            return redirect('/feed/')
    else:
        return redirect('/login/')


def comment_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            post_id = form.cleaned_data.get('post').id
            comment_text = form.cleaned_data.get('comment_text')
            comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
            comment.save()
            return redirect('/feed/')
        else:
            return redirect('/feed/')
    else:
        return redirect('/login')

# View to log the user out
def logout_view(request):
    if request.method == 'GET':
        if request.COOKIES.get('session_token'):
            SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).delete()
        return redirect('/login/')
    else:
        return redirect('/feed/')

# For validating the session
def check_validation(request):
    if request.COOKIES.get('session_token'):
        session = SessionToken.objects.filter(session_token=request.COOKIES.get('session_token')).first()
        if session:
            time_to_live = session.created_on + timedelta(days=1)
            if time_to_live > timezone.now():
                return session.user
    else:
        return None
