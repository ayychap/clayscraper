# clayscraper

I wanted a list of clay bodies that can be sorted/filtered by various characteristics. Laguna makes *a lot* of different clays, so I slapped together some functions to scrape the data into a spreadsheet.

Also included are clays from Rocky Mountain, and hopefully some additional companies as I get to them.

Want the cleaned up spreadsheet of clays? [Here it is.](https://docs.google.com/spreadsheets/d/1-OB2215MkYa8ahn4SySlFGC3SruQsl-Ac-zunVDWkUo/edit?usp=sharing)

## Issues: 

The description text is very inconsistent from clay to clay. Even though most of the output is cleaned up, there's still a lot of final tidying required in the resulting spreadsheet.

1. Average shrinkage/water absorption can vary for different cones. Rocky Mountain handles this by using a Cone #: Avg. ... format.
2. Firing color is inconsistently described *within each manufacturer.* Some of these get merged, some of them don't.
3. There are some garbage columns that show up, e.g. unnamed columns. Laguna Flameware has a whole bunch of extra text after the characteristics that generates weird columns.

## Future Improvements: 

Get more clay!

1. [Aardvark](https://www.aardvarkclay.com/pdf/technical/shrinkage_rates.pdf) *this one is a pdf chart*
2. [Kentucky Mudworks](https://kymudworks.com/collections/ky-mudworks-clay)
3. [New Mexico](https://nmclay.com/pugged-clay-bodies)
4. ???
