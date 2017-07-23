from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from forms import SignUpForm, LoginForm, PostForm, LikeForm, CommentForm
from models import User, SessionToken, PostModel, LikeModel, CommentModel
from datetime import timedelta
from django.utils import timezone
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from imgurpython import ImgurClient

# for sending mail to user
import sendgrid
sendgrid_key = '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'
my_client = sendgrid.SendGridAPIClient(apikey=sendgrid_key)

def create_payload(subject,message,email):
    from_email = "socialkids2017@gmail.com"
    from_name = "Social Kids"

    data = {
            "personalizations":[{
                "to":[{"email":email }],
                "subject": subject
            }],
            "from": {
                "email": from_email,
                "name": from_name
            },
            "content": [{
                "type":"text/html",
                "value": message
            }]
        }
    return data

# Create your views here.
def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user_len = len(username)
            password_len = len(password)
            if user_len > 4 and password_len > 5:
                print "User name should be at least three characters long and password length more than 5"
            # saving data to DB
            else:
                user = User(name=name, password=make_password(password), email=email, username=username)
                user.save()

                subject = "Successfully Signed Up"
                message = "Welcome to Social Kids"
                payload = create_payload(subject, message, email)
                response = my_client.client.mail.send.post(request_body=payload)
                print response

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
    return render(request, 'login.html', dict)


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
                post.save()
                return redirect('/feed/')
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
            post = form.cleaned_data.get('post')
            post_id = form.cleaned_data.get('post').id
            existing_like = LikeModel.objects.filter(post_id=post_id, user=user).first()
            if not existing_like:
                LikeModel.objects.create(post_id=post_id, user=user)
                LikeModel.objects.create(post_id=post_id, user=user)
                print "Post is liked"
                sg = sendgrid.SendGridAPIClient(apikey=API_KEY)
                from_email = email("socialkids2017.com")
                to_email = email(post.user.email)
                subject = "InstaClone"
                content = Content("text/plain", "Your post is liked")
                mail = Mail(from_email, subject, to_email, content)
                response = sg.client.mail.send.post(request_body=mail.get())
                print response
                print post.user.email
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
