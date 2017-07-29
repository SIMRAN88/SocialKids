# SocialKids
A social network that is safe for kids. It makes sure that images and text is appropriate for kids under the age of 12.


````````````````````````
Name:SocialKids
Version:1.0
Description:A social network that is safe for kids. It makes sure that images and text is appropriate for kids under the age of 12.
Author Name:Simran Raj
Author Url:http://www.simranraj.com
``````````````````````````

 
 # Objectives:
* The home page should have a form for signup and a button for login.
* Clicking on the login button should redirect the user to the /login page.
* On click the submit button the form should make a POST request.
* If the user is created the app should show a confirmation message to the user
that the account has been created and redirect the user to the login page..
* Send a welcome email to the user for successfully completing the sign up.
* The view method should send the user to the /feeds/ page after log in.
* Create a post.
* The webpage should contain a button to upload an image and a text box to add a caption to the same.
* If the post was successfully created show a success message to the user else an error message.
* View Posts.
* The page should show a list of all photos posted by every user in a chronological order, with the latest image on top.
* Each post should carry the name of the person who posted it, the timestamp, the image that was posted and caption it was posted with.
* The web page should have a button or link called Create a new Post which links to the /post url and a logout button.
* Like a post
* For each post add a button to like the post.
* If the user has already liked a post the button/icon should indicate the same through either text or color indicators.
* If a user clicks the like button on an already liked post it should unlike the post in the database.
* Send an email to the user who created the post informing them that their post has been liked.
* Comment on Photos
* Add a comment box and 'Comment' button for each post.
* Show the list of comments for each post along with other details. The list of comments should include the user name,
timestamp and comment text of the comment.
* Send an email to the user who create the post informing them of a new comment on the post they created.
* Implement upvoting on a comment.
* Make the url accept query parameters to optionally show posts only from a particular user.
* Log Out.(button on feeds and post page)



````````````````````````````````````````````
### Python setup

To properly use this python-modules some additional libraries have to be
installed beforehand. This can be easily accomplished with the commands below.
``````````````````````````````````````````````````

```bash
pip install virtual_env
source bin/activate
pip install Django
pip install sendgrid
pip install imgurpythn
pip install clarifai
pip install ParallelDots
pip install DateTime
```

### Run 
pyhton manage.py runserver

Preview
localhost:8000 - Home Page
![alt tag](https://i.imgflip.com/1t9iru.gif)

localhost:8000 - Signup
![alt tag](http://i.imgur.com/3U3j10q.jpg)

localhost:8000/login/ - Login
![alt tag](http://i.imgur.com/WYljeCk.jpg)

localhost:8000/post/ - Post
![alt tag](http://i.imgur.com/cc1Vd9Q.jpg)

localhost:8000/post/ - PostSuccessful(Analysis proper content[image and caption] for children)
![alt tag](http://i.imgur.com/1vfEdoa.jpg)

localhost:8000/feed/ - Feed
![alt tag](http://i.imgur.com/u3Jc4r2.jpg)

localhost:8000/feed/ - Comment(Analysis for the comment)
![alt tag](http://i.imgur.com/cda7dEQ.jpg)


