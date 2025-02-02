import glob
import csv

# Change delimiter to the appropriate one in CSV
delimiter = ';'

csvs = glob.glob('*.csv')

f = open('fire_alarm.csv', 'wb')
master_csv = csv.writer(f)
# Take the header of the first CSV and make it the master header
first_csv = open(csvs[0], 'rb')
headers = first_csv.readline().strip().split(delimiter)
master_csv.writerow(headers)
# Write remaining rows
for line in first_csv:
    master_csv.writerow(line.strip().split(delimiter))

# Read remaining CSVs and skip the first row
for file in csvs[1:]:
    current_csv = open(file, 'rb')
    for line_num, line in enumerate(current_csv):
        if line_num > 0:
            master_csv.writerow(line.strip().split(delimiter))

f.close()