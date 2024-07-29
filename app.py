from flask import Flask, request, render_template, redirect, url_for, flash
from PIL import Image, ImageFilter
from pprint import PrettyPrinter
from dotenv import load_dotenv
import json
import os
import random
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__,
            static_url_path='', 
            static_folder='static',
            template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

@app.route('/')
def homepage():
    """A homepage with handy links for your convenience."""
    return render_template('home.html')

################################################################################
# COMPLIMENTS ROUTES
################################################################################
list_of_compliments = [
    'awesome',
    'beatific',
    'blithesome',
    'conscientious',
    'coruscant',
    'erudite',
    'exquisite',
    'fabulous',
    'fantastic',
    'gorgeous',
    'indubitable',
    'ineffable',
    'magnificent',
    'outstanding',
    'propitioius',
    'remarkable',
    'spectacular',
    'splendiferous',
    'stupendous',
    'super',
    'upbeat',
    'wondrous',
    'zoetic'
]

@app.route('/compliments')
def compliments():
    """Shows the user a form to get compliments."""
    return render_template('compliments_form.html')

@app.route('/compliments_results')
def compliments_results():
    """Show the user some compliments."""
    try:
        users_name = request.args.get('users_name')
        if not users_name:
            raise ValueError("Name is required")
        
        wants_compliments = request.args.get('wants_compliments') == 'on'
        
        num_compliments_str = request.args.get('num_compliments', '1')
        if num_compliments_str.isdigit():
            num_compliments = int(num_compliments_str)
        else:
            raise ValueError("Number of compliments must be a number")
        
        if num_compliments > len(list_of_compliments):
            raise ValueError("Number of compliments requested exceeds available compliments. ")

        compliments_list = random.sample(list_of_compliments, num_compliments) if wants_compliments else []
    
        context = {
            'users_name': users_name,
            'wants_compliments': wants_compliments,
            'num_compliments': num_compliments,
            'compliments_list': compliments_list
        }

        return render_template('compliments_results.html', **context)
    except ValueError as e:
        flash(str(e))
        return redirect(url_for('compliments'))

################################################################################
# ANIMAL FACTS ROUTE
################################################################################
animal_to_fact = {
    'koala': 'Koala fingerprints are so close to humans\' that they could taint crime scenes.',
    'parrot': 'Parrots will selflessly help each other out.',
    'mantis shrimp': 'The mantis shrimp has the world\'s fastest punch.',
    'lion': 'Female lions do 90 percent of the hunting.',
    'narwhal': 'Narwhal tusks are really an "inside out" tooth.'
}

@app.route('/animal_facts', methods=['GET', 'POST'])
def animal_facts():
    """Show a form to choose an animal and receive facts."""
    # Get form data
    chosen_animal = request.args.get('animal')

    # Get the list of all animals
    all_animals = list(animal_to_fact.keys())

    # Get the chosen animal fact
    chosen_animal_fact = animal_to_fact.get(chosen_animal)
    

    context = {
        'all_animals': all_animals,
        'chosen_animal_fact': chosen_animal_fact
    }
    return render_template('animal_facts.html', **context)


################################################################################
# IMAGE FILTER ROUTE
################################################################################

filter_types_dict = {
    'blur': ImageFilter.BLUR,
    'contour': ImageFilter.CONTOUR,
    'detail': ImageFilter.DETAIL,
    'edge enhance': ImageFilter.EDGE_ENHANCE,
    'emboss': ImageFilter.EMBOSS,
    'sharpen': ImageFilter.SHARPEN,
    'smooth': ImageFilter.SMOOTH
}

def save_image(image, filter_type):
    """Save the image, then return the full file path of the saved image."""
    # Append the filter type at the beginning (in case the user wants to 
    # apply multiple filters to 1 image, there won't be a name conflict)
    new_file_name = f"{filter_type}-{image.filename}"
    image.filename = new_file_name

    # Construct full file path
    file_path = os.path.join(app.root_path, 'static/images', new_file_name)
    
    # Save the image
    image.save(file_path)

    return file_path

def apply_filter(file_path, filter_name):
    """Apply a Pillow filter to a saved image."""
    i = Image.open(file_path)
    i.thumbnail((500, 500))
    i = i.filter(filter_types_dict.get(filter_name))
    i.save(file_path)

@app.route('/image_filter', methods=['GET', 'POST'])
def image_filter():
    """Filter an image uploaded by the user, using the Pillow library."""
    filter_types = filter_types_dict.keys()

    if request.method == 'POST':
        
        filter_type = request.form.get('filter_type')
        
        # Get the image file submitted by the user
        image = request.files.get('users_image')
        
        # call `save_image()` on the image & the user's chosen filter type, save the returned
        # value as the new file path
        file_path = save_image(image, filter_type)
        apply_filter(file_path, filter_type)

        # call `apply_filter()` on the file path & filter type

        image_url = f'./static/images/{image.filename}'

        context = {
            'filter_type': filter_types,
            'image_url': image_url
        }

        return render_template('image_filter.html', **context)

    else: # if it's a GET request
        context = {
            'filter_types': filter_types
        }
        return render_template('image_filter.html', **context)


################################################################################
# GIF SEARCH ROUTE
################################################################################

"""You'll be using the Tenor API for this next section. 
Be sure to take a look at their API. 

https://tenor.com/gifapi/documentation

Register and make an API key for yourself. 
Set up dotenv, create a .env file and define a variable 
API_KEY with a value that is the api key for your account. """

API_KEY = os.getenv('API_KEY')
lmt = 8
ckey = "my_test_app" # set the client_key for the integration and use the same value for API calls.

# Tenor API base URL
TENOR_URL = f"https://tenor.googleapis.com/v2/search" 

# PrettyPrinter for debugging
pp = PrettyPrinter(indent=4)

@app.route('/gif_search', methods=['GET', 'POST'])
def gif_search():
    """Show a form to search for GIFs and show resulting GIFs from Tenor API."""
    if request.method == 'POST':
        # Get the search query & number of GIFs requested by the user, store each as a 
        # variable
        search_query = request.form.get('search_query')
        quantity = request.form.get('quantity')

        # Make a request to the Tenor API
        response = requests.get(
            TENOR_URL,
            params={
                'q': search_query,
                'key': API_KEY,
                'limit': quantity
            })
        # Check if API was successful
        if response.status_code == 200:
            gifs = json.loads(response.content).get('results')

        else:
            gifs = []

        context = {
            'gifs': gifs
        }

         # Uncomment me to see the result JSON!
        # Look closely at the response! It's a list
        # list of data. The media property contains a 
        # list of media objects. Get the gif and use it's 
        # url in your template to display the gif. 
        pp.pprint(gifs)

        return render_template('gif_search.html', **context)
    else:
        return render_template('gif_search.html')

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)

