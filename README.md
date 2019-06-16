# CO2PeakFinder

This is a couple of small python scripts used to gather live carbon intensity information from [co2signal](https://www.co2signal.com/) and create a peak schedule for when carbon intensity is highest and lowest for a given location. I personally use this to schedule when I charge my electric car (Chevorlet Volt) by entering the CO2 intensity schedule provided by this script as a Time of Use (TOU) schedule in my car. This allows my car to prioritize charging when the carbon intensity of my local grid is lowest, but the feature is normally there to allow people to minimize their charging costs if they have Time of Use pricing for their electricity.

Example unsmoothed output from graph_data.py:

![image](https://i.imgur.com/RXaiT6O.png)

Example smoothed output and schedule from generate_peak_schedule.py:

![image](https://i.imgur.com/5kP43cm.png)

Text schedule from generate_peak_schedule.py:
```
Data from 25 weekdays and 9 weekend days.

Weekday Ranges:
00:00:00-06:30:00 Off-Peak
06:30:00-08:30:00 Mid-Peak
08:30:00-19:15:00 Peak
19:15:00-21:15:00 Mid-Peak
21:15:00-21:45:00 Peak
21:45:00-23:15:00 Mid-Peak
23:15:00-23:59:59.999999 Off-Peak

Weekend Ranges:
00:00:00-07:30:00 Off-Peak
07:30:00-09:00:00 Mid-Peak
09:00:00-19:45:00 Peak
19:45:00-22:15:00 Mid-Peak
22:15:00-23:59:59.999999 Off-Peak
```
