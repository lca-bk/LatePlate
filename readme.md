
# Late Plate App

Our house has a meal plan that includes lunch and dinner throughout the week.
Often, some of our members can't make it during the scheduled meal time, so they sign up to have their food boxed up and saved for later.
This app makes it incredibly easy to sign up for and cancel these Late Plates and presents a page for the chef to see the updated list.


## Setup

This is a python webapp2 app that runs on  [Google App Engine](https://developers.google.com/appengine/).

1. Create an account for Google App Engine
1. Clone this GitHub repository: `git clone git://github.com/GTKappaSig/LatePlate'`
1. Configure for your organization.  TODO: explain what needs to be changed
1. Add google app engine as a git remote: `git remote add appengine https://code.google.com/id/###########`.  The url for this can be found in the admin console when you login to app engine.
1. Push to app engine to deploy the application.  `git push appengine master`


## Weekly Menu

One of the tabs on the webapp displays a pdf of the weekly menu.
This must be manually uploaded each week to stay up to date.
A script is included to make the upload easier.
Keep in mind that you'll have to change the upload url in the script and in menu.html depending on where you want the menu to go.

```
./upload_menu.sh menu-week1.pdf
######################################################################## 100.0%
```


## Support

If you notice an issue, feel free to open a new ticket on our [GitHub Issues page](https://github.com/GTKappaSig/LatePlate/issues).
