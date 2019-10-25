Change logs
===

## 1.1.0 - 22/10/2019

By @sonofmun

- Minor changes to make Nemo compatible with MyCapytain 3.0.0
- This version is no longer compatible with earlier versions of MyCapytain. Please upgrade to MyCapytain 3.0.0.

## 1.0.4 - 22/10/2019

By @ponteineptique

- Ensure Nemo < 2.0.0 does not use MyCapytain 3.0.0

## 1.0.3 - 22/05/2018

By @sonofmun

- Refactored __transform (in flask_nemo.__init__) to _transform. This will make it available to class extensions.
- Changed a single occurrence of "import flask.ext.nemo" in the tests to "import flask_nemo"

## 1.0.2 - 26/01/2017

By @ponteineptique

- Moved to Mozilla Public License Version 2
- Fixed a bug tests would fail in mockup ( Issue #112 )
- Added a warning when base_url is not correct ( Issue #109 ) 
- Harmonized chunkers parameter names ( Issue #113 )
- Created a new tutorial on https://github.com/capitains/tutorial-nemo ( Issues #14, #78 and #97 )
- Added a CHANGES.md
