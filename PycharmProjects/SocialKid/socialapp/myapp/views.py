

import requests
import urllib3
import httplib
import json
import os
from datetime import timedelta
import paralleldots

import textblob

import cloudinary.api
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from django.utils import timezone
from imgurpython import ImgurClient

from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm, UpVoteForm
from models import User, SessionToken, PostModel, LikeModel, CommentModel, UpVoteModel

# Importing TextBlob to delete negative comments
from textblob import TextBlob
# To check for positive and negative comments
from textblob.sentiments import NaiveBayesAnalyzer



# setup sendgrid
sendgrid_key = "17ed6b09b6b16a35f32bfcd307e1b21cb132b21e"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = 'https://eastasia.api.cognitive.microsoft.com/text/analytics/v2.0'
# Replace the accessKey string value with your valid access key.
accessKey = '4ea5fc4f73f7497bb95b12ce495512c0'

uri = 'eastasia.api.cognitive.microsoft.com'
path = '/text/analytics/v2.0/sentiment'

cloudinary.config(
    cloud_name='dbkhurkci',
    api_key='892844133313338',
    api_secret='sBwb1k59rE1gzctf5tkTp7Y6asM'
)
# Set up clarifai and define a model
from clarifai.rest import ClarifaiApp

app = ClarifaiApp(api_key='f10d3e0e9b72419a8df462deef896456')
model = app.models.get('nsfw-v1.0')

#PKEY = 'RSElfqhPZOqwmkYdqIq4SpRSMBHYDMeH7nzc0edlBz8'
PKEY = 'ICViBavMo5wuPcwTYvlkNeYUPHXciMOWbunfczI8nVU';
paralleldots.set_api_key(PKEY);


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
            # sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('sendgrid_key'))
            # from_email = Email("socialkids2017@gmail.com")
            # to_email = Email(email)
            # subject = "Susseccfully Signed Up"
            # content = Content("text/plain", "Welcome to Social Kids")
            # mail = Mail(from_email, subject, to_email, content)
            # response = sg.client.mail.send.post(request_body=mail.get())
            # print(response.status_code)

            return render(request, 'success.html')
        else:
            error = 'Error.Sign Up again!'
            return render(request, 'index.html', {'text': error})

    else:
        SignupForm = SignUpForm()
        return render(request, 'index.html', {'signup_form': SignupForm})


def login_view(request):
    dict = {}

    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = User.objects.filter(username=username).first()
            if user:
                if check_password(password, user.password):
                    # User is Valid
                    print 'Valid'
                    token = SessionToken(user=user)
                    token.create_token()
                    token.save()

                    response = redirect('/feed/')

                    response.set_cookie(key='session_token', value=token.session_token)
                    return response
                else:
                    error = "Username or password wrong!"
                    return render(request, 'login.html', {'text': error})
            else:
                error = 'Register Yourself first'
                return render(request, 'login.html', {'text': error})
        else:
            error = 'Fill the form correctly'
            return render(request, 'login.html', {'text': error})
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})


# **********************************************
# *** Update or verify the following values. ***
# **********************************************
def is_abusive(text):
    # import pdb ;
    # pdb.set_trace()
    url = 'http://apis.paralleldots.com/v3/abuse'
    api_key = paralleldots.get_api_key();
    response = requests.post("https://apis.paralleldots.com/v3/abuse", data={"api_key": api_key, "text": text}).text
    # payload = {'apikey': PKEY, 'text': text}
    text_type = json.loads(response);
    #text_type = requests.post(url, payload).json()
    if text_type['sentence_type'] == 'Abusive' :
        print text_type['confidence_score']
        print text_type['sentence_type']
        return True
    else:
        return False




def post_view(request):
    user = check_validation(request)
    if user:
        if request.method == 'POST':
            form = PostForm(request.POST, request.FILES)
            if form.is_valid():
                image = form.cleaned_data.get('image')
                print image
                caption = form.cleaned_data.get('caption')
                print caption
                post = PostModel(user=user, image=image, caption=caption)
                post.save()
                # import pdb;
                # pdb.set_trace()
                z = post.image.url
                path = BASE_DIR + '\\' + str(post.image.url)

                client = ImgurClient('dec3784447179c1', '0da91e6f758a1b4dd217320909d8d34831320b13')
                post.image_url = client.upload_from_path(path, anon=True)['link']

                app = ClarifaiApp(api_key="f10d3e0e9b72419a8df462deef896456")
                model = app.models.get('nsfw-v1.0')
                response = model.predict_by_url(url=post.image_url)
                concepts_value = response['outputs'][0]['data']['concepts']
                for i in concepts_value:
                    if i['name'] == 'nsfw':
                        nudity_level = i['value']

                        if nudity_level >= 0.85 or is_abusive(caption):
                            print("sim")
                            print response['outputs'][0]['data']['concepts']
                            print nudity_level
                            error_message = 'Post cannot be submitted'
                            post.delete()
                            return render(request, 'error.html', {'context': error_message})
                        else:
                            post.save()
                            saved_message = 'Post is successfully submitted'
                            return render(request, 'error.html', {'context': saved_message})
                            return redirect('/feed/')
        else:
            form = PostForm()

        return render(request, "post.html", {'form': form})
    else:
        return redirect('login')


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


def profile_view(request, username):
    user = check_validation(request)
    if user:
        user_profile = User.objects.all().filter(username=username)
        print user_profile
        posts = PostModel.objects.all().filter(user=user_profile).order_by('-created_on')

        for post in posts:
            existing_like = LikeModel.objects.filter(post_id=post.id, user=user).first()
            comments = CommentModel.objects.filter(post_id=post.id)
            for comment in comments:
                existing_up_vote = UpVoteModel.objects.filter(comment=comment.id).first()
                if existing_up_vote:
                    comment.has_up_voted = True

            # If user has liked the post
            if existing_like:
                post.has_liked = True

        return render(request, 'feed.html', {'posts': posts})
    else:
        return redirect('/login/')
    return render(request, 'feed.html', {'print': username})


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
                # sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('sendgrid_key'))
                #######print(response.status_code)

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
            text = form.cleaned_data.get('comment_text')
            blob = TextBlob(text, analyzer=NaiveBayesAnalyzer())
            print blob.sentiment.p_neg
            print blob.sentiment.p_pos
            if blob.sentiment.p_neg > blob.sentiment.p_pos:
                error_message = 'Comment cannot be submitted.Be safe.Bad content is restricted.Continue.'
                comment.delete()
                return render(request, 'feed_message.html', {'error_comment': error_message})
            else:
                comment.save()
                post = LikeModel.objects.create(post_id=post_id, user=user)
                # sg = sendgrid.SendGridAPIClient(apikey=os.environ.get('sendgrid_key'))
                # from_email = Email("socialkids2017@gmail.com")
                # to_email = Email(post.user.email)
                # subject = "Got a Comment"
                # content = Content("text/plain", "You got a  on your post")
                # mail = Mail(from_email, subject, to_email, content)
                # response = sg.client.mail.send.post(request_body=mail.get())
                # print(response.status_code)

                saved_message = 'Comment is successfully submitted.Check feed for more.'
                return render(request, 'feed_message.html', {'error_comment': saved_message})

            return redirect('/feed/')

        else:
            return redirect('/feed/')
    else:
        return redirect('/login')


def up_vote_view(request):
    user = check_validation(request)
    if user and request.method == 'POST':
        form = UpVoteForm(request.POST)
        if form.is_valid():
            comment_id = form.cleaned_data.get('comment').id
            existing_up_vote = UpVoteModel.objects.filter(comment_id=comment_id, user=user).first()

            if existing_up_vote:
                existing_up_vote.delete()
            else:
                UpVoteModel.objects.create(comment_id=comment_id, user=user)

        return redirect('/feed/')
    else:
        return redirect('/login/')


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
