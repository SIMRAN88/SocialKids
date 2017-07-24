import os
from datetime import timedelta
from clarifai.rest import ClarifaiApp
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone

from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from models import User, SessionToken, PostModel, LikeModel, CommentModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from imgurpython import ImgurClient

import smtplib
# for sending mail to user
#sendgrid_key = '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'

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

            send_mail('Subject here', 'Here is the message.', 'socialkids2017@gmail.com', [email],
                      fail_silently=False)

            return render(request, 'success.html')

            # return redirect('login/')
    else:
        form = SignUpForm()

    return render(request, 'index.html', {'form': form})


def login_view(request):
    response_data = {}
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = User.objects.filter(username=username).first()

            if user:
                if check_password(password, user.password):
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()
                    response = redirect('/feed/')
                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    response_data['message'] = 'Incorrect Password! Please try again!'

    elif request.method == 'GET':
        form = LoginForm()

    response_data['form'] = form
    return render(request, 'login.html', response_data)


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
            if existing_like:
                existing_like.delete()
            else:
                post = LikeModel.objects.create(post_id=post_id, user=user)

                send_mail(
                    'Your post was liked by : ' + post.user.name ,
                    'Check your feed at SocialKids',
                    'socialkids2017@gmail.com',
                    [post.post.user.email],
                    fail_silently=False,
                )
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
            set_api_key(PKEY)
            response = sentiment(str(comment_text))
            sentiment_score = response["sentiment"]
            if sentiment_score >= 0.6:
                comment = CommentModel.objects.create(user=user, post_id=post_id, comment_text=comment_text)
                comment.save()

                send_mail(
                    'You got a comment on your post by' + comment.user.name,
                    'Check your feed at SocialKids',
                    'socialkids2017@gmail.com',
                    [comment.post.user.email],
                    fail_silently=False,
                )
                saved_message = 'Comment is successfully submitted.Check feed for more.'
                return render(request, 'feed.html', {'error_comment': saved_message})

            else:
                error_message = 'Comment cannot be submitted.Be safe.Bad content is restricted.Continue.'
                comment.delete()
                return render(request, 'feed.html', {'error_comment': error_message})

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
