# Homo Arachnid

Project repository for the Secure Web Development block course, Sose 2020.  
I have tested this using Google Chrome and Safari as the browser, running on Python 3.8.5 and Django 3.1.  

N.B. - Post P2, I have developed the code to work on http://localhost instead of http://127.0.0.1. This also applies to task 5.2 where the sample code explicitly had http://127.0.0.1 but I ended up hardcoding http://localhost, also in postmessage segment.

To run the project on another "port-number" than default 8000, start the django server as -  

python3 manage.py runserver "port-number"  
e.g  
- python3 manage.py runserver 3000  
or  
- python3 manage.py runserver 2000  

Project P1 is done.  
Project P2 is done.  
Project P3 is done.  
Project P4 - when an unlogged user tries to add an item to cart/basket, they are redirected to the login page.
            Post login, the page doesn't redirect to the shopping page (couldn't figure this out.)
            The user sees a link to go to the shopping list page.  
Project P4 -  Apart from the above mentioned case, is done.  
Project P4 - The above part is acceptable behaviour according to the tutor. Leaving it at that. Some vulnerabilities exposed. Will come back to patch them up.  
Project P4 - The vulnerabilities are plugged (most of them). Moved tracker to env for P5.  
Project P5 is done.