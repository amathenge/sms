# Uwazii Mobile - SMS API

git commit -m "first commit"
git branch -M main
git remote add origin git@github.com:amathenge/sms.git
git push -u origin main

<<<<<<< HEAD
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
=======
ssh key is type ecdsa-sha2-nistp256

So the commannds to load the keys are:
eval `ssh-agent -s`
ssh-add /path/to/id_ecdsa
>>>>>>> bf2d0c81da3ee83108fc111de368bc59f717549c
