## About
This Angular 8 Single Page App is the front-end for the [TC2](https://github.com/maxilie/TC2) day trading bot. 
Additionally, this repo contains Docker files enabling you to launch the web app as you would any other Docker container.


## Starting the Web App
```
sdf
```

## Development
TC2 Panel's layout guide is found on [InvisionApp](https://invis.io/F3TAMVD5S9W).
It covers the layout and positioning for every screen of the app. Howevever, the layout guide is not overly concerned with colors, fonts, and shadows.
<br><br>
The "Projects" tab on this repo contains To-Do items, areas where the code doesn't match the layout guide.
<br><br>
TODO: I have to figure out a way to run the angular server locally so I can quickly trial html and css changes.


## App Layout
TC2 Panel has two pages: 
  1) the public landing page
  2) the secure admin panel
Our [InvisionApp board](https://invis.io/F3TAMVD5S9W) will guide the design process.


## Landing Page
- Non-sticky header with a market countdown on the right
- Box in the center
- Tabs above the box (used for choosing what displays in the box):
  + Summary
  + Admin Login
  

## Admin Panel - Header
Header contains 4 tabs:
  + Runtime Control
  + Strategy Control
  + Log Control
  + System Checks

Runtime control is selected by default.
<br>
The selected tab should have no line under it so that it appears to flow into the content area.


## Admin Panel - Runtime Control
TODO


## Admin Panel - Strategy Control
TODO


## Admin Panel - Log Control
TODO


## Admin Panel - System Checks
TODO


## Communication with the Backend
The backend uses Django in Python. To send a message to the backend:
```
TODO
```

