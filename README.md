# Waveform-Watcher

A web app developed to visualize and analyze waveform data collected from XENON1T and XENONnT experiment. You can [view the website here](https://waveform-watcher.azurewebsites.net/). Access restricted to only [XENON1T](https://github.com/XENON1T) and [XENONnT](https://github.com/XENONnT) organization.

![Login-Page](https://github.com/cheryonthetop/waveform-watcher/blob/master/images/login.PNG)
![Home-Page](https://github.com/cheryonthetop/waveform-watcher/blob/master/images/Home.PNG)

---

## Main Features

- Get new waveform based on run ID and build level
- Create tag and enter comments to annotate a specific waveform
- Save a tag and comments with a waveform
- Delete a tag and therefore the comments and waveform with it
- Pan and view different parts of the visualization
- Box zoom in and out of the visualization
- Wheel zoom on x-axis
- Save the visualizations locally
- Interaction is synced between the first 2 graphs and between the last 2 graphs (e.g if you box zoom in the first graph, the second graph will do the same)

---

## Run on Local Machine

You will need key environmental variables. Ask the repo owner for them before you try running the app locally.

### **Run with Docker Containers**

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop)
1. cd into /client
1. Run `docker build -t client` .
1. cd into /server
1. Run `docker build -t server` .
1. cd into /flask
1. Run `docker build -t flask` .
1. Run the separate docker containers with

- `docker run --it -p 3000:3000 client`

- `docker run --it -p 5000:5000 server`

- `docker run --it -p 4000:4000 flask`

8. Go to http://localhost:3000 on the browser

### **Run without Docker Containers**

1. Install [node](https://nodejs.org/en/download/) and [python](https://www.python.org/downloads/). Note these come with the needed package managers `npm` and `pip`. So there is no need for separte installations.
1. cd into /client
1. Run `npm install`
1. cd into /server
1. Run `npm install`
1. Run `npm run dev`
1. cd into /flask
1. Run `pip install -r requirements.txt`

---

## The structure and workflow of the app

![Workflow-1](https://github.com/cheryonthetop/waveform-watcher/blob/master/images/workflow/workflow-1.jpg)
![Workflow-2](https://github.com/cheryonthetop/waveform-watcher/blob/master/images/workflow/workflow-2.jpg)
![Workflow-3](https://github.com/cheryonthetop/waveform-watcher/blob/master/images/workflow/workflow-3.jpg)
![Workflow-4](https://github.com/cheryonthetop/waveform-watcher/blob/master/images/workflow/workflow-4.jpg)
