from django.core.exceptions import ValidationError
from django import forms
from models import User, PostModel, LikeModel, CommentModel, UpVoteModel


class SignUpForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email', 'username', 'name', 'password']

    def clean_username(self):
        username = self.cleaned_data['username']
        if len(username) < 5:
            print 'Username short'
            raise forms.ValidationError('Username must be greater than 4 characters')
        return username

    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) <= 5:
            print 'Password short'
            raise forms.ValidationError('Password must be greater than 5 characters')
        return password

    def delete(self):
        self.party.delete()
        self.delete()

class LoginForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'password']


class PostForm(forms.ModelForm):
    class Meta:
        model = PostModel
        fields = ['image', 'caption']


class LikeForm(forms.ModelForm):
    class Meta:
        model = LikeModel
        fields = ['post']


class CommentForm(forms.ModelForm):
    class Meta:
        model = CommentModel
        fields = ['comment_text', 'post']

class UpVoteForm(forms.ModelForm):
    class Meta:
        model = UpVoteModel
        fields = ['comment']
