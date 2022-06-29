# Uwazii Mobile - SMS API

git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:amathenge/sms.git
git push -u origin main

For Flask_Recaptcha there is a problem with Markup()

Need to modify the file:

.venv/lib/python3.8/site-packages/flask_recaptcha.py

where .venv is the virtual environment directory.

Look for the line:

    from jinja2 import Markup

comment it.
Add:

    from markupsafe import Markup

Your code should look like:

    # from jinja2 import Markup
    from markupsafe import Markup
