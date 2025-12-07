# ATOMU AIR
#### Video Demo:  <URL HERE>
#### Description:
This is an air purifier project called ATOMU AIR that i have made using raspberry pi pico as the final project of the CS50 course.
I have included all of the files within the project, even the ones that do not work and many tests i have done.
Since this was my first project using microcontrollers i do not recommend anyone use it as an actual air purifier, not to mention the filter incrementing function is imaginary, but feel free to do as you wish.
This project is entirely dependent on gc9a01py.py by russhughes for displaying stuff and it would have not been possible to display anything on the lcd without it.

## Software:
The fonts directory is responsible for loading fonts in a format that the gc9a01 is able to read.
The kicad directory is my failed attempt at making a PCB for the project but ultimatel failed to do so, so i just decided to leave it there.
The res directory is where all the images for displaying on the LCD were saved and turned into raw formats.
The test directory is where i actually spent most of my time, it has tests for all of the various components present in the project (i think i even deleted multiple of them) there are tests for all of the failed versions and succesfull ones.
The files that are not within a directory i will try to explain them one by one, fram.py is a way for the pico to write the filter percentage data on the fram, since i heard that pico is not very constant write friendly, the *bu.py files are the failed versions, the ones with multiple bugs that do not work as intended.

## Hardware:
Im using a BLDC motor as the main driving force which will push the air through the filter, there's an air quality sensor which sends PM 1.0, 2.5, and 10 via tx to the pico in this case im only using PM 2.5 since most air purifires use that as their main refrence, there's also a circular lcd im using which i talked about the driver, there is a buzzer to give it kind of an industrial feedback like feelig to the user touch, and lastly there are multiple microswitches for checking if the filter is in place or if the filter door is closed.

## Usage:
It requires 24v DC input which then uses 2 DC-DC regulators to turn that into 5v and 3.3v for the components, when the user taps the touch module the logo pops up, after another tap the it goes into mode selecting you have a small window to tap again in order to change it to the next mode, if it gets timed out then the mode that is curently being displayed gets selected, if it is one of the three manual modes then the motor will have a constant speed, and if the auto mode gets selected the motors speed will depend on the pm 2.5 value, the pm 2.5 gets updated constantly and is always shown in the display.
