from pkg_resources import resource_filename
import json

with open(resource_filename("flask_nemo", "data/i18n/languages.json")) as f:
    ISOCODES = json.load(f)
    AVAILABLE_TRANSLATIONS = set([key for value in ISOCODES.values() for key in value.keys()])
