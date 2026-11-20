## Usage

### First time running



```
$ sudo apt-get install ros-$ROS_DISTRO-rqt
$ sudo apt-get install ros-$ROS_DISTRO-rqt-common-plugins
```



OR



```
$ rosdep install rqt_plot
```

 Also if you're on Ubuntu and like to know the
most recommended plotting result, simply get a `.deb` file of
`pyqtgraph` [here](http://www.pyqtgraph.org/), which is not available
via `rosdep`. And run it by something like:



```
$ dpkg -i %NAME_OF_DOT_DEB_FILE%.deb
```



### How to run in general



```
$ rqt_plot
```

 To specify topic(s) to plot, you need full path
name of the topics published. You can find them easily for instance by
the command below:



```
$ rostopic list
/rosout         #  these are only example topics.
/rosout_agg
/turtle1/cmd_vel
/turtle1/color_sensor
/turtle1/pose
```



### To give topic names to plot

There are two ways to give the topic names to `rqt_plot` as explained
in following sections. In both ways, topics that are set in previous run
is resumed (as far as the program was shut down without error).

#### Run from commandline

Both of the following lines plot the same topics.



```
$ rqt_plot /turtle1/pose/x:y:z
$ rqt_plot /turtle1/pose/x /turtle1/pose/y /turtle1/pose/z
```

 Obviously, if you want to change the topics to
plot, you need to restart the program and give the new topic names.

#### From GUI

Type in the "Topic" input field the full path of the topic name, and
press "+" button. ![width="100%"](doc/rqt_plot.png)

"Topic" field auto-completes the topic name (although it's not fully
working as noticed).

#### Note for the input value syntax

The input value should be the full path to the value, not only the topic
name. E.g., in above case the topic `/turtle1/pose/x` is a member
"x" in a published topic "/turtle1/pose", which is defined as
["turtlesim/Pose" message](http://docs.ros.org/kinetic/api/turtlesim/html/msg/Pose.html).

New short example to show this; say you want to plot a topic called
position `x` of `/your_robot/pose` topic, which is a type of
[geometry_msgs/Pose](http://docs.ros.org/api/geometry_msgs/html/msg/Pose.html)
message. This can be plotted by `/your_robot/pose/position/x`.
Possiblly you can figure out this plot name by following steps like
this:

- [geometry_msgs/Pose](http://docs.ros.org/api/geometry_msgs/html/msg/Pose.html)
  contains a member `position`. Look into its definition by clicking
  the link at `geometry_msgs/Point` in the api page.
- You see `x` as a member of `geometry_msgs/Point`.

### To choose plotting backend type

Currently `rqt_plot` has three plotting backend options (**numbered in
recommended order**) which can be configured using the setting dialog
available via the gear icon in the window title bar:

1\. [pyqtgraph](http://www.pyqtgraph.org/) (fast and needs `pyqtgraph`
to be manually installed which is not in the `Ubuntu` binary
repository as of Sep 2013) 1. [matplotlib](http://matplotlib.org/) (slow
but always available) 1. `qwt plot` (fast, but not using message
timestamps and needs python-qwt bindings)

By default, backend option is chosen in the order above; the first one
found on your system gets used (eg. if your system has `matplotlib`
but not `pyqtgraph`, your `rqt_plot` runs with the `matplotlib`).

User can also select one of them from GUI; click "gear" icon next to
question symbol and a dialog should pop up.

### Zoom out on time axis

See
[this post](http://answers.ros.org/question/187036/zoom-out-in-rqtplot/).

## Trouble shooting

### Topic is not plotted

Check the following:

- Your topic is an array (eg.
  [sensor_msgs/JointState/position](http://www.ros.org/doc/api/sensor_msgs/html/msg/JointState.html))
- specify an array index
  ([see this thread](http://answers.ros.org/question/60194/oddity-in-rxplot/?answer=60203#post-id-60203))
- You didn't give the full path of your topic
- Topic is not being published
- Use [rqt_topic](https://index.ros.org/p/rqt_topic) to see the
  `topic`s being published.
- You are plotting data from a bag file?
- [Use simulation time.](http://wiki.ros.org/Clock#Using_Simulation_Time_from_the_.2BAC8-clock_Topic)

## Limitation

### Data type

TODO need to figure out which data types are supported

### No trajectory supported

[See this discussion](http://answers.ros.org/question/58907/has-anyone-written-a-trajectory-plotting-tool/?comment=70249#comment-70249).

[Spline](http://www.youtube.com/watch?v=9ZnVGvxzjG4) curve is not
supported either.
