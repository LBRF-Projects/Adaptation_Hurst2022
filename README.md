# Motor Imagery & Fine Motor Adaptation - Hurst 2022

This repository contains the experiment code for a study looking at whether effector mapping (i.e., the mapping of specific muscle movements to specific intended outcomes) is rehearsed when performing motor imagery. This is tested using a simple-yet-challenging fine motor pointing task.

![MotorMapping](task.gif)

On each trial, a target will appear on the screen at a random distance and angle from fixation after a random delay. Once the target appears, the task of the participant is to move the cursor (translucent red circle) from the middle of the screen to be hovering over the target (small white dot) using the joystick on a gamepad. They then need to squeeze one of the gamepad's rear triggers while over the target to end the trial.

The experiment has three phases: a practice phase, a training phase, and a testing phase:

* The **practice phase** is the same for all particpants (a small number of physical practice trials to familiarize people with the task). 
* The **training phase** differs depending on the experiment condition: some people continue to practice the task physically, some are asked to practice the task using motor imagery, and others are asked to simply squeeze the trigger as soon as a target appears (control task). 
* During the **testing phase**, all participants perform the task physically using the joystick, except that the x-axis of the joystick is flipped so that "left" and "right" now move the cursor in the opposite direction as they did before.

Reaction times to targets are recorded, allowing the degree and duration of the mapping-change impairment in the final block to be measured and compared across groups.

## Requirements

This experiment is programmed in Python 3.9 using the [KLibs framework](https://github.com/a-hurst/klibs). It has been developed and tested on recent versions of macOS and Linux, but should also work without issue on Windows systems.

To use the task with a gamepad (as intended), you will also need a USB or wireless controller that is supported by your computer. The task has been tested with Microsoft Xbox 360 wired controllers as well as Sony DualShock 3 controllers connected via USB, but most gamepads that provide a joystick and rear triggers should work with the task. If no gamepad is available, mouse movement/clicking will be used in place of the joystick/triggers (respectively).


## Getting Started

### Installation

To download a copy of the task, you can grab a .zip archive of the current code [here](https://github.com/LBRF-Projects/Adaptation-Hurst2022/archive/refs/heads/main.zip). Alternatively, you can clone this repository to your computer using Git by opening a terminal in your destination folder and running the following command:

```
git clone https://github.com/LBRF-Projects/Adaptation_Hurst2022.git
```

#### Option 1: Pipenv Installation

To install the task and its dependencies in a self-contained Python environment, run the following commands in a terminal window inside the same folder as this README:

```bash
pip install pipenv
pipenv install
```
These commands should create a fresh environment the task with all its dependencies installed. Note that to run commands using this environment, you will need to prefix them with `pipenv run` (e.g. `pipenv run klibs run 15.6`).

#### Option 2: Global Installation

Alternatively, to install the dependencies for the task in your global Python environment, run the following commands in a terminal window:

```bash
pip install https://github.com/a-hurst/klibs/releases/download/0.7.6b1/klibs.tar.gz
pip install pyusb
pip install libusb_package
```

### Running the Experiment

MotorMapping is a KLibs experiment, meaning that it is run using the `klibs` command at the terminal (running the 'experiment.py' file using Python directly will not work).

To run the experiment, navigate to the MotorMapping folder in Terminal and run `klibs run [screensize]`, replacing `[screensize]` with the diagonal size of your display in inches (e.g. `klibs run 21.5` for a 21.5-inch monitor). Note that the stimulus sizes for the study assume that a) the screen size for the monitor has been specified accurately, and b) that participants are seated approximately 57 cm from the screen.

If running the task in a self-contained Pipenv environment, simply prefix all `klibs` commands with `pipenv run` (e.g. `pipenv run klibs run 21.5`).

If you just want to test the program out for yourself and skip demographics collection, you can add the `-d` flag to the end of the command to launch the experiment in development mode.

#### Optional Settings

The MotorMapping paradigm has three possible between-subjects conditions: physical practice (PP), motor imagery (MI), and a control condition (CC).

To choose which condition to run, launch the experiment with the `--condition` or `-c` flag, followed by either `PP`, `MI`, or `CC`. For example, if you wanted to run a participant in the motor imagery condition on a computer with a 15.6-inch monitor, you would run 

```
klibs run 15.6 --condition MI
```

If no condition is manually specified, the experiment program will default to physical practice.
 

### Exporting Data

To export data from the task, simply run

```
klibs export
```

while in the root of the MotorMapping directory. This will export the trial data for each participant into individual tab-separated text files in the project's `ExpAssets/Data` subfolder.

KVIQ scores and raw gamepad joystick data can likewise be exported from the data base with `klibs export -t kviq` and `klibs export -t gamepad`, respectively.
