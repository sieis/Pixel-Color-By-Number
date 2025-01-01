# Pixel-Color-By-Number
Generate pixel art color by number from an image.

## For My Sons

They're obsessed with these and the internet doesn't have enough cool ones.

This let's them find any pic. Like this one:

![pic of landscape](pics/landscape2.jpg)

Turn it into pixel art. Like this:

![landscape pixel art](pixel_art/landscape2_pixel_art.png)

And then print out a PDF of a color by number grid. Like this:

![landscape pixel grid](pixel_art/landscape_grid.png)

___

It's not perfect.

Yet.

But it's a real fun start!

___

## How to Use

* Get pics and put them in the `pics` folder.
* Open terminal and run the Python script. All you have to declare is the output size in pixels. 
* The bigger the number, the more detailed the pixel grid. We found that between 30x30 and 50x50 work best. We've only tested square outputs so far.
* This will create a 30x30 grid output in a printable PDF in the `templates` folder.

```bash
python3 pixel_color_by_number 30 30
```

* you'll also get the pixel art image in the `pixel_art` folder.
* (both of those folders will automatically be generated. All you need to start is at least one image in a pics folder).
* This will loop through all the images in the folder, so you can add a bunch of them.

* If you re-run the code with a different dimensions, it'll replace both the templates and pixel_art outputs with the new results.